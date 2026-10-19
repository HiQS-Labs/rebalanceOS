# GH-336 verification summary

These are manual checks; no suite was added. The change is a skill and docs only.

| Check | Result |
|---|---|
| Plan QA, codex | **Approved** in round 2/2, attested against `f0c4ea0` (`qa/gh336-plan-qa-relay.md`) |
| Smoke, main path (disposable scratch repo) | SKILL.md 2.4e's new command `git diff --binary HEAD`, taken during a conflicted rebase (`UU c.bin`, `UU t.txt`). Both checks pass: the patch is non-empty and has no placeholder line. `rebase --abort` rc=0, then `git apply` onto a detached worktree at the `-head` backup, rc=0. **Content checks** print the expected (pre-abort disk) and actual (restored) full sha256, and all four match: the resolved unstaged text, the overwritten conflicted binary, the staged binary edit, and the rename target's content. **Property checks** all hold: the deletion (file absent), `chmod +x` (mode 755) and the rename source (gone). The stated limit is confirmed: staged `B` with `A` on disk restores `A`. `smoke-binary-backup.log` |
| Red control (old command `git diff HEAD`) | The placeholder check **FAILs**, so 2.4e as now written would stop before the abort. When the old flow is forced through: `git apply` rc=1 (`cannot apply binary patch to 'c.bin' without full index line`), and because apply is all-or-nothing, **every** edit is lost, text included. That is worse than #336 described. |
| Smoke, adjacent path (text-only conflict) | `--binary` patch: checks pass, apply rc=0, the resolved text is restored. The flag does not disturb the ordinary case. |
| Static gate | `.githooks/pre-push` static stages on `22962ba`: **PASS** (ruff, the format check and 5 ratchets). See `provenance.jsonl`. |

Script: `smoke-binary-backup.sh.txt` (run with `bash <file> <empty dir>`; it never touches a real pulse clone).
