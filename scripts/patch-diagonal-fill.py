"""Candy Crush-style refill: new flowers only drop in from the top of the board.

Before, a column blocked by a rock, soil or ice got brand-new flowers spawned right under the blocker,
so flowers seemed to appear from the middle of the board. Now the empty cells under a blocker are filled
by flowers sliding in diagonally from the next column (diagStep), and those columns refill from the top.
A hole that nothing can fall or slide into stays empty (like Candy Crush) until a blocker next to it breaks.
Safety net: if the board has no move even after a shuffle (too few flowers), the empty holes are filled once.
Runs after the .patch files (it edits the final www/index.html).
"""
from pathlib import Path

path = Path("www/index.html")
src = path.read_text()
if "DIAGONAL_FILL_PATCH" in src:
    print("diagonal fill patch already applied"); raise SystemExit(0)

def rep(before, after):
    global src
    if src.count(before) != 1:
        raise RuntimeError("patch-diagonal-fill: code changed: " + before[:70])
    src = src.replace(before, after)

rep("""      if (!entryAt.has(top * COLS + c) && !noSpawn.has(top * COLS + c)) {""",
    """      // DIAGONAL_FILL_PATCH: no new flowers under a rock/soil/ice inside the board; those holes fill by diagonal slides
      if (!entryAt.has(top * COLS + c) && !noSpawn.has(top * COLS + c) && (forceFill || top === 0 || mask[top - 1][c] !== 1)) {""")
rep("""      const p = grid[r - 1][sc]; if (!p || p.frozen || staysInShower(p) || used.has(p.id)) continue;""",
    """      const p = grid[r - 1][sc]; if (!p || p.frozen || staysInShower(p) || used.has(p.id)) continue;
      if (!blockedCell(r, sc) && !grid[r][sc]) continue;   // it can still fall straight down, let it""")
rep("""    if (diagStep()) { any = true; await settle(); continue; }
    if (!v) break;""",
    """    if (diagStep()) { any = true; await settle(); continue; }
    if (!v) break;   // like Candy Crush: a hole nothing can fall or slide into stays empty until a blocker next to it breaks""")
# safety net: if even a shuffle can't give a move (too few flowers left), fill the empty holes once and shuffle again
rep("""  sfx("swap"); await settle();
  hint = null; lastInput = T();   // clue restarts from the new layout
}""", """  sfx("swap"); await settle();
  if (!findMove() && !shuffleBoard.refill) {
    forceFill = true; const f = verticalPass(); forceFill = false;
    if (f) { await settle(); shuffleBoard.refill = true; try { if (!findMove()) await shuffleBoard(); } finally { shuffleBoard.refill = false; } }
  }
  hint = null; lastInput = T();   // clue restarts from the new layout
}""")
rep("""function verticalPass() {""", """let forceFill = false;
function verticalPass() {""")
path.write_text(src)
print("diagonal fill patch applied")
