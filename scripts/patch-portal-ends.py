"""Split boards: a wind fan never takes a portal's cell.

From Level 100 a wind fan can sit on the board's edge by cutting away the corner cell of a row. On 13 split
boards (178, 322, 394, 478, 566, 586, 682, 694, 722, 766, 790, 974, 986) that corner was a portal's entrance
(bottom of the upper part) or exit (top of the lower part), so no flower could go through and that column of
the lower part never refilled. Now a fan skips those rows and takes its usual place in another row.
Runs after the .patch files (it edits the final www/index.html)."""
from pathlib import Path

path = Path("www/index.html")
src = path.read_text()
if "PORTAL_ENDS_PATCH" in src:
    print("portal ends patch already applied"); raise SystemExit(0)

def rep(before, after):
    global src
    if src.count(before) != 1:
        raise RuntimeError("patch-portal-ends: board building code changed; review before building: " + before[:70])
    src = src.replace(before, after)

rep("""if (a === 0) { if (g[r][0] !== "X" || !empty(r - 1, 0) || !solid(r, 1, b)) continue;""",
    """if (a === 0) { if (g[r][0] !== "X" || !empty(r - 1, 0) || !solid(r, 1, b) || portalEnd(r, 0)) continue;""")
rep("""if (b === ENVW - 1) { if (g[r][b] !== "X" || !empty(r + 1, b) || !solid(r, a, b - 1)) continue;""",
    """if (b === ENVW - 1) { if (g[r][b] !== "X" || !empty(r + 1, b) || !solid(r, a, b - 1) || portalEnd(r, b)) continue;""")
rep("""      const segR = (r, a) => {""",
    """      // PORTAL_ENDS_PATCH: a portal's entrance or exit cell is never cut away for a fan
      const portalEnd = (r, c) => (L.portals || []).some(([a1, b1, c1, d1]) => (a1 === r && b1 === c) || (c1 === r && d1 === c));
      const segR = (r, a) => {""")
path.write_text(src)
print("Fans keep clear of portal cells")
