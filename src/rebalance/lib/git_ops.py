import fcntl
import hashlib
import json
import os
import re
import shlex
import signal
import subprocess
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Callable, Iterator, TextIO, Any

__all__ = [
    "DEFAULT_PRUNE_DIRS",
    "build_hardened_ssh_command",
    "canonical_github_url",
    "compute_origin_ref_digest",
    "git_pull_rebase_safe",
    "git_publish_lock",
    "publication_state_error",
    "publish_git_paths",
    "GitPublishLockBusy",
    "parse_github_remote_url",
    "peek_remote_refs",
    "run_git",
    "should_descend",
]


class GitPublishLockBusy(RuntimeError):
    """Another Rebalance publisher owns the target checkout."""


@contextmanager
def git_publish_lock(repo_path: Path) -> Iterator[TextIO]:
    """Hold the one non-blocking advisory lock shared by Rebalance publishers."""
    result = run_git(repo_path, "rev-parse", "--absolute-git-dir")
    if result.returncode != 0 or not result.stdout.strip():
        raise RuntimeError(result.stderr.strip() or "cannot resolve git directory")
    lock_path = Path(result.stdout.strip()) / "rebalance-publish.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    handle = lock_path.open("a+", encoding="utf-8")
    try:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise GitPublishLockBusy(f"publisher busy for {repo_path}") from exc
        yield handle
    finally:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        finally:
            handle.close()


# remote_url forms mapped to owner/repo:
#   https://github.com/Owner/Repo.git
#   git@github.com:Owner/Repo.git
#   ssh://git@github.com/Owner/Repo
#
# Canonical owner (GH-5 Phase 1) of what were two near-identical regexes:
# ask_self_scan._REMOTE_RE and local_repos._FULL_NAME_RE. The two differed only
# in their character class — ask_self_scan matched `[^/]+`, local_repos the
# narrower `[A-Za-z0-9_.-]+`. The permissive form is canonical: it is what the
# ask_self inventory has always used, and narrowing it would silently drop repos
# whose owner or name contains a character outside that set.
_GITHUB_REMOTE_RE = re.compile(
    r"""(?:github\.com[:/])(?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?/?$""",
    re.IGNORECASE,
)


def parse_github_remote_url(remote_url: str | None) -> str | None:
    """Parse a git remote URL into ``owner/repo`` (original casing), or None."""
    if not remote_url:
        return None
    match = _GITHUB_REMOTE_RE.search(remote_url.strip())
    if not match:
        return None
    return f"{match.group('owner')}/{match.group('repo')}"


def canonical_github_url(url_or_name: str) -> str:
    """Normalize any GitHub URL or owner/repo shorthand to standard canonical https URL."""
    s = (url_or_name or "").strip()
    if s.endswith(".git"):
        s = s[:-4]
    if s.startswith("git@github.com:"):
        s = s[len("git@github.com:") :]
    elif s.startswith("https://github.com/"):
        s = s[len("https://github.com/") :]
    elif s.startswith("http://github.com/"):
        s = s[len("http://github.com/") :]
    elif s.startswith("ssh://git@github.com/"):
        s = s[len("ssh://git@github.com/") :]
    parts = s.strip("/").split("/")
    if len(parts) == 2:
        return f"https://github.com/{parts[0].lower()}/{parts[1].lower()}.git"
    return url_or_name.strip()


# Directories never worth descending into when walking for git checkouts or
# harness files. Canonical owner (GH-5 Phase 2) — moved here from
# ``ask_self_scan._PRUNE_DIRS``, which was the de-facto owner via a leaf import.
#
# Standalone scripts that cannot reach ``rebalance.lib`` at runtime (notably
# ``experimental/git-pulse/discover-repos.py``, which sets up no sys.path)
# deliberately keep their own lighter rule rather than coupling to this module.
DEFAULT_PRUNE_DIRS = frozenset(
    {
        "node_modules",
        ".venv",
        "venv",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "build",
        "dist",
        ".next",
        ".cache",
        "Library",
        ".Trash",
        ".npm",
        ".cargo",
        "site-packages",
        ".tox",
        ".gradle",
        "target",
        "vendor",
        ".terraform",
        "DerivedData",
        ".git",
    }
)


def should_descend(name: str, *, prune: frozenset[str] = DEFAULT_PRUNE_DIRS) -> bool:
    """True if a directory named *name* is worth descending into during a walk.

    Prunes the known-heavy directories in *prune*, then all hidden directories.
    ``.git`` is matched by both rules — walkers detect a repo by its ``.git``
    marker and never descend into it.
    """
    if name in prune:
        return False
    return not name.startswith(".")


def run_git(
    repo_path: Path,
    *args: str,
    timeout: float = 30.0,
    extra_env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run ``git`` in *repo_path* without raising for a non-zero exit code.

    This is the single subprocess boundary for Rebalance's git operations.
    Callers retain ownership of command-specific error handling by inspecting
    the returned completed process; timeouts and executable failures still
    raise their standard ``subprocess`` exceptions.
    Spawns in a new session (dedicated process group) so timeouts cleanly kill
    the entire descendant process tree (SSH helpers, credential helpers).
    """
    env = None
    if extra_env:
        env = os.environ.copy()
        env.update(extra_env)

    cmd = ["git", "-C", str(repo_path), *args]
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
        start_new_session=True,
    )
    try:
        stdout, stderr = proc.communicate(timeout=timeout)
        return subprocess.CompletedProcess(
            args=cmd,
            returncode=proc.returncode,
            stdout=stdout,
            stderr=stderr,
        )
    except subprocess.TimeoutExpired as exc:
        try:
            pgid = os.getpgid(proc.pid)
            os.killpg(pgid, signal.SIGKILL)
        except OSError:
            try:
                proc.kill()
            except OSError:
                pass
        proc.communicate()
        raise exc
    except Exception:
        try:
            pgid = os.getpgid(proc.pid)
            os.killpg(pgid, signal.SIGKILL)
        except OSError:
            try:
                proc.kill()
            except OSError:
                pass
        raise


def build_hardened_ssh_command(
    repo_path: Path | None = None,
    extra_ssh_opts: str = "",
    timeout: float = 1.0,
) -> str:
    """Build a hardened, non-interactive SSH command honoring user configuration.

    Reads GIT_SSH_COMMAND or core.sshCommand, neutralizes conflicting prompt options
    (e.g. BatchMode=no), and enforces BatchMode=yes and ConnectTimeout=5.
    """
    ssh_base = os.environ.get("GIT_SSH_COMMAND")
    if not ssh_base and repo_path:
        try:
            cfg = run_git(repo_path, "config", "--get", "core.sshCommand", timeout=timeout)
            if cfg.returncode == 0 and cfg.stdout.strip():
                ssh_base = cfg.stdout.strip()
        except Exception:
            pass
    if not ssh_base:
        ssh_base = "ssh"

    try:
        tokens = shlex.split(ssh_base)
    except ValueError:
        tokens = ["ssh"]
    if not tokens:
        tokens = ["ssh"]

    binary = tokens[0]
    user_tokens = tokens[1:]

    filtered_tokens: list[str] = []
    skip_next = False
    for i, tok in enumerate(user_tokens):
        if skip_next:
            skip_next = False
            continue
        tok_lower = tok.lower()
        if tok == "-o" and i + 1 < len(user_tokens):
            val = user_tokens[i + 1].lower()
            if val.startswith("batchmode=") or val.startswith("connecttimeout="):
                skip_next = True
                continue
        elif tok_lower.startswith("-obatchmode=") or tok_lower.startswith("-oconnecttimeout="):
            continue
        filtered_tokens.append(tok)

    enforced = ["-o", "BatchMode=yes", "-o", "ConnectTimeout=5"]
    if extra_ssh_opts:
        try:
            enforced.extend(shlex.split(extra_ssh_opts))
        except ValueError:
            enforced.append(extra_ssh_opts)

    return shlex.join([binary] + enforced + filtered_tokens)


def peek_remote_refs(
    repo_path: Path,
    remote: str = "origin",
    *,
    timeout: float = 2.0,
    extra_ssh_opts: str = "",
) -> dict[str, str] | None:
    """Peek remote refs via git ls-remote in a hardened, non-interactive environment.

    Enforces a strict shared deadline through SSH config lookup, remote execution, and cleanup.
    Returns mapping of ref_name -> sha, or None if probe failed, timed out, or unverified.
    """
    start_time = time.monotonic()
    config_timeout = min(0.5, max(0.01, timeout * 0.25))
    ssh_cmd = build_hardened_ssh_command(repo_path, extra_ssh_opts, timeout=config_timeout)

    rem_timeout = timeout - (time.monotonic() - start_time)
    if rem_timeout <= 0:
        return None

    extra_env = {
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_ASKPASS": "",
        "SSH_ASKPASS": "",
        "GIT_SSH_COMMAND": ssh_cmd,
    }

    try:
        proc = run_git(
            repo_path,
            "ls-remote",
            remote,
            timeout=rem_timeout,
            extra_env=extra_env,
        )
        if proc.returncode != 0:
            return None

        ref_map: dict[str, str] = {}
        for line in proc.stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split(None, 1)
            if len(parts) != 2:
                return None
            sha, ref_name = parts
            if len(sha) not in (40, 64) or not all(c in "0123456789abcdefABCDEF" for c in sha):
                return None
            ref_map[ref_name] = sha

        if not ref_map or not any(k.startswith("refs/heads/") for k in ref_map):
            return None

        return ref_map
    except (subprocess.TimeoutExpired, OSError):
        return None


def compute_origin_ref_digest(ref_map: dict[str, str]) -> str:
    """Compute canonical hash of all origin branch heads (refs/heads/*)."""
    origin_branches = {ref: sha for ref, sha in ref_map.items() if ref.startswith("refs/heads/")}
    encoded = json.dumps(sorted(origin_branches.items())).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def publication_state_error(repo_path: Path, owned_paths: list[str] | None = None) -> str | None:
    """Refuse foreign state; caller must hold git_publish_lock until publication ends."""
    git_dir = run_git(repo_path, "rev-parse", "--absolute-git-dir")
    if git_dir.returncode:
        return git_dir.stderr.strip() or "not a Git checkout"
    state = Path(git_dir.stdout.strip())
    if any(
        (state / name).exists()
        for name in ("rebase-merge", "rebase-apply", "MERGE_HEAD", "CHERRY_PICK_HEAD", "REVERT_HEAD")
    ):
        return "publication blocked: existing Git operation; preserve it for its owner"
    branch = run_git(repo_path, "symbolic-ref", "--quiet", "HEAD")
    if branch.returncode:
        return "publication blocked: detached HEAD; preserve local work"
    if owned_paths is not None:
        for path in owned_paths:
            if (
                not path
                or Path(path).is_absolute()
                or ".." in Path(path).parts
                or Path(path).parts[0] == ".git"
                or not (repo_path / path).resolve().is_relative_to(repo_path.resolve())
                or (repo_path / path).is_symlink()
            ):
                return "publication blocked: invalid owned path"
        for args, kind in (
            (["diff", "--cached", "--name-only", "-z"], "staged"),
            (["diff", "--name-only", "-z"], "unstaged"),
        ):
            result = run_git(repo_path, *args)
            if result.returncode:
                return result.stderr.strip() or "cannot inspect Git state"
            foreign = set(result.stdout.rstrip("\0").split("\0")) - set(owned_paths) - {""}
            if foreign:
                return f"publication blocked: unrelated {kind} paths: {', '.join(sorted(foreign))}"
    return None


def git_pull_rebase_safe(
    repo_path: Path,
    *,
    timeout: float = 30.0,
    resolve_conflicts: Callable[[], bool] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Reconcile under the caller's lock; abort only a rebase we started.

    A narrow owner-supplied resolver may fix generated-file conflicts. It must
    refuse all other conflicts. The bound prevents replaying an arbitrary backlog.
    """
    error = publication_state_error(repo_path)
    if error:
        return subprocess.CompletedProcess(["git", "pull", "--rebase"], 1, "", error)
    try:
        result = run_git(repo_path, "-c", "rebase.autoStash=false", "pull", "--rebase", timeout=timeout)
        for _ in range(3):
            if result.returncode == 0 or resolve_conflicts is None or not resolve_conflicts():
                break
            result = run_git(repo_path, "-c", "core.editor=true", "rebase", "--continue", timeout=timeout)
    except (OSError, subprocess.SubprocessError, ValueError) as exc:
        result = subprocess.CompletedProcess(["git", "pull", "--rebase"], 1, "", str(exc))
    if result.returncode != 0:
        git_dir = run_git(repo_path, "rev-parse", "--absolute-git-dir")
        state = Path(git_dir.stdout.strip())
        if any((state / name).exists() for name in ("rebase-merge", "rebase-apply")):
            aborted = run_git(repo_path, "rebase", "--abort", timeout=timeout)
            if aborted.returncode:
                result.stderr += "\nRebase abort failed; preserve checkout and inspect manually."
    return result


def publish_git_paths(
    repo_path: Path,
    paths: list[str],
    message: str,
    *,
    push: bool = True,
    resolve_conflicts: Callable[[], bool] | None = None,
) -> dict[str, Any]:
    """Commit exact owned paths, deliver once plus one race retry, under caller lock.

    Git commits are the durable pending output. No model, stash or reset is used.
    Foreign staged changes are refused even though --only also bounds the commit.
    """
    error = publication_state_error(repo_path, paths)
    if error:
        return {"committed": False, "pushed": False, "git_error": error}
    proc = run_git(repo_path, "add", "--", *paths)
    if proc.returncode:
        return {"committed": False, "pushed": False, "git_error": proc.stderr.strip()}
    diff = run_git(repo_path, "diff", "--cached", "--quiet", "--", *paths)
    committed = diff.returncode == 1
    if diff.returncode not in (0, 1):
        return {"committed": False, "pushed": False, "git_error": "cannot inspect staged output"}
    if committed:
        proc = run_git(repo_path, "commit", "--only", "-m", message, "--", *paths)
        if proc.returncode:
            return {"committed": False, "pushed": False, "git_error": proc.stderr.strip()}
    result: dict[str, Any] = {"committed": committed, "pushed": False}
    if not push:
        return result
    proc = run_git(repo_path, "push")
    if proc.returncode and ("rejected" in proc.stderr or "fetch first" in proc.stderr):
        result["repair_log"] = ["one bounded pull/rebase and push retry"]
        proc = git_pull_rebase_safe(repo_path, resolve_conflicts=resolve_conflicts)
        if proc.returncode == 0:
            proc = run_git(repo_path, "push")
            result["repaired"] = proc.returncode == 0
    if proc.returncode:
        result.update(git_error=proc.stderr.strip() or proc.stdout.strip(), pending=True)
        return result
    # A successful push must attest the exact committed blobs on the configured upstream.
    for path in paths:
        local = run_git(repo_path, "rev-parse", f"HEAD:{path}")
        remote = run_git(repo_path, "rev-parse", f"@{{u}}:{path}")
        if local.returncode or remote.returncode or local.stdout != remote.stdout:
            result["git_error"] = f"remote output verification failed: {path}"
            return result
    result["pushed"] = True
    if not committed:
        result["reason"] = "no content change"
    return result


def _git(repo_path: Path, *args: str, timeout: float = 30.0) -> str | None:
    """Compatibility helper returning stdout, or ``None`` for git failures."""
    try:
        result = run_git(repo_path, *args, timeout=timeout)
        return result.stdout.strip() if result.returncode == 0 else None
    except subprocess.TimeoutExpired:
        return None
