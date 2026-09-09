"""Local-git commit backfill — completeness independent of the Events API (GH-169).

GH-155/#157 made direct branch commits collectable, but only ones the GitHub
Events API still remembers: at most 300 events, roughly 90 days, scoped to a
single actor's feed. A measured 182 of 938 commits on ``development`` were
absent from the signal, including ``cfeafe4`` — the commit that brought CLIO
into this repo, and the one document that answered "where did CLIO come from?"

This module closes that by enumerating history from the local clone rather than
the API. Every missing SHA is already on disk, so the walk costs zero API calls
and is not rate-limited — which is precisely what makes full-history coverage
affordable, instead of the 90-day compromise the API forces.

Two invariants this module exists to hold:

- **Coverage is fetched, not assumed.** A stale clone under-reports, so a repo
  is fetched before enumeration; otherwise the backfill would confidently close
  a gap it never measured.
- **An uncoverable repo is reported, not skipped.** A logged skip is still
  silence, and silence is the failure shape of this entire issue.
"""

from __future__ import annotations

import json
import sqlite3
import subprocess
from functools import lru_cache
from dataclasses import asdict, dataclass, field
from pathlib import Path

from rebalance.ingest.db import db_connection, ensure_github_schema
from rebalance.ingest.db import github as gh
from rebalance.ingest.local_repos import scan_local_repos
from rebalance.lib.git_ops import compute_origin_ref_digest, peek_remote_refs, run_git
from rebalance.lib.time_ops import _now, now_utc

# One ASCII unit separator between fields and a record separator between commits:
# commit messages are multi-line and contain almost any printable character, so
# splitting on newlines or a pipe would corrupt exactly the bodies we care about
# (cfeafe4's message spans 6 lines and carries a URL, an @-SHA, and slashes).
_FIELD_SEP = "\x1f"
_RECORD_SEP = "\x1e"
_LOG_FORMAT = _FIELD_SEP.join(["%H", "%an", "%ae", "%aI", "%B"]) + _RECORD_SEP

MAX_COMMITS_PER_BACKFILL = 5000
_GIT_TIMEOUT_S = 120

# This DB is written by long-lived processes (pulse-server, MCP servers), so a
# backfill must not hold one write transaction across a whole repo walk. Found
# live: the first full run died on "database is locked" against 60 repos.
# Commit in batches and wait rather than failing instantly.
_COMMIT_BATCH = 100
_BUSY_TIMEOUT_MS = 30_000


@dataclass
class BackfillResult:
    repo: str = ""
    state: str = "ok"  # ok | uncoverable
    reason: str = ""
    local_path: str = ""
    default_branch: str = ""
    commits_seen: int = 0
    commits_inserted: int = 0
    commits_updated: int = 0
    commits_skipped_existing: int = 0
    merge_commits: int = 0
    files_written: int = 0
    fetched: bool = False
    api_calls_used: int = 0  # structurally always 0; asserted in tests
    capped: bool = False
    skipped_cache: bool = False  # True when remote peek matched cached checkpoint (GH-201)
    warnings: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return asdict(self)


def is_commit_walk_cached(
    conn: sqlite3.Connection,
    canonical_remote_url: str,
    current_remote_ref_map: dict[str, str],
    requested_since_utc: str | None,
) -> bool:
    """Evaluate cache-hit equality across ALL origin branches and history window (GH-201).

    Requires:
    1. Table entry exists for canonical_remote_url.
    2. ref_digest matches current digest across all origin branches (refs/heads/*).
    3. Complete origin branch ref-name -> SHA mapping matches exactly.
    4. Requested history window ('since') is within covered_since_utc.
    Missing or unverified remote proof always returns False.
    """
    if not current_remote_ref_map:
        return False

    cur = conn.cursor()
    row = cur.execute(
        "SELECT ref_digest, sha_map_json, covered_since_utc FROM github_remote_peeks WHERE canonical_remote_url = ?",
        (canonical_remote_url,),
    ).fetchone()
    if not row:
        return False

    cached_digest, cached_json, covered_since = row
    current_digest = compute_origin_ref_digest(current_remote_ref_map)
    if cached_digest != current_digest:
        return False

    try:
        cached_map = json.loads(cached_json)
        current_branches = {k: v for k, v in current_remote_ref_map.items() if k.startswith("refs/heads/")}
        if cached_map != current_branches:
            return False
    except Exception:
        return False

    if requested_since_utc is not None:
        if covered_since is not None and requested_since_utc < covered_since:
            return False

    return True


def record_commit_coverage_checkpoint(
    conn: sqlite3.Connection,
    canonical_remote_url: str,
    remote_ref_map: dict[str, str],
    covered_since_utc: str | None,
    verified_at_utc: str,
    snapshot_time_utc: str,
) -> bool:
    """Publish an atomic commit coverage checkpoint with overlap protection (GH-201 / SCHEDULER.md:72).

    Update is conditional on recorded verified_at <= snapshot_time_utc to prevent
    stale overlapping runs from overwriting newer proofs.
    """
    origin_branches = {k: v for k, v in remote_ref_map.items() if k.startswith("refs/heads/")}
    ref_digest = compute_origin_ref_digest(remote_ref_map)
    sha_map_json = json.dumps(origin_branches, sort_keys=True)

    cur = conn.cursor()
    existing = cur.execute(
        "SELECT verified_at FROM github_remote_peeks WHERE canonical_remote_url = ?",
        (canonical_remote_url,),
    ).fetchone()

    if existing is None:
        cur.execute(
            """
            INSERT INTO github_remote_peeks
                (canonical_remote_url, ref_digest, sha_map_json, covered_since_utc, verified_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (canonical_remote_url, ref_digest, sha_map_json, covered_since_utc, verified_at_utc),
        )
        return True

    existing_verified_at = existing[0]
    if existing_verified_at > snapshot_time_utc:
        return False

    cur.execute(
        """
        UPDATE github_remote_peeks
        SET ref_digest = ?, sha_map_json = ?, covered_since_utc = ?, verified_at = ?
        WHERE canonical_remote_url = ? AND (verified_at <= ? OR verified_at IS NULL)
        """,
        (ref_digest, sha_map_json, covered_since_utc, verified_at_utc, canonical_remote_url, snapshot_time_utc),
    )
    return cur.rowcount > 0


def _git(repo_path: Path, *args: str) -> tuple[int, str, str]:
    """Run git in *repo_path*, returning (returncode, stdout, stderr).

    Unlike ``local_repos._git`` this surfaces the failure detail rather than
    collapsing it to None — a backfill that cannot fetch must say why, since
    the whole point is that silence is not an acceptable outcome.
    """
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_path), *args],
            capture_output=True,
            text=True,
            timeout=_GIT_TIMEOUT_S,
        )
    except subprocess.TimeoutExpired:
        return 124, "", f"git {' '.join(args)} timed out after {_GIT_TIMEOUT_S}s"
    except OSError as exc:  # git missing, path vanished
        return 127, "", str(exc)
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def default_roots() -> list[str]:
    """Where to look for clones when ``local_repo_roots`` is unset.

    Discovered the hard way: the first live run marked all 60 watched repos
    ``uncoverable`` because ``local_repo_roots`` defaults to empty, so the whole
    backfill was a no-op. Reusing that config key is still right — one canonical
    place per fact — but a feature that requires manual configuration before it
    does anything will simply never run.

    The fallback is the parent of this installation's own repository PLUS the
    machine's configured repo scan roots (the same roots the Focus 5 / repo
    discovery collectors walk): sibling clones under a shared dev directory are
    the overwhelmingly common layout, but a split install — scheduler pinned to
    a runtime checkout, development in another tree — makes the parent of THIS
    checkout the wrong answer alone. Found live (#147): the runtime checkout's
    parent did not contain the operator's clone directory, every clone under it
    was beyond the depth-bounded walk, and each hourly sync stamped the repos
    ``uncoverable`` — silencing the zero-API commit backstop exactly when the
    rate-limited API path needed it most. Explicit config always wins.
    """
    from rebalance.ingest.config import get_focus5_scan_roots, get_local_repo_roots, get_repo_scan_roots

    configured = get_local_repo_roots()
    if configured:
        return configured

    roots: list[str] = []

    def _add(root: str | None) -> None:
        if root and root not in roots:
            roots.append(root)

    # Resolve via git rather than walking for a `.git` entry. In a worktree
    # `.git` is a FILE pointing elsewhere, so a naive walk stops at the worktree
    # and returns `.claude/worktrees` as the dev root — which finds nothing.
    # `--git-common-dir` always resolves to the MAIN checkout's .git, whether we
    # are running from the main tree or any worktree of it.
    here = Path(__file__).resolve().parent
    code, out, _ = _git(here, "rev-parse", "--path-format=absolute", "--git-common-dir")
    if code == 0 and out:
        _add(str(Path(out).parent.parent))

    # The machine's own answer to "where do repos live" — already configured for
    # the other repo-discovery collectors, so this is one fact, not a second
    # knob. get_focus5_scan_roots() falls back to get_repo_scan_roots() itself;
    # reading both honours a focus5-only override on machines that never set the
    # shared key.
    for root in (*get_repo_scan_roots(), *get_focus5_scan_roots()):
        _add(str(Path(root).expanduser()))

    return roots


@lru_cache(maxsize=8)
def _clone_index(roots_key: tuple[str, ...]) -> dict[str, Path]:
    """``owner/repo`` (lowercased) -> local path, scanned ONCE per root set.

    Cached because the naive form re-walked the whole dev directory for every
    repo: with 60 watched repos that is 60 full filesystem scans, which pushed
    a single `rebalance doctor` run past two minutes. The scan result is stable
    within a process, so once is enough.
    """
    index: dict[str, Path] = {}
    for repo in scan_local_repos(list(roots_key)):
        if repo.full_name:
            index.setdefault(repo.full_name.lower(), repo.path)
    return index


def resolve_clone(repo_full_name: str, *, roots: list[str] | None = None) -> Path | None:
    """Local checkout for ``owner/repo``, or None when this machine has none.

    Reuses the existing ``local_repo_roots`` scan rather than introducing a
    second notion of "where repos live" — one canonical place per fact.
    """
    if roots is None:
        roots = default_roots()
    if not roots:
        return None
    return _clone_index(tuple(roots)).get(repo_full_name.strip().lower())


def _default_branch(repo_path: Path) -> str:
    """The clone's default branch, preferring origin's HEAD over local HEAD.

    Local HEAD is whatever branch happens to be checked out — in a worktree
    that is routinely a feature branch, which would silently narrow the walk.
    """
    code, out, _ = _git(repo_path, "symbolic-ref", "--quiet", "refs/remotes/origin/HEAD")
    if code == 0 and out:
        return out.rsplit("/", 1)[-1]
    for candidate in ("development", "main", "master"):
        code, _, _ = _git(repo_path, "rev-parse", "--verify", f"origin/{candidate}")
        if code == 0:
            return candidate
    code, out, _ = _git(repo_path, "rev-parse", "--abbrev-ref", "HEAD")
    return out if code == 0 and out else "HEAD"


def _parse_log(raw: str) -> list[dict]:
    commits: list[dict] = []
    for record in raw.split(_RECORD_SEP):
        record = record.strip("\n")
        if not record.strip():
            continue
        parts = record.split(_FIELD_SEP)
        if len(parts) < 5:
            continue
        sha, author_name, author_email, authored_at, message = parts[:5]
        commits.append(
            {
                "sha": sha.strip(),
                "author_name": author_name.strip(),
                "author_email": author_email.strip(),
                "committed_at": authored_at.strip(),
                "message": message.strip(),
            }
        )
    return commits


def _changed_paths(repo_path: Path, sha: str) -> list[str] | None:
    """Changed paths for one commit.

    ``-m --first-parent`` makes merge commits report the files the merge
    actually brought in; without it git prints nothing for a merge, which is
    how merge commits ended up invisible in the first place.
    Returns None if git show failed, allowing caller to mark the row retryable (GH-201).
    """
    code, out, _ = _git(repo_path, "show", "--pretty=format:", "--name-only", "-m", "--first-parent", sha)
    if code != 0:
        return None
    seen: list[str] = []
    for line in out.splitlines():
        path = line.strip()
        if path and path not in seen:
            seen.append(path)
    return seen


def _is_merge(repo_path: Path, sha: str) -> bool:
    code, out, _ = _git(repo_path, "rev-list", "--parents", "-n", "1", sha)
    return code == 0 and len(out.split()) > 2


def _record_coverage(conn, repo: str, result: BackfillResult, now: str) -> None:
    conn.execute(
        """
        INSERT INTO github_repo_coverage
            (repo_full_name, state, reason, local_path, default_branch, checked_at)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(repo_full_name) DO UPDATE SET
            state=excluded.state, reason=excluded.reason,
            local_path=excluded.local_path, default_branch=excluded.default_branch,
            checked_at=excluded.checked_at
        """,
        (repo, result.state, result.reason or None, result.local_path or None, result.default_branch or None, now),
    )


def backfill_commits(
    database_path: Path,
    repo_full_name: str,
    *,
    since: str | None = None,
    cap: int = MAX_COMMITS_PER_BACKFILL,
    fetch: bool = True,
    clone_path: Path | None = None,
    roots: list[str] | None = None,
    branch: str | None = None,
    force_refresh: bool = False,
) -> BackfillResult:
    """Enumerate *repo_full_name* from its local clone into the commit corpus.

    Dedupes against both ``github_commits`` (PR commits) and existing
    ``github_direct_commits`` rows. A row that already has ``path_coverage =
    'complete'`` is left alone; anything else is upgraded, never downgraded.
    """
    result = BackfillResult(repo=repo_full_name)
    now = _now()
    snapshot_time = now_utc().isoformat()

    path = clone_path or resolve_clone(repo_full_name, roots=roots)
    if path is None:
        result.state = "uncoverable"
        result.reason = "no local clone found under configured local_repo_roots"
        with db_connection(database_path, ensure_github_schema) as conn:
            conn.execute(f"PRAGMA busy_timeout = {_BUSY_TIMEOUT_MS}")
            _record_coverage(conn, repo_full_name, result, now)
            conn.commit()
        return result
    result.local_path = str(path)

    # 0-API Remote Peeking Checkpoint Gating (GH-201)
    proc = run_git(path, "remote", "get-url", "origin", timeout=1.0)
    canonical_url = proc.stdout.strip() if proc.returncode == 0 else f"https://github.com/{repo_full_name}.git"

    peek_map: dict[str, str] | None = None
    if not force_refresh:
        peek_map = peek_remote_refs(path, remote="origin", timeout=2.0)
        if peek_map:
            with db_connection(database_path, ensure_github_schema) as conn:
                conn.execute(f"PRAGMA busy_timeout = {_BUSY_TIMEOUT_MS}")
                if is_commit_walk_cached(conn, canonical_url, peek_map, since):
                    result.skipped_cache = True
                    result.default_branch = branch or _default_branch(path)
                    result.state = "ok"
                    result.reason = "remote refs unchanged (cached checkpoint)"
                    _record_coverage(conn, repo_full_name, result, now)
                    conn.commit()
                    return result

    if fetch:
        code, _, err = _git(path, "fetch", "--quiet", "origin")
        result.fetched = code == 0
        if code != 0:
            # Non-fatal: enumerate what is on disk, but never let the caller
            # read the result as authoritative coverage.
            result.warnings.append(f"fetch failed ({err or 'unknown error'}); clone may be stale")

    # Scope: ALL remote branches by default, not just the default branch.
    #
    # Found by running this against the real clone: `origin/HEAD` here points at
    # `main`, but this repo's actual trunk is `development` -- so a
    # default-branch walk enumerated 515 commits of the wrong branch and missed
    # the measured gap entirely. Deriving "where the work is" from origin/HEAD
    # is an assumption the repo layout does not honour, and the same is true of
    # any repo using a main/develop split.
    #
    # Walking `--remotes=origin` also closes a second hole: commits on branches
    # that were never merged to any trunk. Dedup is by (repo, sha), so overlap
    # between branches costs nothing.
    result.default_branch = branch or _default_branch(path)
    if branch:
        ref_args = [f"origin/{branch}"]
        code, _, _ = _git(path, "rev-parse", "--verify", f"origin/{branch}")
        if code != 0:
            ref_args = [branch]
    else:
        ref_args = ["--remotes=origin"]

    log_args = ["log", *ref_args, f"--format={_LOG_FORMAT}", f"--max-count={cap + 1}"]
    if since:
        log_args.append(f"--since={since}")
    code, raw, err = _git(path, *log_args)
    if code != 0:
        result.state = "uncoverable"
        result.reason = f"git log failed on {' '.join(ref_args)}: {err or 'unknown error'}"
        with db_connection(database_path, ensure_github_schema) as conn:
            conn.execute(f"PRAGMA busy_timeout = {_BUSY_TIMEOUT_MS}")
            _record_coverage(conn, repo_full_name, result, now)
            conn.commit()
        return result

    commits = _parse_log(raw)
    if len(commits) > cap:
        commits = commits[:cap]
        result.capped = True
        result.warnings.append(f"walk capped at {cap} commits; older history not enumerated this run")
    result.commits_seen = len(commits)

    # Capture peek snapshot for checkpointing if not already captured
    if peek_map is None:
        peek_map = peek_remote_refs(path, remote="origin", timeout=2.0)

    any_file_read_failed = False
    with db_connection(database_path, ensure_github_schema) as conn:
        conn.execute(f"PRAGMA busy_timeout = {_BUSY_TIMEOUT_MS}")
        pr_shas = {
            row[0] for row in conn.execute("SELECT sha FROM github_commits WHERE repo_full_name = ?", (repo_full_name,))
        }
        existing = {
            row[0]: row[1]
            for row in conn.execute(
                "SELECT sha, path_coverage FROM github_direct_commits WHERE repo_full_name = ?",
                (repo_full_name,),
            )
        }

        for commit in commits:
            sha = commit["sha"]
            if not sha:
                continue
            # A PR commit is already in the corpus via the PR path; re-persisting
            # it here would duplicate it into github_documents.
            if sha in pr_shas:
                result.commits_skipped_existing += 1
                continue
            if existing.get(sha) == "complete":
                result.commits_skipped_existing += 1
                continue

            paths = _changed_paths(path, sha)
            path_cov = "complete"
            if paths is None:
                path_cov = "failed"
                paths = []
                any_file_read_failed = True

            if _is_merge(path, sha):
                result.merge_commits += 1
            is_new = sha not in existing

            gh.upsert_direct_commit(
                conn,
                (
                    repo_full_name,
                    sha,
                    f"git-backfill:{result.default_branch}",
                    f"refs/heads/{result.default_branch}",
                    "",  # author_login: git has no GitHub login; left to the API path
                    commit["author_name"],
                    commit["message"],
                    commit["committed_at"],
                    f"https://github.com/{repo_full_name}/commit/{sha}",
                    path_cov,
                    now,
                    now,
                ),
                source="git_backfill",
            )
            gh.replace_direct_commit_files(
                conn,
                repo_full_name,
                sha,
                [{"filename": p, "status": "", "additions": None, "deletions": None, "changes": None} for p in paths],
            )
            result.files_written += len(paths)
            if is_new:
                result.commits_inserted += 1
            else:
                result.commits_updated += 1

            # Release the write lock periodically so concurrent readers/writers
            # are not starved for the length of a full-history walk.
            written = result.commits_inserted + result.commits_updated
            if written % _COMMIT_BATCH == 0:
                conn.commit()

        # Atomic Checkpoint Contract (GH-201 / Codex R2):
        # Only certify commit coverage checkpoint if:
        # 1. peek_map was obtained successfully
        # 2. git fetch succeeded
        # 3. History walk was NOT capped
        # 4. Zero commit file reads failed (no git show failure; all rows certified)
        if (
            peek_map is not None
            and result.fetched
            and not result.capped
            and not any_file_read_failed
            and canonical_url
        ):
            record_commit_coverage_checkpoint(
                conn,
                canonical_url,
                peek_map,
                covered_since_utc=since,
                verified_at_utc=now,
                snapshot_time_utc=snapshot_time,
            )

        _record_coverage(conn, repo_full_name, result, now)
        conn.commit()

    return result


def backfill_repos(
    database_path: Path,
    repos: list[str],
    *,
    since: str | None = None,
    cap: int = MAX_COMMITS_PER_BACKFILL,
    fetch: bool = True,
    roots: list[str] | None = None,
    branch: str | None = None,
    force_refresh: bool = False,
) -> list[BackfillResult]:
    """Backfill several repos, never letting one repo's failure hide the rest."""
    return [
        backfill_commits(
            database_path,
            repo,
            since=since,
            cap=cap,
            fetch=fetch,
            roots=roots,
            branch=branch,
            force_refresh=force_refresh,
        )
        for repo in repos
    ]
