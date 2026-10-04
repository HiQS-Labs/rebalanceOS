"""Regression tests for the release-ledger dump reader (multi-line INSERT values).

The ledger tool writes string values verbatim, so a value holding a newline spans several dump
lines. The reader used to match each statement with a single-line regex, which made
`releases_app.py check --rebuild` refuse the committed dump. These tests pin the multi-line fix
and the guard that keeps one match from running past a statement's end.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("releases_app_dump_parse_test", ROOT / "utils/py/releases_app.py")
assert _spec is not None and _spec.loader is not None
releases_app = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(releases_app)

HEADER = "-- releases-app canonical dump\n-- generation: 1\n-- table: t\n"


def _row(*values: str | None) -> str:
    return "INSERT INTO t(a, b) VALUES(%s);" % ", ".join(releases_app._sql_str(v) for v in values)


def test_multiline_string_value_parses():
    text = HEADER + _row("x", "line one\nline two\n\nline four") + "\n" + _row("y", None) + "\n"
    rows = releases_app.parse_dump(text)["t"]
    assert rows == [
        {"a": "x", "b": "line one\nline two\n\nline four"},
        {"a": "y", "b": None},
    ]


def test_row_terminator_inside_multiline_value_does_not_end_the_row():
    tricky = "first line ends like a statement);\nINSERT INTO t(a, b) VALUES('not', 'a row');\nlast"
    text = HEADER + _row("x", tricky) + "\n" + _row("y", "plain") + "\n"
    rows = releases_app.parse_dump(text)["t"]
    assert rows == [{"a": "x", "b": tricky}, {"a": "y", "b": "plain"}]


def test_quotes_and_escapes_survive_round_trip():
    value = "it's 'quoted'\nand ''doubled''"
    rows = releases_app.parse_dump(HEADER + _row("x", value) + "\n")["t"]
    assert rows == [{"a": "x", "b": value}]


def test_broken_row_is_not_merged_into_the_next_one():
    # The first statement is missing its closing quote. A greedy multi-line match must not glue
    # it to the following row; the reader refuses instead of inventing a row.
    text = HEADER + "INSERT INTO t(a, b) VALUES('x', 'unterminated);\n" + _row("y", "z") + "\n"
    with pytest.raises(SystemExit):
        releases_app.parse_dump(text)


def test_committed_ledger_dump_parses_completely():
    text = (ROOT / "releases.sql").read_text(encoding="utf-8")
    tables = releases_app.parse_dump(text)
    parsed = sum(len(rows) for rows in tables.values())
    statements = sum(1 for line in text.split("\n") if line.startswith("INSERT INTO "))
    assert parsed == statements
