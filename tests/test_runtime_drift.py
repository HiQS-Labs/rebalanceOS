"""``scripts/stack.sh drift`` reports how far the deployed runtime trails
origin/development, and returns 1 when it does (SOP.md § 7).

Two throwaway repositories stand in for origin and the runtime; the runtime is
declared through the same ``~/.config/rebalance/runtime-root`` file
``install_common.sh`` reads in production, by pointing ``HOME`` at a temp dir. No
network, no operator config, no launchd.
"""

from __future__ import annotations

import os
import subprocess
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

REPO = Path(__file__).resolve().parents[1]
STACK = REPO / "scripts" / "stack.sh"

_GIT_ID = ["-c", "user.name=t", "-c", "user.email=t@example.invalid"]


def _git(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", *_GIT_ID, *args], cwd=cwd, capture_output=True, text=True, check=True).stdout


def _commit(repo: Path, name: str) -> None:
    (repo / name).write_text(name)
    _git(repo, "add", name)
    _git(repo, "commit", "-q", "-m", name)


class RuntimeDriftTests(unittest.TestCase):
    def test_reports_commits_behind_then_up_to_date(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            origin, runtime, home = root / "origin", root / "runtime", root / "home"
            origin.mkdir()
            _git(origin, "init", "-q", "-b", "development")
            _commit(origin, "a")
            _git(root, "clone", "-q", "-b", "development", str(origin), str(runtime))

            # Declare the runtime the way production does.
            cfg = home / ".config" / "rebalance"
            cfg.mkdir(parents=True)
            (cfg / "runtime-root").write_text(str(runtime) + "\n")
            env = {**os.environ, "HOME": str(home)}

            _commit(origin, "b")
            _commit(origin, "c")

            behind = subprocess.run(["bash", str(STACK), "drift"], env=env, capture_output=True, text=True)
            self.assertEqual(behind.returncode, 1, behind.stdout + behind.stderr)
            self.assertIn("2 commit(s) BEHIND origin/development", behind.stdout)
            self.assertIn("pull --ff-only origin development", behind.stdout)

            # Under a git hook GIT_DIR points at the DEV repo. The check must still
            # measure the runtime, or a post-merge hook reports a false "up to date".
            hooked = subprocess.run(
                ["bash", str(STACK), "drift"],
                env={**env, "GIT_DIR": str(origin / ".git"), "GIT_WORK_TREE": str(origin)},
                capture_output=True,
                text=True,
            )
            self.assertEqual(hooked.returncode, 1, hooked.stdout + hooked.stderr)
            self.assertIn("2 commit(s) BEHIND", hooked.stdout)

            _git(runtime, "pull", "-q", "--ff-only", "origin", "development")

            synced = subprocess.run(["bash", str(STACK), "drift"], env=env, capture_output=True, text=True)
            self.assertEqual(synced.returncode, 0, synced.stdout + synced.stderr)
            self.assertIn("up to date with origin/development", synced.stdout)


if __name__ == "__main__":
    unittest.main()
