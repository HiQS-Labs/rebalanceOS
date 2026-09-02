#!/usr/bin/env python3
"""GH-144 Phase 0 — CI-side D2 exact-once union check from spike-job junit
artifacts. Run as: python3 check_ci_union.py <artifacts-dir> <run_id>
Downloads artifacts if the dir is empty (needs gh api auth), then compares each
candidate's lane union against c0's root+hiqs executed set."""
import subprocess, sys, zipfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_s1 import parse_junit

def fetch(run_id: str, dest: Path) -> None:
    names = subprocess.run(["gh","api",f"repos/HiQS-Labs/rebalanceOS/actions/runs/{run_id}/artifacts?per_page=50",
                            "--jq",".artifacts[] | \"\\(.id) \\(.name)\""], capture_output=True, text=True).stdout
    for line in names.splitlines():
        aid, name = line.split(" ", 1)
        d = dest / name
        d.mkdir(parents=True, exist_ok=True)
        z = d / "a.zip"
        subprocess.run(["gh","api",f"repos/HiQS-Labs/rebalanceOS/actions/artifacts/{aid}/zip"], stdout=open(z,"wb"), check=True)
        with zipfile.ZipFile(z) as f: f.extractall(d)
        z.unlink()

def load(p: Path) -> dict:
    return parse_junit(p)["outcomes"]

def main() -> None:
    dest = Path(sys.argv[1]); run_id = sys.argv[2]
    if not any(dest.iterdir()):
        fetch(run_id, dest)
    for py in ("3.12","3.13"):
        b = {**load(dest/f"c0-junit-{py}/junit-root.xml"), **load(dest/f"c0-junit-{py}/junit-hiqs.xml")}
        h2 = load(dest/f"c2-hiqs-junit-{py}/junit-hiqs.xml")
        print(f"py{py}: base(root+hiqs)={len(b)}")
        for label, parts in (
            ("C2", [dest/f"c2-root-junit-{py}/junit-root.xml", h2]),
            ("C3", [dest/f"c3-root-junit-{py}/junit-root.xml", dest/f"c3-seam-junit-{py}/junit-seam.xml", h2]),
            ("C4-n4", [dest/f"c4-xdist4-junit-{py}/junit-root.xml", h2]),
        ):
            maps = [load(p) if isinstance(p, Path) else p for p in parts]
            u = {}
            for m in maps: u.update(m)
            dup = len(u) - sum(len(m) for m in maps) + len(maps[0])  # not used; explicit pairwise below
            pairs = 0
            seen = set()
            for m in maps:
                pairs += len(seen & set(m)); seen |= set(m)
            print(f"  {label:<6} union={len(u)} missing={len(set(b)-set(u))} added={len(set(u)-set(b))} dup={pairs}")

if __name__ == "__main__":
    main()
