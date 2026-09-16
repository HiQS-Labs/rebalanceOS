"""Tests for portfolio matrix projection and hardened goal completion in rebalanceOS."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any
import pytest
from starlette.testclient import TestClient

from rebalance.ingest.goals_file import (
    AmbiguousGoalError,
    RawSectionGroup,
    StaleRevisionError,
    complete_goal_in_file,
    compute_goals_revision,
    parse_goals_content,
    parse_sectioned_goals_content,
)
from rebalance.web import _safe_int, app


def test_safe_int_coercion() -> None:
    assert _safe_int(None, 0) == 0
    assert _safe_int(5, 0) == 5
    assert _safe_int(5.7, 0) == 5
    assert _safe_int("9", 0) == 9
    assert _safe_int("  8  ", 0) == 8
    assert _safe_int("invalid", 42) == 42
    assert _safe_int(["list"], 10) == 10


def test_parse_goals_content() -> None:
    content = """# Header
- [ ] Task 1
  Description line 1
  Description line 2
- [x] Done Task
- [ ] Task 2
"""
    items = parse_goals_content(content, limit=None)
    assert len(items) == 2
    assert items[0]["title"] == "Task 1"
    assert items[0]["description"] == "Description line 1 Description line 2"
    assert items[0]["line_index"] == 1
    assert items[1]["title"] == "Task 2"
    assert items[1]["line_index"] == 5


def test_parse_sectioned_goals_content() -> None:
    content = """# Unassociated Goal
- [ ] Orphan Task

## Inspired Magazine / Monetization
- [ ] Setup Stripe Connect
- [x] Completed item
- [ ] Add payout webhooks

## Binoid/Bloomz
- [ ] PCI DSS audit preparation
"""
    groups = parse_sectioned_goals_content(content)
    assert len(groups) == 3

    assert groups[0].header == "Unassociated Goal"
    assert len(groups[0].tasks) == 1
    assert groups[0].tasks[0]["title"] == "Orphan Task"

    assert groups[1].header == "Inspired Magazine / Monetization"
    assert len(groups[1].tasks) == 2
    assert groups[1].tasks[0]["title"] == "Setup Stripe Connect"
    assert groups[1].tasks[1]["title"] == "Add payout webhooks"

    assert groups[2].header == "Binoid/Bloomz"
    assert len(groups[2].tasks) == 1
    assert groups[2].tasks[0]["title"] == "PCI DSS audit preparation"


def test_compute_goals_revision() -> None:
    rev1 = compute_goals_revision("- [ ] Task 1\n")
    rev2 = compute_goals_revision("- [ ] Task 1\n")
    rev3 = compute_goals_revision("- [ ] Task 2\n")
    assert rev1 == rev2
    assert rev1 != rev3
    assert len(rev1) == 64  # SHA-256 hex string


def test_complete_goal_in_file_with_revision(tmp_path: Path) -> None:
    goals_file = tmp_path / "0. Goals.md"
    content = "- [ ] Task 1\n- [ ] Task 2\n"
    goals_file.write_text(content, encoding="utf-8")
    initial_rev = compute_goals_revision(content)

    # 1. Successful completion with valid revision
    rec = complete_goal_in_file(
        goals_file,
        "Task 1",
        line_index=0,
        expected_revision=initial_rev,
    )
    assert rec is not None
    assert rec["title"] == "Task 1"
    assert rec["line_index"] == 0
    new_content = goals_file.read_text(encoding="utf-8")
    assert "- [x] Task 1\n" in new_content

    # 2. Stale revision raises StaleRevisionError
    with pytest.raises(StaleRevisionError) as exc_info:
        complete_goal_in_file(
            goals_file,
            "Task 2",
            line_index=1,
            expected_revision=initial_rev,  # Outdated revision
        )
    assert exc_info.value.expected_revision == initial_rev
    assert exc_info.value.current_revision == rec["goals_revision"]


def test_complete_goal_ambiguous_without_revision(tmp_path: Path) -> None:
    goals_file = tmp_path / "0. Goals.md"
    content = "- [ ] Duplicate Task\n- [ ] Duplicate Task\n"
    goals_file.write_text(content, encoding="utf-8")

    # Omitting revision on duplicate title without matching line_index strictly raises AmbiguousGoalError
    with pytest.raises(AmbiguousGoalError) as exc_info:
        complete_goal_in_file(goals_file, "Duplicate Task", line_index=None)
    assert exc_info.value.title == "Duplicate Task"
    assert exc_info.value.matching_indexes == [0, 1]


def test_complete_goal_api_endpoint(tmp_path: Path, monkeypatch: Any) -> None:
    vault_dir = tmp_path / "Vault"
    vault_dir.mkdir()
    goals_file = vault_dir / "0. Goals.md"
    content = "- [ ] Buy Coffee\n- [ ] Fix Bug\n"
    goals_file.write_text(content, encoding="utf-8")
    rev = compute_goals_revision(content)

    monkeypatch.setattr("rebalance.ingest.config.get_vault_path", lambda: str(vault_dir))
    monkeypatch.setattr("rebalance.web._request_is_local", lambda req: True)

    client = TestClient(app)

    # 1. Stale revision returns 409
    res = client.post(
        "/api/focus5/goals/complete",
        json={"title": "Buy Coffee", "line_index": 0, "goals_revision": "invalid_hash"},
    )
    assert res.status_code == 409
    data = res.json()
    assert data["error"] == "stale_goal_snapshot"

    # 2. Valid revision succeeds and returns new revision
    res = client.post(
        "/api/focus5/goals/complete",
        json={"title": "Buy Coffee", "line_index": 0, "goals_revision": rev},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["ok"] is True
    assert data["title"] == "Buy Coffee"
    assert data["goals_revision"] is not None


def test_portfolio_matrix_endpoint(tmp_path: Path, monkeypatch: Any) -> None:
    vault_dir = tmp_path / "Vault"
    vault_dir.mkdir()
    goals_file = vault_dir / "0. Goals.md"
    content = """# Inspired Magazine / Monetization
- [ ] Task A
- [ ] Task B
- [ ] Task C
- [ ] Task D (should be capped)

# Inspired Magazine / Reader Experience
- [ ] Subtask 1

# Binoid/Bloomz
- [ ] Binoid Task 1

# Nonexistent Project
- [ ] Ghost Task
"""
    goals_file.write_text(content, encoding="utf-8")

    mock_projects = [
        {
            "name": "Inspired Magazine",
            "priority_tier": 4,
            "custom_fields": {
                "revenue_ranking": 5,
                "revenue_potential": 4,
                "computed_score": 9,
            },
        },
        {
            "name": "Binoid/Bloomz",
            "priority_tier": 5,
            "custom_fields": {
                "revenue_ranking": 5,
                "revenue_potential": 3,
                "computed_score": 8,
            },
        },
        {
            "name": "Bare Project",
            "priority_tier": 2,
            "custom_fields": {},
        },
    ]

    dummy_db = tmp_path / "dummy.db"
    dummy_db.touch()

    monkeypatch.setattr("rebalance.ingest.config.get_vault_path", lambda: str(vault_dir))
    monkeypatch.setattr("rebalance.paths.resolve_database_path", lambda: dummy_db)
    monkeypatch.setattr("rebalance.ingest.registry.get_projects", lambda db, status="active": mock_projects)

    client = TestClient(app)
    res = client.get("/portfolio-matrix.json")
    assert res.status_code == 200
    data = res.json()

    assert "goals_revision" in data
    assert data["goals_revision"] == compute_goals_revision(content)
    projects = data["projects"]

    # 4 rows expected:
    # - Inspired Magazine / Monetization (score 9)
    # - Inspired Magazine / Reader Experience (score 9)
    # - Binoid/Bloomz (score 8)
    # - Bare Project (score 2)
    assert len(projects) == 4

    # Verification of sorting by computed_score desc
    assert projects[0]["name"] == "Inspired Magazine"
    assert projects[0]["computed_score"] == 9
    assert projects[0]["subproject"] == "Monetization"
    assert len(projects[0]["tasks"]) == 3  # Capped at 3

    assert projects[1]["name"] == "Inspired Magazine"
    assert projects[1]["subproject"] == "Reader Experience"
    assert len(projects[1]["tasks"]) == 1

    assert projects[2]["name"] == "Binoid/Bloomz"
    assert projects[2]["computed_score"] == 8
    assert projects[2]["subproject"] is None
    assert len(projects[2]["tasks"]) == 1

    assert projects[3]["name"] == "Bare Project"
    assert projects[3]["computed_score"] == 2
    assert projects[3]["subproject"] is None
    assert projects[3]["tasks"] == []
