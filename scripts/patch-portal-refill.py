"""Portals keep feeding the board during the Flower Shower.

In the shower, power-ups stay parked in place while flowers fall past them. A parked power-up
on a portal's exit cell (bottom of the upper part) or entry cell (top of the lower part) used to
block the portal, so the lower part kept empty cells until that power-up went off.
Now the portal takes the lowest flower above parked power-ups and drops it into the first free
cell below parked power-ups. Outside the shower nothing changes.
Runs after the .patch files (it edits the final www/index.html).
"""
from pathlib import Path

path = Path("www/index.html")
src = path.read_text()
before = """  portals.forEach(([er, ec, nr, nc], i) => {
    const src = grid[er][ec];
    if (!src || src.frozen || staysInShower(src) || grid[nr][nc] || mask[nr][nc] !== 1 || ground[nr][nc] > 0) return;
    grid[er][ec] = null; grid[nr][nc] = src; src.r = nr; src.c = nc; src.px = nc; src.py = nr - 1 - teleK[i]++ * 1.15;"""
after = """  portals.forEach(([er, ec, nr, nc], i) => {
    // in the shower, look past parked power-ups on both sides of the portal
    let sr = er; while (sr > 0 && staysInShower(grid[sr][ec]) && !blockedCell(sr, ec)) sr--;
    let dr = nr; while (dr < ROWS - 1 && staysInShower(grid[dr][nc]) && !blockedCell(dr, nc)) dr++;
    if (blockedCell(sr, ec) || blockedCell(dr, nc)) return;
    const src = grid[sr][ec];
    if (!src || src.frozen || staysInShower(src) || grid[dr][nc]) return;
    grid[sr][ec] = null; grid[dr][nc] = src; src.r = dr; src.c = nc; src.px = nc; src.py = nr - 1 - teleK[i]++ * 1.15;"""
if src.count(before) == 1:
    path.write_text(src.replace(before, after))
elif src.count(after) != 1:
    raise RuntimeError("Portal code changed; check patch-portal-refill.py")
print("portal refill patch applied")
