"""Architecture contracts for the shared GitHub HTTP client."""

from __future__ import annotations

import ast
from pathlib import Path


_INGEST_DIR = Path(__file__).resolve().parents[1] / "src" / "rebalance" / "ingest"


def _authorization_header_literals(path: Path) -> list[int]:
    """Return lines that construct an Authorization header, excluding comments."""
    tree = ast.parse(path.read_text(), filename=str(path))
    lines: list[int] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Dict):
            for key in node.keys:
                if isinstance(key, ast.Constant) and key.value == "Authorization":
                    lines.append(node.lineno)
        elif isinstance(node, ast.Subscript):
            key = node.slice
            if isinstance(key, ast.Constant) and key.value == "Authorization":
                lines.append(node.lineno)
    return lines


def test_github_authorization_headers_are_constructed_only_by_shared_client() -> None:
    violations = {
        path.relative_to(_INGEST_DIR): _authorization_header_literals(path)
        for path in _INGEST_DIR.rglob("*.py")
        if path.name != "_http.py" and _authorization_header_literals(path)
    }
    assert violations == {}, f"GitHub Authorization headers must be owned by _http.py: {violations}"
