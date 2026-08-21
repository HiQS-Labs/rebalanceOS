"""Recovery copy command validation tests (GH-110).

Pins:
- Every command referenced in user-facing recovery copy / empty states (e.g.
  `rebalance <cmd>`) must be a valid registered CLI command.
- Specifically, `rebalance refresh-index` was a dead command that must never return.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

from rebalance import cli, web

SRC_DIR = Path(__file__).resolve().parents[1] / "src" / "rebalance"

#: Pattern matching user-facing `rebalance <subcommand>` in markdown/HTML/code strings
_REBALANCE_CMD_PATTERN = re.compile(r"""(?:<code>|`|run:\s*|Run\s*)rebalance\s+([a-z0-9_-]+)""")


def _get_registered_cli_command_names() -> set[str]:
    names: set[str] = set()
    for cmd in cli.app.registered_commands:
        if cmd.name:
            names.add(cmd.name)
    for group in cli.app.registered_groups:
        if group.name:
            names.add(group.name)
    return names


class RecoveryCopyCommandsTests(unittest.TestCase):
    def test_registered_command_set_is_non_empty(self) -> None:
        cmds = _get_registered_cli_command_names()
        self.assertIn("refresh", cmds)
        self.assertIn("ingest", cmds)
        self.assertIn("config", cmds)
        self.assertNotIn("refresh-index", cmds)

    def test_no_product_file_references_dead_refresh_index_command(self) -> None:
        """THE PIN (GH-110): `rebalance refresh-index` is dead; code must say `rebalance refresh`."""
        offenders: list[str] = []
        for py_path in sorted(SRC_DIR.rglob("*.py")):
            content = py_path.read_text(encoding="utf-8")
            if "refresh-index" in content:
                for i, line in enumerate(content.splitlines(), 1):
                    if "refresh-index" in line:
                        rel = py_path.relative_to(SRC_DIR)
                        offenders.append(f"{rel}:{i}: {line.strip()}")
        self.assertEqual(
            offenders,
            [],
            "Found references to non-existent `rebalance refresh-index` command:\n" + "\n".join(offenders),
        )

    def test_web_empty_states_reference_valid_cli_commands(self) -> None:
        """All commands suggested in web.py empty states or messages must be registered."""
        valid_cmds = _get_registered_cli_command_names()
        web_src = Path(web.__file__).read_text(encoding="utf-8")

        for match in _REBALANCE_CMD_PATTERN.finditer(web_src):
            cmd_name = match.group(1)
            # Skip placeholders or non-command tokens if any
            if cmd_name in ("--help", "<command>"):
                continue
            with self.subTest(cmd=cmd_name):
                self.assertIn(
                    cmd_name,
                    valid_cmds,
                    f"web.py suggests non-existent CLI command `rebalance {cmd_name}`",
                )


if __name__ == "__main__":
    unittest.main()
