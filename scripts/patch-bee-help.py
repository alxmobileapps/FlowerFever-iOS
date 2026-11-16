"""Bees help with the goals more often.

A third of plain bee flights (outside the Flower Shower) are "helper" flights:
  1) first they break obstacles still on the board (ice, soil), goal or not;
  2) when no obstacle is left, the flower the bee lands on becomes a power-up that helps an unfinished goal
     (the asked-for power-up, a power-up for "make"/"combo" goals, or a striped flower of a goal colour).
The other flights work as before (they aim at goal flowers, ice and soil first).
Before: only a quarter of flights made a power-up, and only for "make a power-up" goals.
Runs after the .patch files (it edits the final www/index.html).
"""
from pathlib import Path

path = Path("www/index.html")
src = path.read_text()
if "BEE_HELP_PATCH" in src:
    print("bee help patch already applied"); raise SystemExit(0)

def rep(before, after):
    global src
    if src.count(before) != 1:
        raise RuntimeError("patch-bee-help: code changed: " + before[:70])
    src = src.replace(before, after)

rep("""function pickGift() {
  const open = goals.filter(g => g.k === "special" && g.left > 0);   // gifts only help with the hard "make a power-up" goals
  return open.length ? open[rnd(open.length)] : null;
}""", """function pickGift() {   // BEE_HELP_PATCH: a power-up for the goals still open
  const open = goals.filter(g => (g.k === "special" || g.k === "make" || g.k === "combo") && g.left > 0);
  if (open.length) return open[rnd(open.length)];
  const col = goals.filter(g => g.k === "color" && g.left > 0);
  if (col.length) return col[rnd(col.length)];
  return goals.some(g => g.k === "score" && g.left > 0) ? { k: "make" } : null;
}
function pickObstacle(fromR, fromC) {   // ice and soil still on the board
  const pool = [];
  eachPiece((p, r, c) => { if (p.frozen && !p.shield && !reserved.has(r * COLS + c) && !(r === fromR && c === fromC)) pool.push([r, c]); });
  for (let r = 0; r < ROWS; r++) for (let c = 0; c < COLS; c++) if (ground[r][c] > 0 && !reserved.has(r * COLS + c)) pool.push([r, c]);
  return pool.length ? pool[rnd(pool.length)] : null;
}""")
rep("""  const gift = !carry && !inShower && Math.random() < .25 ? pickGift() : null;
  const tg = (gift && giftTarget(gift, r, c)) || pickBeeTarget(r, c); if (!tg) return;""",
    """  const help = !carry && !inShower && Math.random() < 1 / 3, obst = help ? pickObstacle(r, c) : null;
  const gift = help && !obst ? pickGift() : null;
  const tg = obst || (gift && giftTarget(gift, r, c)) || pickBeeTarget(r, c); if (!tg) return;""")
path.write_text(src)
print("bee help patch applied")
