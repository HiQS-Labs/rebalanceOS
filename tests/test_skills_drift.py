"""Guard against drift between .agents/skills and .claude/skills (#258)."""

import filecmp
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_daily_skills_identical():
    agents_daily = REPO_ROOT / ".agents" / "skills" / "daily"
    claude_daily = REPO_ROOT / ".claude" / "skills" / "daily"

    assert agents_daily.exists(), ".agents/skills/daily must exist"
    assert claude_daily.exists(), ".claude/skills/daily must exist"

    agents_files = {
        p.relative_to(agents_daily)
        for p in agents_daily.rglob("*")
        if p.is_file() and not p.name.endswith(".pyc") and "__pycache__" not in p.parts
    }
    claude_files = {
        p.relative_to(claude_daily)
        for p in claude_daily.rglob("*")
        if p.is_file() and not p.name.endswith(".pyc") and "__pycache__" not in p.parts
    }

    assert agents_files == claude_files, f"File set mismatch: {agents_files ^ claude_files}"

    for rel_path in agents_files:
        agent_file = agents_daily / rel_path
        claude_file = claude_daily / rel_path
        assert filecmp.cmp(agent_file, claude_file, shallow=False), f"Divergence detected in skill file: {rel_path}"


def test_no_hardcoded_users_paths_in_skills():
    for base in [REPO_ROOT / ".agents" / "skills", REPO_ROOT / ".claude" / "skills"]:
        for path in base.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            assert "/Users/" not in text, f"Hardcoded /Users/ path found in {path}"
            assert 'Path.home() / "Documents"' not in text, f"Hardcoded Path.home() Documents path found in {path}"
        for path in base.rglob("*.md"):
            text = path.read_text(encoding="utf-8")
            assert "/Users/" not in text, f"Hardcoded /Users/ path found in {path}"
