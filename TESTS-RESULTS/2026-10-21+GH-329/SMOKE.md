# GH-329 + GH-348 smoke receipt (manual check, disposable clone)

Run 2026-10-21 PDT in `<GH Repos>/rebalanceOS-gh329-retire-roadmap-md-2026-10-21-gate`, a `git clone --no-local`
of the task branch at 8e8b697. All writes landed in that disposable clone only.

Verdict: PASS. Main path (park → rate → move → list) works from the DB, a re-park is refused without a
duplicate row, sync no-ops, reconcile flags a closed issue moved back to In progress, and both red controls fail as intended.

Notes:
- The first reconcile run in the gate clone skipped every row ("no matching owned issue URL"): a `--no-local`
  clone's `origin` is a filesystem path, so the owned-repo identity cannot resolve. With `origin` set to
  HiQS-Labs/rebalanceOS, the same command flags #316. This is a harness artifact, not a product defect; real clones
  have a GitHub origin.
- `rc=` lines that print `0` after a `refused:` line come from zsh's `PIPESTATUS` (empty); the row count (1) is the evidence.

## Main and adjacent paths
### smoke @ 8e8b697 in disposable clone (-gate)
## main path: park open issue #346, rate it, move to In progress, list
added roadmap entry rmi-01M5GXTQ6CXJ3QWN0KV4M1CRHQ for GH-346
add rc=0
rated GH-346 40/30/50/80
rate rc=0
updated GH-346
move rc=0
rmi-01M5GXTQ6CXJ3QWN0KV4M1CRHQ  GH-346  In progress            #50  cre=-      calc=200      🆕 docs(front-door): README drift
## adjacent: re-run sync (must skip); park the same issue again (must not duplicate)
roadmap sync: skipped — releases-mode repo (the DB is canonical; sync only mirrors ROADMAP.md in legacy mode, and would delete rows parked by `roadmap add`)
sync rc=0
refused: rule=roadmap-duplicate: issue https://github.com/HiQS-Labs/rebalanceOS/issues/346 is already parked in the roadmap
second add rc=0
1
## adjacent: closed #316 moved back to In progress -> reconcile dry-run flags it
updated GH-316
move rc=0
warn: rule=roadmap-issue-identity: GH-23 has no matching owned issue URL; skipped (fix with `releases roadmap update --issue-num 23 --issue-url <url>`)
warn: rule=roadmap-issue-identity: GH-120 has no matching owned issue URL; skipped (fix with `releases roadmap update --issue-num 120 --issue-url <url>`)
warn: rule=roadmap-issue-identity: GH-126 has no matching owned issue URL; skipped (fix with `releases roadmap update --issue-num 126 --issue-url <url>`)
warn: rule=roadmap-issue-identity: GH-144 has no matching owned issue URL; skipped (fix with `releases roadmap update --issue-num 144 --issue-url <url>`)
warn: rule=roadmap-issue-identity: GH-174 has no matching owned issue URL; skipped (fix with `releases roadmap update --issue-num 174 --issue-url <url>`)
warn: rule=roadmap-issue-identity: GH-177 has no matching owned issue URL; skipped (fix with `releases roadmap update --issue-num 177 --issue-url <url>`)
warn: rule=roadmap-issue-identity: GH-202 has no matching owned issue URL; skipped (fix with `releases roadmap update --issue-num 202 --issue-url <url>`)
warn: rule=roadmap-issue-identity: GH-210 has no matching owned issue URL; skipped (fix with `releases roadmap update --issue-num 210 --issue-url <url>`)
warn: rule=roadmap-issue-identity: GH-230 has no matching owned issue URL; skipped (fix with `releases roadmap update --issue-num 230 --issue-url <url>`)
warn: rule=roadmap-issue-identity: GH-232 has no matching owned issue URL; skipped (fix with `releases roadmap update --issue-num 232 --issue-url <url>`)
warn: rule=roadmap-issue-identity: GH-233 has no matching owned issue URL; skipped (fix with `releases roadmap update --issue-num 233 --issue-url <url>`)
warn: rule=roadmap-issue-identity: GH-255 has no matching owned issue URL; skipped (fix with `releases roadmap update --issue-num 255 --issue-url <url>`)
warn: rule=roadmap-issue-identity: GH-282 has no matching owned issue URL; skipped (fix with `releases roadmap update --issue-num 282 --issue-url <url>`)
warn: rule=roadmap-issue-identity: GH-300 has no matching owned issue URL; skipped (fix with `releases roadmap update --issue-num 300 --issue-url <url>`)
warn: rule=roadmap-issue-identity: GH-310 has no matching owned issue URL; skipped (fix with `releases roadmap update --issue-num 310 --issue-url <url>`)
warn: rule=roadmap-issue-identity: GH-312 has no matching owned issue URL; skipped (fix with `releases roadmap update --issue-num 312 --issue-url <url>`)
warn: rule=roadmap-issue-identity: GH-316 has no matching owned issue URL; skipped (fix with `releases roadmap update --issue-num 316 --issue-url <url>`)
warn: rule=roadmap-issue-identity: GH-329 has no matching owned issue URL; skipped (fix with `releases roadmap update --issue-num 329 --issue-url <url>`)
warn: rule=roadmap-issue-identity: GH-346 has no matching owned issue URL; skipped (fix with `releases roadmap update --issue-num 346 --issue-url <url>`)
warn: rule=roadmap-issue-identity: GH-348 has no matching owned issue URL; skipped (fix with `releases roadmap update --issue-num 348 --issue-url <url>`)
roadmap reconcile-state: no changes; nothing written
reconcile rc=0
## adjacent (rerun with origin=HiQS-Labs; the --no-local clone's origin was a filesystem path, so identity could not resolve): reconcile dry-run
would move GH-316: In progress -> Completed
roadmap reconcile-state: dry-run; nothing written (pass --apply to write)
reconcile rc=

## Red controls (separate gate run, same commit)
## red control: coverage flags the GH-348 doc once its rows are gone
ERROR [pdda-check-roadmap-coverage] PROJECT/2-WORKING/GH-348-RETIRE-ROADMAP-MD.md:1 active working doc has no pointer in releases.db (PROJECT/2-WORKING/GH-348-RETIRE-ROADMAP-MD.md) — park it with releases roadmap add, or set roadmap_exempt: true
SUMMARY [pdda-check-roadmap-coverage] errors=10 warns=0 info=32
## red control: recreating ROADMAP.md fails the retirement test
3 failed, 1 passed in 5.97s

## Final-QA r1 red controls (gate clone at 75f869f)

- Working-doc loop: delete the GH-310 plan's only ledger row → `tests/test_roadmap_retired.py` fails with
  `AssertionError: roadmap-coverage errors rose to 10 (baseline 9 at GH-348)`. The row-count test also fails (146 < 147).
- Inbox loop: delete the row for `PROJECT/1-INBOX/GH-1-SUSTAINED-ACTIVITY-AUTO-PROMOTE.md` →
  `ERROR … captured GH issue doc is not parked in releases.db (PROJECT/1-INBOX/GH-1-…)`, `SUMMARY … errors=11`.
