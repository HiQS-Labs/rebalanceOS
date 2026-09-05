"""GH-182 — a repository belongs to at most one project, enforced on the write paths.

Companion to ``test_alias_dedup_invariant.py``, which *detects* two projects claiming one
repository. These tests pin the two guards that stop the second claim being written at all.

Deterministic and configuration-agnostic: every org and repo name is synthetic, the alias
map is injected rather than read from an operator's ``rbos.config``, and the registry is a
fresh temp file. Nothing here depends on which orgs this checkout's owner has renamed.

Where the guards sit, and why there and not on a database constraint: the registry markdown
is hand-edited YAML and is the source of truth, so SQLite can only ever fail *after* a bad
edit, at the same projection boundary guard 2 already occupies.

1. ``confirm_and_write`` refuses a candidate whose repository an entry already claims, and
   reports it rather than dropping it silently.
2. The refusal is canonical — an org-renamed spelling of a claimed repository still collides.
3. An archived entry holds no claim; retiring a project frees its repositories.
4. Re-confirming a project's own repository is not a collision.
5. ``_registry_to_projection`` refuses to project two active entries claiming one repository.
6. The fixture is not inert — the meta-check. Without the guard the duplicate IS written,
   which is how this defect reached production: the first test written for it inserted a
   duplicate that could never have failed.
"""

import pytest

from rebalance.ingest import config as config_mod
from rebalance.ingest import preflight as preflight_mod
from rebalance.ingest.preflight import confirm_and_write
from rebalance.ingest.registry import (
    DuplicateRepoClaimError,
    Project,
    Registry,
    _registry_to_projection,
    canonical_repo_key,
    read_registry,
    save_registry,
)

OLD_ORG = "oldorg"
NEW_ORG = "NewOrg"
REPO = "widget-service"
OLD_FULL = f"{OLD_ORG}/{REPO}"
NEW_FULL = f"{NEW_ORG}/{REPO}"


@pytest.fixture
def aliases(monkeypatch):
    """Inject a synthetic alias map so this never reads the operator's config."""
    monkeypatch.setattr(config_mod, "get_github_org_aliases", lambda: {OLD_ORG: NEW_ORG})
    return {OLD_ORG: NEW_ORG}


@pytest.fixture
def registry_path(tmp_path):
    """A registry holding one real, human-named project that claims the repository."""
    path = tmp_path / "Projects" / "00-project-registry.md"
    registry = Registry(
        active_projects=[Project(name="Widget Service", status="active", repos=[NEW_FULL], provenance="inferred")]
    )
    save_registry(registry_path=path, registry=registry)
    return path


def _placeholder(repo: str) -> dict:
    """A discovery candidate, shaped exactly as ``discover_candidates`` emits one.

    Its name IS its repository, because at discovery time no project name exists yet.
    That placeholder becoming a permanent project is the whole of GH-182.
    """
    return {
        "name": repo,
        "status": "active",
        "summary": "Recent activity: 9 commits, 19 total events (last 30 days).",
        "repos": [repo],
        "tags": ["A"],
        "provenance": "remote-activity",
    }


def _write(projects, registry_path, tmp_path):
    return confirm_and_write(
        projects=projects,
        vault_path=tmp_path / "vault",
        registry_path=registry_path,
        projects_yaml_path=tmp_path / "vault" / "projects.yaml",
        database_path=tmp_path / "nonexistent.db",
    )


def test_canonical_repo_key_folds_a_renamed_owner(aliases):
    assert canonical_repo_key(OLD_FULL) == canonical_repo_key(NEW_FULL)
    assert canonical_repo_key(f"  {NEW_ORG.upper()}/{REPO}  ") == canonical_repo_key(NEW_FULL)
    assert canonical_repo_key("") == ""


def test_claimed_repository_is_refused_and_reported(aliases, registry_path, tmp_path):
    result = _write([_placeholder(NEW_FULL)], registry_path, tmp_path)

    assert result.project_count == 0
    assert result.skipped_claims == [(NEW_FULL, NEW_FULL, "Widget Service")]

    names = [p.name for p in read_registry(registry_path).active_projects]
    assert names == ["Widget Service"]


def test_the_refusal_is_canonical_not_literal(aliases, registry_path, tmp_path):
    """The stale spelling must collide too, or an org rename re-opens the hole."""
    result = _write([_placeholder(OLD_FULL)], registry_path, tmp_path)

    assert result.project_count == 0
    assert result.skipped_claims == [(OLD_FULL, OLD_FULL, "Widget Service")]


def test_an_archived_entry_holds_no_claim(aliases, tmp_path):
    """Retiring a project must free its repositories, or nothing can ever take them over."""
    path = tmp_path / "Projects" / "00-project-registry.md"
    save_registry(
        registry_path=path,
        registry=Registry(archived_projects=[Project(name="Retired", repos=[NEW_FULL])]),
    )

    result = _write([_placeholder(NEW_FULL)], path, tmp_path)

    assert result.project_count == 1
    assert result.skipped_claims == []


def test_a_project_may_reconfirm_its_own_repository(aliases, registry_path, tmp_path):
    same = {"name": "Widget Service", "status": "active", "repos": [NEW_FULL]}
    result = _write([same], registry_path, tmp_path)

    assert result.project_count == 1
    assert result.skipped_claims == []


def test_two_candidates_in_one_batch_cannot_both_claim_it(aliases, tmp_path):
    """The batch checks itself, not only what was already on disk."""
    path = tmp_path / "Projects" / "00-project-registry.md"
    save_registry(registry_path=path, registry=Registry())

    result = _write([_placeholder(NEW_FULL), _placeholder(OLD_FULL)], path, tmp_path)

    assert result.project_count == 1
    assert result.skipped_claims == [(OLD_FULL, OLD_FULL, NEW_FULL)]


def test_provenance_survives_confirm_and_write(aliases, tmp_path):
    """An unstamped row cannot be told apart from an operator's own — GH-182's real blocker."""
    path = tmp_path / "Projects" / "00-project-registry.md"
    save_registry(registry_path=path, registry=Registry())

    _write([_placeholder(NEW_FULL)], path, tmp_path)

    written = read_registry(path).active_projects
    assert [p.provenance for p in written] == ["remote-activity"]


def test_projection_refuses_two_active_claims(aliases):
    registry = Registry(
        active_projects=[
            Project(name="Widget Service", repos=[NEW_FULL]),
            Project(name=OLD_FULL, repos=[OLD_FULL]),
        ]
    )
    with pytest.raises(DuplicateRepoClaimError) as excinfo:
        _registry_to_projection(registry)

    message = str(excinfo.value)
    assert "Widget Service" in message and OLD_FULL in message


def test_projection_allows_one_project_listing_a_repo_twice(aliases):
    registry = Registry(active_projects=[Project(name="Widget Service", repos=[NEW_FULL, OLD_FULL])])

    projected = _registry_to_projection(registry)

    assert [p["name"] for p in projected["projects"]] == ["Widget Service"]


def test_the_projection_fixture_is_not_inert(aliases, monkeypatch):
    """Bypass the claim key and the same registry projects BOTH rows — the duplicate is real.

    Without this, ``test_projection_refuses_two_active_claims`` could pass against a registry
    the projection would have rejected for some unrelated reason.
    """
    import rebalance.ingest.registry as registry_mod

    monkeypatch.setattr(registry_mod, "canonical_repo_key", lambda repo: "")
    registry = Registry(
        active_projects=[
            Project(name="Widget Service", repos=[NEW_FULL]),
            Project(name=OLD_FULL, repos=[OLD_FULL]),
        ]
    )

    projected = _registry_to_projection(registry)

    assert [p["name"] for p in projected["projects"]] == ["Widget Service", OLD_FULL]


def test_the_fixture_is_not_inert(aliases, registry_path, tmp_path, monkeypatch):
    """Without the guard the duplicate IS written — so these tests can actually fail.

    The first guard written for this defect class inserted a duplicate whose metrics were
    all zero, so summing it changed nothing and the test passed forever. Never again
    without a check that the fixture would break the thing it claims to protect.
    """
    monkeypatch.setattr(preflight_mod, "_claimed_repos", lambda registry: {})

    result = _write([_placeholder(NEW_FULL)], registry_path, tmp_path)

    assert result.project_count == 1
    assert result.skipped_claims == []
    names = [p.name for p in read_registry(registry_path).active_projects]
    assert names == ["Widget Service", NEW_FULL]


# ---------------------------------------------------------------------------
# Guard 3 — the inference writer, which reaches project_registry through
# sync_db directly and so is never seen by the projection guard.
# ---------------------------------------------------------------------------


@pytest.fixture
def inference_db(tmp_path, aliases):
    """A store where one project already claims the repository."""
    import sqlite3

    from rebalance.ingest.db.schema import ensure_project_schema

    path = tmp_path / "inference.db"
    with sqlite3.connect(path) as conn:
        ensure_project_schema(conn)
        conn.execute(
            "INSERT INTO project_registry (name, status, repos_json, custom_fields_json) VALUES (?, ?, ?, ?)",
            (
                "Widget Service",
                "active",
                f'["{NEW_FULL}"]',
                '{"inference": {"generated_by": "activity_inference_v1"}}',
            ),
        )
    return path


def _inferred(name: str, repo: str) -> dict:
    return {"name": name, "status": "active", "repos": [repo], "custom_fields": {}}


def test_inference_will_not_write_a_repo_another_project_claims(inference_db):
    from rebalance.ingest.project_inference import _partition_writable_rows

    writable, skipped = _partition_writable_rows(inference_db, [_inferred(OLD_FULL, OLD_FULL)])

    assert writable == []
    assert skipped == [OLD_FULL]


def test_inference_still_writes_its_own_row(inference_db):
    """A project re-writing the repository it already owns is not a conflict."""
    from rebalance.ingest.project_inference import _partition_writable_rows

    writable, skipped = _partition_writable_rows(inference_db, [_inferred("Widget Service", NEW_FULL)])

    assert [p["name"] for p in writable] == ["Widget Service"]
    assert skipped == []


def test_inference_writes_an_unclaimed_repo(inference_db):
    from rebalance.ingest.project_inference import _partition_writable_rows

    writable, skipped = _partition_writable_rows(inference_db, [_inferred("Gadget", f"{NEW_ORG}/gadget-service")])

    assert [p["name"] for p in writable] == ["Gadget"]
    assert skipped == []


def test_inference_partition_does_not_depend_on_row_order(tmp_path, aliases):
    """With a duplicate already stored, the decision must not flap between runs.

    Ownership is collected per repository as a set, so which of the two existing
    claimants SQLite returns first cannot change the answer.
    """
    import sqlite3

    from rebalance.ingest.db.schema import ensure_project_schema
    from rebalance.ingest.project_inference import _partition_writable_rows

    path = tmp_path / "dupes.db"
    with sqlite3.connect(path) as conn:
        ensure_project_schema(conn)
        for name in ("Widget Service", NEW_FULL):
            conn.execute(
                "INSERT INTO project_registry (name, status, repos_json, custom_fields_json)"
                " VALUES (?, 'active', ?, '{}')",
                (name, f'["{NEW_FULL}"]'),
            )

    writable, skipped = _partition_writable_rows(path, [_inferred("Third Claimant", NEW_FULL)])

    assert writable == []
    assert skipped == ["Third Claimant"]


# ---------------------------------------------------------------------------
# Paths agy's review named as untested. Both pin CURRENT behaviour so a change
# to either is a deliberate decision rather than a silent one.
# ---------------------------------------------------------------------------


def test_a_watched_external_container_does_not_get_a_second_claim(aliases, registry_path, tmp_path):
    """`external: true` is not an exemption, and that is a decision, not an oversight.

    A "Watched — ..." container monitors a repository for *everyone's* activity while a
    normal project claims it for the operator's own work, so the two look like different
    kinds of claim. They are not, for the purpose this guard serves: both rows land in
    project_registry and both are summed by project-level reads, so allowing the pair back
    would reintroduce exactly the double count. An operator who wants both must say which
    row owns the repository.
    """
    watched = {
        "name": "Watched — Widget Service",
        "status": "active",
        "repos": [NEW_FULL],
        "external": True,
    }
    result = _write([watched], registry_path, tmp_path)

    assert result.project_count == 0
    assert result.skipped_claims == [("Watched — Widget Service", NEW_FULL, "Widget Service")]


def test_the_guard_applies_to_the_non_active_segmented_path(aliases, registry_path, tmp_path):
    """A candidate without `status: active` is segmented by activity, and still guarded.

    The collision check sits ahead of the branch that chooses a segment, so a candidate
    cannot dodge it by arriving as `potential` instead of `active`.
    """
    candidate = {"name": "Some Later Name", "status": "potential", "repos": [OLD_FULL]}
    result = _write([candidate], registry_path, tmp_path)

    assert result.project_count == 0
    assert result.skipped_claims == [("Some Later Name", OLD_FULL, "Widget Service")]

    registry = read_registry(registry_path)
    assert [p.name for p in registry.potential_projects] == []
    assert [p.name for p in registry.most_likely_active_projects] == []
