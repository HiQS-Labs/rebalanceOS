#!/usr/bin/env python3
"""GH-144 Phase 0 — CI-side D2 exact-once union check from spike-job junit
artifacts. Run as: python3 check_ci_union.py <artifacts-dir> <run_id>
Downloads artifacts if the dir is absent or empty (needs gh api auth), then
compares each candidate's lane union against c0's root+hiqs executed set."""

import subprocess
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_s1 import parse_junit

REPO_API = "repos/HiQS-Labs/rebalanceOS/actions"


def gh_api_text(endpoint: str, *args: str) -> str:
    proc = subprocess.run(["gh", "api", f"{REPO_API}/{endpoint}", *args], capture_output=True, text=True)
    if proc.returncode != 0:
        sys.exit(
            f"gh api {endpoint} failed (rc={proc.returncode}): "
            f"{proc.stderr.strip() or 'no stderr — is gh authenticated?'}"
        )
    return proc.stdout


def fetch(run_id: str, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    lines = [
        line
        for line in gh_api_text(
            f"runs/{run_id}/artifacts?per_page=50", "--jq", '.artifacts[] | "\\(.id) \\(.name)"'
        ).splitlines()
        if line.strip()
    ]
    if not lines:
        sys.exit(
            f"no artifacts listed for run {run_id} — wrong run id, or the artifacts expired (default 90-day retention)?"
        )
    for line in lines:
        aid, name = line.split(" ", 1)
        d = dest / name
        d.mkdir(parents=True, exist_ok=True)
        z = d / "a.zip"
        with open(z, "wb") as out:
            proc = subprocess.run(["gh", "api", f"{REPO_API}/artifacts/{aid}/zip"], stdout=out, stderr=subprocess.PIPE)
        if proc.returncode != 0 or z.stat().st_size == 0:
            sys.exit(f"download failed for artifact {name} (id={aid}): {proc.stderr.decode(errors='replace').strip()}")
        with zipfile.ZipFile(z) as f:
            f.extractall(d)
        z.unlink()


def load(p: Path) -> dict:
    if not p.exists():
        sys.exit(f"expected junit artifact missing: {p} — fetch step incomplete?")
    return parse_junit(p)["outcomes"]


def main() -> None:
    dest = Path(sys.argv[1])
    run_id = sys.argv[2]
    if not dest.exists() or not any(dest.iterdir()):
        fetch(run_id, dest)
    for py in ("3.12", "3.13"):
        b = {**load(dest / f"c0-junit-{py}/junit-root.xml"), **load(dest / f"c0-junit-{py}/junit-hiqs.xml")}
        h2 = load(dest / f"c2-hiqs-junit-{py}/junit-hiqs.xml")
        print(f"py{py}: base(root+hiqs)={len(b)}")
        for label, parts in (
            ("C2", [dest / f"c2-root-junit-{py}/junit-root.xml", h2]),
            ("C3", [dest / f"c3-root-junit-{py}/junit-root.xml", dest / f"c3-seam-junit-{py}/junit-seam.xml", h2]),
            ("C4-n4", [dest / f"c4-xdist4-junit-{py}/junit-root.xml", h2]),
        ):
            maps = [load(p) if isinstance(p, Path) else p for p in parts]
            u: dict[str, str] = {}
            dup = 0
            seen: set[str] = set()
            for m in maps:
                dup += len(seen & set(m))
                seen |= set(m)
                u.update(m)
            print(f"  {label:<6} union={len(u)} missing={len(set(b) - set(u))} added={len(set(u) - set(b))} dup={dup}")


if __name__ == "__main__":
    main()
