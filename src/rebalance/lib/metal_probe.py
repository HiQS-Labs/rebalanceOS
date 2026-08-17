"""GH-250 / GH-42 — probe for a usable Metal device OUT OF PROCESS.

When no Metal device is reachable, mlx does not raise — it ABORTS. The device
constructor indexes an empty device array, ObjC throws, and the exception is
uncaught in a C++ constructor:

    mlx::core::metal::MetalAllocator::MetalAllocator()
    mlx::core::metal::Device::Device()
    -[__NSArray0 objectAtIndex:]  ->  objc_exception_throw
    std::__terminate  ->  abort            (SIGABRT, "Abort trap: 6")

SIGABRT is a signal, so `try/except RuntimeError` cannot see it, and it takes
the whole process down with it -- not just the caller. A subprocess is the
only safe probe: a crash there is an exit code, not our death.

GH-250 introduced this probe for the test suite (tests/conftest.py used to
carry its own private copy); GH-42 found the same abort reachable from normal
production use (embed_chunks -> mlx_embeddings.load), so this lives here as
the one shared implementation both import.
"""

from __future__ import annotations

import functools
import os
import subprocess
import sys

_METAL_PROBE = "import mlx.core as mx; mx.array([1.0, 2.0]).sum().item()"


@functools.lru_cache(maxsize=1)
def metal_available() -> bool:
    """True when mlx can actually create a Metal device and run an op.

    Never raises and never aborts the caller -- failure of any kind (missing
    module, empty device list, abort, timeout) reports False. Cached for the
    lifetime of this process, so the cost is one subprocess per session.

    Set ``REBALANCE_ASSUME_NO_METAL=1`` to force False without probing. That is
    the belt-and-braces switch for an environment we already know is GPU-less
    (an automated relay/marathon turn), and it is what makes the skip path
    testable on a machine that *does* have Metal.
    """
    if os.environ.get("REBALANCE_ASSUME_NO_METAL") == "1":
        return False
    try:
        proc = subprocess.run(
            [sys.executable, "-c", _METAL_PROBE],
            capture_output=True,
            timeout=120,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return proc.returncode == 0
