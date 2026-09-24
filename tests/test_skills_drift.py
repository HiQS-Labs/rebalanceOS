"""Guard against drift between .agents/skills and .claude/skills (#258)."""

import os
import filecmp
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_daily_skills_identical():
    agents_daily = REPO_ROOT / ".agents" / "skills" / "daily"
    claude_daily = REPO_ROOT / ".claude" / "skills" / "daily"

    assert agents_daily.exists(), ".agents/skills/daily must exist"
    assert claude_daily.exists(), ".claude/skills/daily must exist"

    # Compare all files in daily skill folder
    for root, _, files in os.walk(agents_daily):
        rel_dir = Path(root).relative_to(agents_daily)
        claude_dir = claude_daily / rel_dir
        for f in files:
            if f.endswith(".pyc") or f == "__pycache__":
                continue
            agent_file = Path(root) / f
            claude_file = claude_dir / f
            assert claude_file.exists(), f"Missing mirrored file: {claude_file}"
            assert filecmp.cmp(agent_file, claude_file, shallow=False), f"Divergence detected in skill file: {f}"


def test_no_hardcoded_users_paths_in_skills():
    skills_root = REPO_ROOT / ".agents" / "skills"
    for path in skills_root.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "/Users/" not in text, f"Hardcoded /Users/ path found in {path}"
    for path in skills_root.rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        assert "/Users/" not in text, f"Hardcoded /Users/ path found in {path}"
