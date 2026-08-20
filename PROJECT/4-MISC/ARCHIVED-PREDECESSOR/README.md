# Archived predecessor documents — read as history, not as current work

Everything under this directory was authored in the **archived predecessor repo**,
[Hypercart-Dev-Tools/rebalance-OS](https://github.com/Hypercart-Dev-Tools/rebalance-OS)
(active 2026-03-28 → 2026-08-17), which this repo succeeded.

These documents were **not** carried into this repo when it was seeded on 2026-08-16, but the
links pointing at them were. They were restored under GH-88 so that internal navigation —
notably `ROADMAP.md`, a mandated prior-art check in `ROUTER.md` — resolves again.

## How to read anything in here

**A document's stated status describes the predecessor repo at archive time. It does not
describe this repo today.** A file whose frontmatter says `status: Active` was active *there*,
in July 2026. Treat every plan, phase, decision and date as historical unless you have
independently confirmed it against the current codebase.

The original lifecycle folder is preserved as the subdirectory name (`1-INBOX/`, `2-WORKING/`,
`3-COMPLETED/`, `4-MISC/`) because links between these documents depend on it and because it
records where each doc sat when the predecessor was archived. **It is provenance, not a claim
about current state.**

## Why these live in `4-MISC` and not in the lifecycle folders

`PROJECT/PDDA.md:35` defines `PROJECT/4-MISC` as "reference, stale, superseded, or abandoned
docs", and `PROJECT/PDDA.md:98` excludes it from the active scan. That is exactly the right
bucket for this material.

Restoring these files into `1-INBOX/`, `2-WORKING/` and `3-COMPLETED/` was tried first and
rejected on review: 36 of them assert an active-like `status:` in frontmatter, and this repo
runs a semantic index that retrieves *chunks* from the middle of a file — so a banner at the
top of a document is invisible at retrieval time. The directory path is carried on every chunk;
a header is not. The folder has to do the work.

## Git history

Restoring the files did not restore their history. Their commits live only in the predecessor
repo. `git log` here shows them created on the GH-88 restore date; use the archive for real
authorship and history.

## Links that leave this directory

Some references inside these documents point at
`https://github.com/Hypercart-Dev-Tools/rebalance-OS/...` rather than at a local file. Those
are second-order references — documents referenced *by* these archived documents. They were
deliberately not restored: doing so pulls in another wave of documents that reference yet more,
and it does not terminate.
