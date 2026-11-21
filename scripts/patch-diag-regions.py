"""Split boards: a flower only slides diagonally inside its own board part. Two parts that touch only at a
corner (side by side, one lower than the other) are different boards, so a flower from the 1st part must not
slide straight into the 2nd one. Runs after patch-diagonal-fill.py."""
from pathlib import Path
path = Path("www/index.html"); src = path.read_text()
if "DIAG_REGIONS_PATCH" in src: print("diagonal slide regions already applied"); raise SystemExit(0)
a = "      const p = grid[r - 1][sc]; if (!p || p.frozen || staysInShower(p) || used.has(p.id)) continue;"
if src.count(a) != 1: raise RuntimeError("patch-diag-regions: diagStep changed")
src = src.replace(a, a + "\n      if (regions.regionOf && regions.regionOf(r, c) !== regions.regionOf(r - 1, sc)) continue;   // DIAG_REGIONS_PATCH: never into another board part")
path.write_text(src); print("diagonal slides stay inside their own board part")
