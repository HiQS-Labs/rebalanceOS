"""The version is written down twice; this pins the two copies together.

`pyproject.toml` carries the packaging version and `rebalance.__version__`
carries the runtime-reported one (`rebalance version`). The 0.69.7/0.69.8
bumps updated only pyproject, so the runtime under-reported until a sync
commit — the same write-it-down-once failure GH-5 keeps deleting elsewhere.
A literal in `__init__` costs nothing at import time (reading pyproject or
package metadata on every import would not), so the duplicate stays and this
test makes it impossible to move one without the other.
"""

from __future__ import annotations

import re
from pathlib import Path

import rebalance

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_runtime_version_matches_pyproject():
    pyproject = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    m = re.search(r'^version = "([^"]+)"', pyproject, flags=re.MULTILINE)
    assert m, "no version field found in pyproject.toml"
    assert rebalance.__version__ == m.group(1), (
        f"pyproject says {m.group(1)} but rebalance.__version__ is "
        f"{rebalance.__version__} — bump both together"
    )
