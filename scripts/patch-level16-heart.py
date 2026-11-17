#!/usr/bin/env python3
"""Level 16 (the soft-soil intro level): heart-shaped board (9 wide x 8 tall) with soft soil filling the
   lower heart and 5 Bouquets waiting on the board. X = flower, S = soft soil, . = no space. 22 moves."""
import pathlib, sys

p = pathlib.Path(__file__).resolve().parent.parent / "www" / "index.html"
s = p.read_text(encoding="utf-8")

HEART = [
    ".XXX.XXX.",
    "XXXXXXXXX",
    "XXSSXSSXX",
    "XSSXSXSSX",
    ".SXSXSXS.",
    "..SXSXS..",
    "...SXS...",
    "....S....",
]
code = """
{ // Level 16: heart board with soft soil and 5 Bouquets (patch-level16-heart.py)
  const LV = LEVELS[15], heart = %s;
  const top = Math.floor((ENVH - heart.length) / 2), blank = ".".repeat(ENVW);
  LV.layout = Array.from({ length: ENVH }, (_, r) => heart[r - top] || blank);
  LV.rows = heart; LV.nudge = [0, 0]; LV.portals = []; LV.fans = []; LV.starterAt = [[3, 1], [3, 4], [3, 7], [5, 2], [5, 6]].map(([r, c]) => ["wrap", r + top - 1, c]);
  LV.shape = 0; LV.moves = %d; LV.stars = [LV.moves * 60, LV.moves * 220, LV.moves * 420];
  LV.goals = [{ k: "ground", n: %d }, { k: "color", c: 0, n: %d }];
  LV.intro = "soil";
}
""" % (repr(HEART).replace("'", '"'), 22, sum(r.count("S") for r in HEART), 20)

anchor = "function buildLayout(L) {"
if s.count(anchor) != 1:
    sys.exit("patch-level16-heart: anchor not found")
s = s.replace(anchor, code.strip() + "\n" + anchor, 1)
p.write_text(s, encoding="utf-8")
print("level 16: heart board,", sum(r.count("S") for r in HEART), "soft soil")
