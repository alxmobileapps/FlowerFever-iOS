"""After a reshuffle, at least one next move helps an unfinished goal.

The shuffle already guaranteed some move; now it keeps shuffling (up to its usual limit) until a move exists
that makes progress: clears a flower of a goal colour, breaks ice or soil next to the match, makes a power-up
for a power-up goal (4+ in a row or an L/T/square), or swaps two power-ups for a combo goal.
Runs after the .patch files (it edits the final www/index.html).
"""
from pathlib import Path

path = Path("www/index.html")
src = path.read_text()
if "SHUFFLE_GOAL_PATCH" in src:
    print("shuffle goal patch already applied"); raise SystemExit(0)

def rep(before, after):
    global src
    if src.count(before) != 1:
        raise RuntimeError("patch-shuffle-goal: code changed: " + before[:70])
    src = src.replace(before, after)

rep("""async function shuffleBoard() {""", """// SHUFFLE_GOAL_PATCH: is there a move that helps a goal that isn't finished yet?
function goalMove() {
  const open = goals.filter(g => g.left > 0); if (!open.length) return true;
  const want = new Set(open.filter(g => g.k === "color").map(g => g.c));
  const iceG = open.some(g => g.k === "ice"), soilG = open.some(g => g.k === "ground");
  const makeG = open.some(g => g.k === "special" || g.k === "make"), comboG = open.some(g => g.k === "combo"), scoreG = open.some(g => g.k === "score");
  const near = (r, c, test) => test(r, c) || [[0, 1], [0, -1], [1, 0], [-1, 0]].some(([dr, dc]) => inB(r + dr, c + dc) && test(r + dr, c + dc));
  const iceAt = (r, c) => !!(grid[r][c] && grid[r][c].frozen), soilAt = (r, c) => ground[r][c] > 0;
  for (let r = 0; r < ROWS; r++) for (let c = 0; c < COLS; c++) for (const [dr, dc] of [[0, 1], [1, 0]]) {
    const r2 = r + dr, c2 = c + dc; if (!inB(r2, c2)) continue;
    const a = grid[r][c], b = grid[r2][c2]; if (!a || !b || a.frozen || b.frozen) continue;
    if (a.type === "bomb" || b.type === "bomb" || (isSpecial(a) && isSpecial(b))) return true;   // power-up swaps help every goal
    grid[r][c] = b; grid[r2][c2] = a; const gs = findGroups(); grid[r][c] = a; grid[r2][c2] = b;
    for (const g of gs) {
      if (scoreG) return true;
      if (makeG && (g.cells.length >= 4 || g.squares.length)) return true;
      for (const [y, x] of g.cells) {
        const p = (y === r && x === c) ? b : (y === r2 && x === c2) ? a : grid[y][x];
        if (p && want.has(p.color)) return true;
        if (iceG && near(y, x, iceAt)) return true;
        if (soilG && near(y, x, soilAt)) return true;
      }
    }
    if (comboG && isSpecial(a) && isSpecial(b)) return true;
  }
  return false;
}
async function shuffleBoard() {""")
rep("""    if (!findGroups().length && findMove()) break;
  }""", """    if (!findGroups().length && findMove() && (tries > 260 || goalMove())) break;
  }""")
path.write_text(src)
print("shuffle goal patch applied")
