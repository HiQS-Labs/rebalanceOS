"""Unit tests for utils/daily_synthesis.py (GH-74).

Merges tests/test_obsidian_daily_sync.py (GH-112) and
tests/test_git_pulse_daily_synthesis.py (GH-114), adapted to the merged
module's API, plus a new ordering-guarantee test: the two predecessor scripts
depended on two separate launchd fire times to keep the pulse block above the
git-pulse block; this module does both in one process, so the guarantee is now
that the pulse block is upserted before the git-pulse block in a single run.
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

# utils/ is not a package; the module lives there and reuses obsidian_daily_rollover.
UTILS = Path(__file__).resolve().parent.parent / "utils"
sys.path.insert(0, str(UTILS))
import daily_synthesis as ds  # noqa: E402

# Fixed run-time for byte-stable block assertions (18:20 -> "6:20 PM").
GEN_AT = datetime(2026, 7, 4, 18, 20)


# ===========================================================================
# 1. Shared sentinel-block logic (pulse markers as the representative case)
# ===========================================================================


class TestUpsertPulseBlock:
    def test_upsert_appends_when_no_block(self):
        content = "# 0. Today's Notes\n\nSome manual notes.\n"
        out = ds.upsert_pulse_block(content, "Summary A", GEN_AT)
        assert out.startswith(content)  # manual notes preserved verbatim at the top
        assert out.count(ds.PULSE_MARKER_START) == 1
        assert out.count(ds.PULSE_MARKER_END) == 1
        assert "Summary A" in out

    def test_upsert_replaces_in_place_and_is_idempotent(self):
        content = "# 0. Today's Notes\n\nManual note above.\n"
        once = ds.upsert_pulse_block(content, "First summary", GEN_AT)
        twice = ds.upsert_pulse_block(once, "Second summary", GEN_AT)
        assert twice.count(ds.PULSE_MARKER_START) == 1
        assert twice.count(ds.PULSE_MARKER_END) == 1
        assert "Second summary" in twice
        assert "First summary" not in twice
        # Re-running with the SAME summary is a fixed point (byte-stable).
        assert ds.upsert_pulse_block(twice, "Second summary", GEN_AT) == twice

    def test_upsert_preserves_manual_notes_above(self):
        manual = "# 0. Today's Notes\n\n- bought milk\n- called Jose\n"
        out = ds.upsert_pulse_block(manual, "AI text", GEN_AT)
        assert out[: len(manual)] == manual

    def test_upsert_collapses_accidental_duplicate_blocks(self):
        dup = (
            f"notes\n{ds.PULSE_MARKER_START}\nold one\n{ds.PULSE_MARKER_END}\n"
            f"{ds.PULSE_MARKER_START}\nold two\n{ds.PULSE_MARKER_END}\n"
        )
        out = ds.upsert_pulse_block(dup, "fresh", GEN_AT)
        assert out.count(ds.PULSE_MARKER_START) == 1
        assert out.count(ds.PULSE_MARKER_END) == 1
        assert "fresh" in out and "old one" not in out and "old two" not in out

    def test_upsert_marked_block_on_empty_content_has_no_leading_blank_lines(self):
        """The CLIO log's first-ever write is the production case for this."""
        block = ds.build_pulse_block("hello", GEN_AT)
        assert ds.upsert_marked_block("", block, ds.PULSE_MARKER_START, ds.PULSE_MARKER_END) == block


@pytest.mark.parametrize(
    "hour,minute,expected",
    [
        (18, 0, "6:00 PM"),
        (6, 5, "6:05 AM"),
        (0, 0, "12:00 AM"),
        (12, 0, "12:00 PM"),
        (23, 55, "11:55 PM"),
    ],
)
def test_format_time(hour, minute, expected):
    assert ds._format_time(datetime(2026, 7, 4, hour, minute)) == expected


def test_pulse_block_carries_auto_generated_reminder():
    block = ds.build_pulse_block("body text", datetime(2026, 7, 4, 18, 0))
    assert "*Auto-generated at 6:00 PM.*" in block
    assert block.index(ds.PULSE_BLOCK_HEADING) < block.index("Auto-generated") < block.index("body text")


@pytest.mark.parametrize(
    "hour,expected", [(0, True), (2, True), (11, True), (17, True), (18, False), (19, False), (23, False)]
)
def test_is_late_run(hour, expected):
    assert ds.is_late_run(datetime(2026, 7, 4, hour, 30)) is expected


# ===========================================================================
# 2. Git Pulse block logic (its own markers/heading, CLIO, no-clobber guard)
# ===========================================================================


def test_git_pulse_build_block():
    dt = datetime(2026, 7, 5, 18, 30)
    summary = "Mock summary"
    block = ds.build_git_pulse_block(summary, dt)

    assert ds.GIT_PULSE_MARKER_START in block
    assert ds.GIT_PULSE_MARKER_END in block
    assert ds.GIT_PULSE_BLOCK_HEADING in block
    assert "6:30 PM" in block
    assert summary in block


def test_git_pulse_upsert_appends_to_empty():
    dt = datetime(2026, 7, 5, 18, 30)
    new_content = ds.upsert_git_pulse_block("", "New summary", dt)
    assert ds.GIT_PULSE_MARKER_START in new_content
    assert "New summary" in new_content


def test_git_pulse_upsert_appends_to_existing_text():
    dt = datetime(2026, 7, 5, 18, 30)
    content = "Some existing text.\n"
    new_content = ds.upsert_git_pulse_block(content, "New summary", dt)
    assert new_content.startswith("Some existing text.\n\n")
    assert ds.GIT_PULSE_MARKER_START in new_content


def test_git_pulse_upsert_replaces_existing_block():
    dt2 = datetime(2026, 7, 5, 19, 0)
    content = f"Prefix\n\n{ds.GIT_PULSE_MARKER_START}\nOld summary\n{ds.GIT_PULSE_MARKER_END}\n\nSuffix"
    new_content = ds.upsert_git_pulse_block(content, "New summary", dt2)
    assert "Prefix" in new_content
    assert "Suffix" in new_content
    assert "Old summary" not in new_content
    assert "New summary" in new_content
    assert new_content.count(ds.GIT_PULSE_MARKER_START) == 1


def test_synthesize_git_pulse_zero_rows():
    tsv_content = "local_day\tlocal_time\tutc_time\tdevice_id\tdevice_name\trepo\tbranch\tshort_sha\tsubject"
    assert ds.synthesize_git_pulse(tsv_content) == ds.FALLBACK_SUMMARY
    assert ds.synthesize_git_pulse("") == ds.FALLBACK_SUMMARY


@patch("rebalance.ingest.config.get_gemini_api_key")
@patch("rebalance.ingest.querier._synthesize_gemini")
def test_synthesize_git_pulse_with_rows(mock_synthesize, mock_get_key):
    mock_get_key.return_value = "fake_key"
    mock_synthesize.return_value = "Mocked LLM summary"

    tsv_content = (
        "local_day\tlocal_time\tutc_time\tdevice_id\tdevice_name\trepo\tbranch\tshort_sha\tsubject\n"
        "2026-07-05\t10:00 UTC\t2026-07-05T10:00:00Z\tmac-mini\tMac Mini\trebalance-OS\tmain\ta1b2c3d\tfix: x\n"
    )
    result = ds.synthesize_git_pulse(tsv_content)

    assert result == "Mocked LLM summary"
    mock_synthesize.assert_called_once()
    args, kwargs = mock_synthesize.call_args
    assert tsv_content in args[0]


# --- CLIO block logic ----------------------------------------------------


def test_upsert_clio_block_new_file():
    dt = datetime(2026, 7, 9, 18, 30)
    new_content = ds.upsert_clio_block("", "Did some work", dt)
    assert "<!-- Git Pulse Daily Summary 2026-07-09 Start -->" in new_content
    assert "<!-- Git Pulse Daily Summary 2026-07-09 End -->" in new_content
    assert "2026-07-09" in new_content
    assert "Did some work" in new_content


def test_upsert_clio_block_new_day_preserves_prior_days():
    content = ds.upsert_clio_block("", "Yesterday's summary", datetime(2026, 7, 8, 18, 30))
    new_content = ds.upsert_clio_block(content, "Today's summary", datetime(2026, 7, 9, 18, 30))
    assert "Yesterday's summary" in new_content
    assert "Today's summary" in new_content
    assert "<!-- Git Pulse Daily Summary 2026-07-08 Start -->" in new_content
    assert "<!-- Git Pulse Daily Summary 2026-07-09 Start -->" in new_content


def test_upsert_clio_block_rerun_same_day_replaces_only_that_day():
    content = ds.upsert_clio_block("", "Prior day summary", datetime(2026, 7, 8, 18, 0))
    content = ds.upsert_clio_block(content, "First run summary", datetime(2026, 7, 9, 18, 0))
    new_content = ds.upsert_clio_block(content, "Rerun summary", datetime(2026, 7, 9, 19, 0))
    assert "Prior day summary" in new_content
    assert "First run summary" not in new_content
    assert "Rerun summary" in new_content
    assert new_content.count("<!-- Git Pulse Daily Summary 2026-07-09 Start -->") == 1


# --- sync_to_clio ----------------------------------------------------------


@patch("rebalance.ingest.config.get_pulse_config")
def test_sync_to_clio_disabled_is_noop(mock_get_cfg):
    mock_get_cfg.return_value = {"git_pulse_clio_enabled": False}
    result = ds.sync_to_clio("summary", datetime(2026, 7, 9, 18, 0))
    assert result == {"enabled": False}


@patch("rebalance.ingest.config.get_pulse_config")
def test_sync_to_clio_missing_target_path(mock_get_cfg):
    mock_get_cfg.return_value = {"git_pulse_clio_enabled": True, "pulse_target_path": None}
    result = ds.sync_to_clio("summary", datetime(2026, 7, 9, 18, 0))
    assert result["enabled"] is True
    assert result["ok"] is False


@patch("rebalance.ingest.pulse._commit_and_push_if_changed")
@patch("rebalance.ingest.config.get_pulse_config")
def test_sync_to_clio_writes_and_commits(mock_get_cfg, mock_commit, tmp_path):
    (tmp_path / ".git").mkdir()
    mock_get_cfg.return_value = {
        "git_pulse_clio_enabled": True,
        "pulse_target_path": str(tmp_path),
        "git_pulse_clio_subdir": "CLIO",
        "git_pulse_clio_filename": "git-pulse-daily-log.md",
    }
    mock_commit.return_value = {"wrote_file": True, "committed": True, "pushed": True}

    result = ds.sync_to_clio("Today's summary", datetime(2026, 7, 9, 18, 0))

    assert result["ok"] is True
    assert result["file_rel"] == "CLIO/git-pulse-daily-log.md"
    mock_commit.assert_called_once()
    _, kwargs = mock_commit.call_args
    assert kwargs["file_rel"] == "CLIO/git-pulse-daily-log.md"
    assert "Today's summary" in kwargs["new_content"]
    assert kwargs["push"] is True


@patch("rebalance.ingest.config.get_pulse_config")
def test_sync_to_clio_dry_run_writes_nothing(mock_get_cfg, tmp_path):
    (tmp_path / ".git").mkdir()
    mock_get_cfg.return_value = {
        "git_pulse_clio_enabled": True,
        "pulse_target_path": str(tmp_path),
        "git_pulse_clio_subdir": "CLIO",
        "git_pulse_clio_filename": "git-pulse-daily-log.md",
    }

    result = ds.sync_to_clio("Summary", datetime(2026, 7, 9, 18, 0), dry_run=True)

    assert result["dry_run"] is True
    assert not (tmp_path / "CLIO" / "git-pulse-daily-log.md").exists()


# --- no-clobber guard (GH-129 follow-up #3) ----------------------------------


def test_extract_block_text_present():
    content = f"Prefix\n{ds.GIT_PULSE_MARKER_START}\nBlock body\n{ds.GIT_PULSE_MARKER_END}\nSuffix"
    assert ds._extract_block_text(content, ds.GIT_PULSE_MARKER_START, ds.GIT_PULSE_MARKER_END) == "\nBlock body\n"


def test_extract_block_text_absent():
    assert ds._extract_block_text("No markers here", ds.GIT_PULSE_MARKER_START, ds.GIT_PULSE_MARKER_END) is None


def test_extract_block_text_with_clio_date_scoped_markers():
    start, end = ds._clio_markers("2026-07-16")
    content = f"{start}\nBody\n{end}\n"
    assert ds._extract_block_text(content, start, end) == "\nBody\n"


def test_would_clobber_real_summary_true_for_real_block_and_fallback_new():
    existing = "\n## Heading\n*stamp*\n\nDid real work today.\n"
    assert ds._would_clobber_real_summary(existing, ds.FALLBACK_SUMMARY) is True


def test_would_clobber_real_summary_false_when_no_existing_block():
    assert ds._would_clobber_real_summary(None, ds.FALLBACK_SUMMARY) is False


def test_would_clobber_real_summary_false_when_existing_block_is_fallback():
    existing = f"\n## Heading\n*stamp*\n\n{ds.FALLBACK_SUMMARY}\n"
    assert ds._would_clobber_real_summary(existing, ds.FALLBACK_SUMMARY) is False


def test_would_clobber_real_summary_false_when_existing_block_empty():
    assert ds._would_clobber_real_summary("   \n", ds.FALLBACK_SUMMARY) is False


def test_would_clobber_real_summary_false_when_new_summary_is_real():
    existing = "\n## Heading\n*stamp*\n\nDid real work today.\n"
    assert ds._would_clobber_real_summary(existing, "Fresh new content") is False


# ===========================================================================
# 3. run() orchestration
# ===========================================================================


class TestRunLateGuard:
    def test_run_skips_late_catch_up(self, tmp_path, monkeypatch):
        target = tmp_path / "0. Today's Notes.md"
        target.write_text("manual\n", encoding="utf-8")
        monkeypatch.setattr(ds, "TODAY_FILE", target)
        monkeypatch.setattr(ds, "vault_ready", lambda: True)
        # Guard must fire BEFORE any signal collection / synthesis.
        monkeypatch.setattr(ds, "collect_pulse_activity", lambda: pytest.fail("collected on late run"))
        monkeypatch.setattr(ds, "synthesize_pulse", lambda a: pytest.fail("synthesized on late run"))
        monkeypatch.setattr(ds, "collect_git_pulse_activity", lambda: pytest.fail("git-pulse collected on late run"))

        rc = ds.run(now=datetime(2026, 7, 5, 2, 5))  # 02:05 next morning
        assert rc == 0
        assert target.read_text(encoding="utf-8") == "manual\n"  # untouched


class TestRunPulseHalf:
    def test_run_aborts_without_write_when_gemini_fails(self, tmp_path, monkeypatch):
        target = tmp_path / "0. Today's Notes.md"
        original = "# 0. Today's Notes\n\nmanual\n"
        target.write_text(original, encoding="utf-8")
        monkeypatch.setattr(ds, "TODAY_FILE", target)
        monkeypatch.setattr(ds, "vault_ready", lambda: True)
        monkeypatch.setattr(ds, "collect_pulse_activity", lambda: {"gh_commits": []})
        monkeypatch.setattr(ds, "synthesize_pulse", lambda a: None)  # Gemini unavailable/failed
        monkeypatch.setattr(ds, "collect_git_pulse_activity", lambda: (None, 1))  # view.sh absent — neutral

        rc = ds.run(now=datetime(2026, 7, 4, 18, 30))
        assert rc == 0
        assert target.read_text(encoding="utf-8") == original  # nothing written

    def test_run_writes_pulse_block_and_preserves_notes(self, tmp_path, monkeypatch):
        target = tmp_path / "0. Today's Notes.md"
        manual = "# 0. Today's Notes\n\n- manual note\n"
        target.write_text(manual, encoding="utf-8")
        monkeypatch.setattr(ds, "TODAY_FILE", target)
        monkeypatch.setattr(ds, "vault_ready", lambda: True)
        monkeypatch.setattr(ds, "collect_pulse_activity", lambda: {"gh_items": ["x"]})
        monkeypatch.setattr(ds, "synthesize_pulse", lambda a: "Shipped GH-112 today.")
        monkeypatch.setattr(ds, "collect_git_pulse_activity", lambda: (None, 1))

        rc = ds.run(now=datetime(2026, 7, 4, 19, 0))
        assert rc == 0
        out = target.read_text(encoding="utf-8")
        assert out.startswith(manual)  # human notes intact at the top
        assert out.count(ds.PULSE_MARKER_START) == 1
        assert "Shipped GH-112 today." in out

    def test_run_dry_run_does_not_write(self, tmp_path, monkeypatch, capsys):
        target = tmp_path / "0. Today's Notes.md"
        original = "manual\n"
        target.write_text(original, encoding="utf-8")
        monkeypatch.setattr(ds, "TODAY_FILE", target)
        monkeypatch.setattr(ds, "vault_ready", lambda: True)
        monkeypatch.setattr(ds, "collect_pulse_activity", lambda: {})
        monkeypatch.setattr(ds, "synthesize_pulse", lambda a: "preview text")
        monkeypatch.setattr(ds, "collect_git_pulse_activity", lambda: (None, 1))

        rc = ds.run(dry_run=True, now=datetime(2026, 7, 4, 20, 0))
        assert rc == 0
        assert target.read_text(encoding="utf-8") == original  # unchanged
        assert "preview text" in capsys.readouterr().out  # but shown


class TestRunGitPulseHalf:
    @patch("daily_synthesis.sync_to_clio")
    @patch("daily_synthesis.synthesize_git_pulse")
    @patch("daily_synthesis.collect_git_pulse_activity")
    @patch("rebalance.ingest.config.get_pulse_config")
    @patch("daily_synthesis.vault_ready")
    def test_run_writes_to_clio_when_vault_not_ready(
        self, mock_vault_ready, mock_get_cfg, mock_collect, mock_synthesize, mock_sync_clio
    ):
        mock_vault_ready.return_value = False
        mock_get_cfg.return_value = {"git_pulse_clio_enabled": True}
        mock_collect.return_value = ("tsv data", 0)
        mock_synthesize.return_value = "A summary"

        now = datetime(2026, 7, 9, 18, 30)
        code = ds.run(now=now)

        assert code == 0
        mock_synthesize.assert_called_once()
        mock_sync_clio.assert_called_once_with("A summary", now, dry_run=False)

    @patch("daily_synthesis.synthesize_git_pulse")
    @patch("daily_synthesis.collect_git_pulse_activity")
    @patch("rebalance.ingest.config.get_pulse_config")
    @patch("daily_synthesis.vault_ready")
    def test_run_skips_entirely_with_no_destination(self, mock_vault_ready, mock_get_cfg, mock_collect, mock_synthesize):
        mock_vault_ready.return_value = False
        mock_get_cfg.return_value = {"git_pulse_clio_enabled": False}

        code = ds.run(now=datetime(2026, 7, 9, 18, 30))

        assert code == 0
        mock_collect.assert_not_called()
        mock_synthesize.assert_not_called()

    def test_run_zero_row_rerun_does_not_clobber_existing_real_summary(self, tmp_path, monkeypatch, capsys):
        today_file = tmp_path / "0. Today's Notes.md"
        real_block = ds.build_git_pulse_block("Shipped GH-129 follow-up.", datetime(2026, 7, 16, 10, 0))
        original_content = f"Prefix text\n\n{real_block}"
        today_file.write_text(original_content, encoding="utf-8")

        monkeypatch.setattr(ds, "TODAY_FILE", today_file)
        monkeypatch.setattr(ds, "vault_ready", lambda: True)
        monkeypatch.setattr(ds, "collect_pulse_activity", lambda: {})
        monkeypatch.setattr(ds, "synthesize_pulse", lambda a: None)  # isolate the git-pulse half under test
        monkeypatch.setattr(ds, "collect_git_pulse_activity", lambda: ("header only", 0))
        monkeypatch.setattr(ds, "synthesize_git_pulse", lambda tsv: ds.FALLBACK_SUMMARY)
        with patch("rebalance.ingest.config.get_pulse_config", return_value={"git_pulse_clio_enabled": False}):
            code = ds.run(now=datetime(2026, 7, 16, 20, 0))

        assert code == 0
        assert today_file.read_text(encoding="utf-8") == original_content
        out = capsys.readouterr().out
        assert "SKIP: zero-row rerun would clobber an existing non-empty summary" in out

    def test_run_first_zero_row_write_of_day_still_writes_fallback(self, tmp_path, monkeypatch):
        """No existing block yet — the documented first-write-of-the-day behavior
        must be completely unaffected by the no-clobber guard."""
        today_file = tmp_path / "0. Today's Notes.md"
        today_file.write_text("Just some prefix text.\n", encoding="utf-8")

        monkeypatch.setattr(ds, "TODAY_FILE", today_file)
        monkeypatch.setattr(ds, "vault_ready", lambda: True)
        monkeypatch.setattr(ds, "collect_pulse_activity", lambda: {})
        monkeypatch.setattr(ds, "synthesize_pulse", lambda a: None)  # isolate the git-pulse half under test
        monkeypatch.setattr(ds, "collect_git_pulse_activity", lambda: ("header only", 0))
        monkeypatch.setattr(ds, "synthesize_git_pulse", lambda tsv: ds.FALLBACK_SUMMARY)
        with patch("rebalance.ingest.config.get_pulse_config", return_value={"git_pulse_clio_enabled": False}):
            code = ds.run(now=datetime(2026, 7, 16, 20, 0))

        assert code == 0
        new_content = today_file.read_text(encoding="utf-8")
        assert ds.GIT_PULSE_MARKER_START in new_content
        assert ds.FALLBACK_SUMMARY in new_content

    @patch("rebalance.ingest.pulse._commit_and_push_if_changed")
    def test_sync_to_clio_zero_row_rerun_does_not_clobber_existing_real_summary(self, mock_commit, tmp_path, capsys):
        (tmp_path / ".git").mkdir()
        now = datetime(2026, 7, 16, 20, 0)
        existing_content = ds.upsert_clio_block("", "Real work landed today.", now)
        clio_file = tmp_path / "CLIO" / "git-pulse-daily-log.md"
        clio_file.parent.mkdir(parents=True)
        clio_file.write_text(existing_content, encoding="utf-8")

        with patch(
            "rebalance.ingest.config.get_pulse_config",
            return_value={
                "git_pulse_clio_enabled": True,
                "pulse_target_path": str(tmp_path),
                "git_pulse_clio_subdir": "CLIO",
                "git_pulse_clio_filename": "git-pulse-daily-log.md",
            },
        ):
            result = ds.sync_to_clio(ds.FALLBACK_SUMMARY, now)

        assert result["ok"] is True
        assert result.get("skipped") == "would_clobber"
        mock_commit.assert_not_called()
        assert clio_file.read_text(encoding="utf-8") == existing_content
        out = capsys.readouterr().out
        assert "SKIP: zero-row rerun would clobber an existing non-empty summary" in out


# ===========================================================================
# 4. Ordering guarantee (GH-74) — the reason this module exists
# ===========================================================================


class TestOrdering:
    def test_pulse_block_lands_before_git_pulse_block_in_one_run(self, tmp_path, monkeypatch):
        """The whole point of the merge: no scheduler race can invert this —
        it's guaranteed by the order these two steps run in Python, in one
        read-modify-write of the vault file."""
        target = tmp_path / "0. Today's Notes.md"
        target.write_text("manual notes\n", encoding="utf-8")
        monkeypatch.setattr(ds, "TODAY_FILE", target)
        monkeypatch.setattr(ds, "vault_ready", lambda: True)
        monkeypatch.setattr(ds, "collect_pulse_activity", lambda: {"x": 1})
        monkeypatch.setattr(ds, "synthesize_pulse", lambda a: "Pulse summary text")
        monkeypatch.setattr(ds, "collect_git_pulse_activity", lambda: ("some\ttsv\trow\n", 0))
        monkeypatch.setattr(ds, "synthesize_git_pulse", lambda tsv: "Git pulse summary text")
        with patch("rebalance.ingest.config.get_pulse_config", return_value={"git_pulse_clio_enabled": False}):
            rc = ds.run(now=datetime(2026, 7, 4, 19, 0))

        assert rc == 0
        out = target.read_text(encoding="utf-8")
        assert out.index(ds.PULSE_MARKER_START) < out.index(ds.GIT_PULSE_MARKER_START), (
            "the pulse block must land above the git-pulse block — this is the ordering "
            "dependency GH-74 removed the two-launchd-jobs race around"
        )

    def test_rerun_preserves_order_even_when_only_git_pulse_changes(self, tmp_path, monkeypatch):
        """A rerun that only refreshes the git-pulse block must not reorder or
        duplicate the pulse block already in place."""
        target = tmp_path / "0. Today's Notes.md"
        pulse_block = ds.build_pulse_block("Yesterday's pulse text", datetime(2026, 7, 3, 18, 20))
        target.write_text(f"manual\n\n{pulse_block}", encoding="utf-8")
        monkeypatch.setattr(ds, "TODAY_FILE", target)
        monkeypatch.setattr(ds, "vault_ready", lambda: True)
        monkeypatch.setattr(ds, "collect_pulse_activity", lambda: {"x": 1})
        monkeypatch.setattr(ds, "synthesize_pulse", lambda a: None)  # no new pulse content this run
        monkeypatch.setattr(ds, "collect_git_pulse_activity", lambda: ("some\ttsv\trow\n", 0))
        monkeypatch.setattr(ds, "synthesize_git_pulse", lambda tsv: "Fresh git pulse text")
        with patch("rebalance.ingest.config.get_pulse_config", return_value={"git_pulse_clio_enabled": False}):
            rc = ds.run(now=datetime(2026, 7, 4, 19, 0))

        assert rc == 0
        out = target.read_text(encoding="utf-8")
        assert "Yesterday's pulse text" in out  # untouched pulse block preserved
        assert out.index(ds.PULSE_MARKER_START) < out.index(ds.GIT_PULSE_MARKER_START)
        assert "Fresh git pulse text" in out
