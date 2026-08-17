import re
import subprocess
from pathlib import Path

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
) -> subprocess.CompletedProcess[str]:
    """Run ``git`` in *repo_path* without raising for a non-zero exit code.

    This is the single subprocess boundary for Rebalance's git operations.
    Callers retain ownership of command-specific error handling by inspecting
    the returned completed process; timeouts and executable failures still
    raise their standard ``subprocess`` exceptions.
    """
    return subprocess.run(
        ["git", "-C", str(repo_path), *args],
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout,
    )


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
