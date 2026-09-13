"""Small shared redactors for text that may cross a trust boundary."""

from __future__ import annotations

import re


KEY_SHAPED_SECRET_RE = re.compile(
    r"sk-ant-[A-Za-z0-9\-_]{20,}"
    r"|sk-[A-Za-z0-9]{20,}"
    r"|ghp_[A-Za-z0-9]{35,}"
    r"|gho_[A-Za-z0-9]{35,}"
    r"|github_pat_[A-Za-z0-9_]{20,}"
    r"|AIza[A-Za-z0-9\-_]{35,}"
    r"|AKIA[A-Za-z0-9]{16}"
    r"|xoxb-[0-9]+-[A-Za-z0-9\-]+"
    r"|xoxp-[0-9]+-[A-Za-z0-9\-]+"
    r"|ya29\.[A-Za-z0-9\-_]{20,}"
)


def redact_key_shaped_secrets(text: str) -> str:
    """Replace recognized bare credential shapes with a fixed placeholder."""
    return KEY_SHAPED_SECRET_RE.sub("[REDACTED]", text)
