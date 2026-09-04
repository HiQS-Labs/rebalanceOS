"""Property-based and invariant test battery for src/rebalance/ingest/md_parser.py.

Uses Hypothesis to verify parser stability, crash-freedom, and invariants over
arbitrary markdown notes and frontmatter payloads.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml
from hypothesis import given, strategies as st

from rebalance.ingest.md_parser import (
    ParsedChunk,
    ParsedNote,
    _title_from_body,
    chunk_by_headings,
    extract_frontmatter,
    extract_tags,
    extract_wikilinks,
    parse_note,
)


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

safe_text = st.text(
    alphabet=st.characters(blacklist_categories=("Cs",)),  # exclude surrogate pairs
    max_size=2000,
)

simple_words = st.text(
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")),
    min_size=1,
    max_size=30,
)


# ---------------------------------------------------------------------------
# 1. extract_frontmatter properties
# ---------------------------------------------------------------------------

@given(raw_text=st.text())
def test_extract_frontmatter_crash_free(raw_text: str) -> None:
    """extract_frontmatter must never raise on arbitrary unicode input."""
    fm, body = extract_frontmatter(raw_text)
    assert isinstance(fm, dict)
    assert isinstance(body, str)


@given(
    data=st.dictionaries(
        keys=simple_words,
        values=st.one_of(st.text(), st.integers(), st.booleans(), st.lists(st.text())),
        max_size=10,
    ),
    body_content=safe_text,
)
def test_extract_frontmatter_roundtrip_valid_yaml(data: dict[str, Any], body_content: str) -> None:
    """extract_frontmatter cleanly recovers a valid YAML dictionary."""
    yaml_text = yaml.safe_dump(data)
    raw = f"---\n{yaml_text}---\n{body_content}"
    fm, body = extract_frontmatter(raw)
    assert isinstance(fm, dict)
    assert body == body_content
    for k, v in data.items():
        assert fm.get(k) == v


@given(
    non_dict_data=st.one_of(
        st.lists(st.text(min_size=1), min_size=1, max_size=5),
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.text(min_size=1),
    ),
    body_content=safe_text,
)
def test_extract_frontmatter_non_dict_payload_fallback(non_dict_data: Any, body_content: str) -> None:
    """Non-dict YAML frontmatter (e.g. top-level list or scalar) safely falls back to {}."""
    yaml_text = yaml.safe_dump(non_dict_data)
    raw = f"---\n{yaml_text}---\n{body_content}"
    fm, body = extract_frontmatter(raw)
    assert fm == {}
    assert body == body_content


# ---------------------------------------------------------------------------
# 2. extract_tags properties
# ---------------------------------------------------------------------------

@given(text=st.text())
def test_extract_tags_crash_free(text: str) -> None:
    """extract_tags must never raise on arbitrary text and return unique tags."""
    tags = extract_tags(text)
    assert isinstance(tags, list)
    assert len(tags) == len(set(tags))  # unique tags


@given(
    tag_name=st.from_regex(r"^[a-zA-Z][a-zA-Z0-9_/-]{1,20}$", fullmatch=True),
    prefix=st.text(alphabet=" \t\n"),
)
def test_extract_tags_valid_pattern(tag_name: str, prefix: str) -> None:
    """Valid #tag patterns outside code fences are extracted correctly."""
    text = f"{prefix}#{tag_name} some trailing text"
    tags = extract_tags(text)
    assert tag_name in tags


@given(
    tag_name=st.from_regex(r"^[a-zA-Z][a-zA-Z0-9_/-]{1,20}$", fullmatch=True),
    code_body=safe_text,
)
def test_extract_tags_ignores_tags_in_code_blocks(tag_name: str, code_body: str) -> None:
    """Tags inside triple backtick code blocks must be ignored."""
    fenced_code = f"```\n#{tag_name}\n{code_body}\n```"
    tags = extract_tags(fenced_code)
    assert tag_name not in tags


# ---------------------------------------------------------------------------
# 3. extract_wikilinks properties
# ---------------------------------------------------------------------------

@given(text=st.text())
def test_extract_wikilinks_crash_free(text: str) -> None:
    """extract_wikilinks must never raise on arbitrary text."""
    links = extract_wikilinks(text)
    assert isinstance(links, list)
    for target, link_type in links:
        assert isinstance(target, str)
        assert link_type in ("wikilink", "embed")


@given(
    target=st.text(alphabet=st.characters(blacklist_characters="]\n|", blacklist_categories=("Cs",)), min_size=1),
    alias=st.text(alphabet=st.characters(blacklist_characters="]\n", blacklist_categories=("Cs",))),
)
def test_extract_wikilinks_target_and_alias(target: str, alias: str) -> None:
    """Wikilinks with alias [[Target|Alias]] must extract the target without the alias."""
    raw = f"[[{target}|{alias}]]" if alias else f"[[{target}]]"
    links = extract_wikilinks(raw)
    expected_target = target.strip()
    assert (expected_target, "wikilink") in links


@given(
    target=st.text(alphabet=st.characters(blacklist_characters="]\n|", blacklist_categories=("Cs",)), min_size=1),
)
def test_extract_wikilinks_embed(target: str) -> None:
    """Embeds ![[Target]] must be typed as 'embed' and not duplicated as wikilink."""
    raw = f"![[{target}]]"
    links = extract_wikilinks(raw)
    expected_target = target.strip()
    assert (expected_target, "embed") in links
    assert (expected_target, "wikilink") not in links


# ---------------------------------------------------------------------------
# 4. chunk_by_headings invariants
# ---------------------------------------------------------------------------

@given(body=st.text())
def test_chunk_by_headings_invariants(body: str) -> None:
    """chunk_by_headings produces well-formed ParsedChunk sequences."""
    chunks = chunk_by_headings(body)
    assert len(chunks) >= 1
    # Sequential chunk indices starting at 0
    indices = [c.chunk_index for c in chunks]
    assert indices == list(range(len(chunks)))

    for chunk in chunks:
        assert isinstance(chunk.body, str)
        assert chunk.char_count == len(chunk.body)
        if chunk.heading_level is not None:
            assert 1 <= chunk.heading_level <= 6
            assert isinstance(chunk.heading, str)


non_heading_text = st.text(
    alphabet=st.characters(blacklist_characters="#", blacklist_categories=("Cs",)),
    max_size=500,
)


@given(
    h1=simple_words,
    h2=simple_words,
    p1=non_heading_text,
    p2=non_heading_text,
)
def test_chunk_by_headings_structure(h1: str, h2: str, p1: str, p2: str) -> None:
    """Multi-heading markdown parses into distinct chunks with correct levels."""
    content = f"# {h1}\n{p1}\n\n## {h2}\n{p2}"
    chunks = chunk_by_headings(content)
    assert len(chunks) == 2
    assert chunks[0].heading == h1
    assert chunks[0].heading_level == 1
    assert chunks[1].heading == h2
    assert chunks[1].heading_level == 2



# ---------------------------------------------------------------------------
# 5. _title_from_body & parse_note end-to-end
# ---------------------------------------------------------------------------

@given(
    title=simple_words,
    body=safe_text,
)
def test_title_from_body_h1_priority(title: str, body: str) -> None:
    """An explicit H1 heading is always prioritized for note title."""
    text = f"# {title}\n\n{body}"
    resolved = _title_from_body(text, Path("some_note.md"))
    assert resolved == title


def test_parse_note_full_lifecycle(tmp_path: Path) -> None:
    """End-to-end parse_note verification on a synthetic note."""
    vault = tmp_path / "vault"
    vault.mkdir()
    note_file = vault / "Engineering Note.md"
    note_file.write_text(
        "---\ntype: project\ntags: [arch, core]\n---\n# Engineering Note\n\nDiscussion about [[Architecture|Arch]] and ![[diagram.png]].\n\n#deep-work\n\n## Next Steps\n- Action items\n",
        encoding="utf-8",
    )

    parsed = parse_note(note_file, vault)
    assert isinstance(parsed, ParsedNote)
    assert parsed.rel_path == "Engineering Note.md"
    assert parsed.title == "Engineering Note"
    assert parsed.frontmatter.get("type") == "project"
    assert "arch" in parsed.tags
    assert "core" in parsed.tags
    assert "deep-work" in parsed.tags
    assert ("Architecture", "wikilink") in parsed.wikilinks
    assert ("diagram.png", "embed") in parsed.wikilinks
    assert len(parsed.chunks) == 2
    assert len(parsed.content_hash) == 64  # valid sha256 hex
