import hashlib
import json
import os
import re
import shlex
import signal
import subprocess
import time
from pathlib import Path

__all__ = [
    "DEFAULT_PRUNE_DIRS",
    "build_hardened_ssh_command",
    "canonical_github_url",
    "compute_origin_ref_digest",
    "git_pull_rebase_safe",
    "parse_github_remote_url",
    "peek_remote_refs",
    "run_git",
    "should_descend",
]

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
        s = s[len("git@github.com:"):]
    elif s.startswith("https://github.com/"):
        s = s[len("https://github.com/"):]
    elif s.startswith("http://github.com/"):
        s = s[len("http://github.com/"):]
    elif s.startswith("ssh://git@github.com/"):
        s = s[len("ssh://git@github.com/"):]
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
    origin_branches = {
        ref: sha for ref, sha in ref_map.items() if ref.startswith("refs/heads/")
    }
    encoded = json.dumps(sorted(origin_branches.items())).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def git_pull_rebase_safe(
    repo_path: Path,
    *,
    timeout: float = 30.0,
) -> subprocess.CompletedProcess[str]:
    """Pull with rebase and abort a failed rebase before returning its result.

    The original failed result is always returned, so the caller can report
    its stderr/stdout.  Aborting is deliberately best-effort: it prevents a
    conflicted rebase from leaking into a later scheduled run without masking
    the operation that actually failed.
    """
    result = run_git(repo_path, "pull", "--rebase", timeout=timeout)
    if result.returncode != 0:
        try:
            run_git(repo_path, "rebase", "--abort", timeout=timeout)
        except (OSError, subprocess.SubprocessError):
            pass
    return result


def _git(repo_path: Path, *args: str, timeout: float = 30.0) -> str | None:
    """Compatibility helper returning stdout, or ``None`` for git failures."""
    try:
        result = run_git(repo_path, *args, timeout=timeout)
        return result.stdout.strip() if result.returncode == 0 else None
    except subprocess.TimeoutExpired:
        return None
