import subprocess
from pathlib import Path

# Directories never worth descending into when walking for git checkouts or
# harness files. Canonical owner (GH-5 Phase 2) — moved here from
# ``ask_self_scan._PRUNE_DIRS``, which was the de-facto owner via a leaf import.
#
# Standalone scripts that cannot reach ``rebalance.lib`` at runtime (notably
# ``experimental/git-pulse/discover-repos.py``, which sets up no sys.path)
# deliberately keep their own lighter rule rather than coupling to this module.
DEFAULT_PRUNE_DIRS = frozenset({
    "node_modules", ".venv", "venv", "__pycache__", ".pytest_cache",
    ".mypy_cache", ".ruff_cache", "build", "dist", ".next", ".cache",
    "Library", ".Trash", ".npm", ".cargo", "site-packages", ".tox",
    ".gradle", "target", "vendor", ".terraform", "DerivedData", ".git",
})


def should_descend(name: str, *, prune: frozenset[str] = DEFAULT_PRUNE_DIRS) -> bool:
    """True if a directory named *name* is worth descending into during a walk.

    Prunes the known-heavy directories in *prune*, then all hidden directories.
    ``.git`` is matched by both rules — walkers detect a repo by its ``.git``
    marker and never descend into it.
    """
    if name in prune:
        return False
    return not name.startswith(".")


def _git(repo_path: Path, *args: str, timeout: float = 30.0) -> str | None:
    """Run git in *repo_path* and return stdout. Returns None if it fails."""
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_path), *args],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.stdout.strip() if result.returncode == 0 else None
    except subprocess.TimeoutExpired:
        return None
