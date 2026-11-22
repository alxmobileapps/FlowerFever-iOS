#!/usr/bin/env python3
"""New board shapes (from the player's reference boards): dome, castle (2 versions), heart with bee pockets,
ring vault, twin hives.  No board shape is used on more than 60 levels: every shape over 60 gives its extra
levels (picked at random, same picks every build) to these 6 new boards, spread evenly.
Levels 1-60, every 20th showcase level, Level 16 and levels that introduce something new are never touched.
Big star candy = big beehive (G), keys = bees (starter power-ups), locks = soft soil (S).
Each garden mirrors the board left/right and swaps obstacles, so a board never looks exactly the same.
Before Level 111 big beehives become hard soil; before Level 151 swamp becomes hard soil.
X flower, . no space, S soft soil, H hard soil, W swamp, R garden stone, I frozen flower, E ice block, G big beehive (2 x 2)."""
import json, pathlib, sys

D = [
    # 1 dome: round top, the lower half full of soil with holes
    {"rows": ["..XXXXX..", ".XXXXXXX.", "XXXXXXXXX", "XXXXXXXXX", "SSXSXSXSS", "HSSSXSSSH", "HS.SXS.SH", "XS.SXS.SX", "XXXXXXXXX"], "st": []},
    # 2 castle: full top, narrowing towers, a gap at the bottom middle (soft soil "locks")
    {"rows": ["XXXXXXXXX", "XXXXXXXXX", "XSXSXSXSX", ".XXXXXXX.", "..XSXSX..", "..XXXXX..", "..XSXSX..", ".XXX.XXX.", "XXX...XXX"], "st": [["bee", 0, 4]]},
    # 3 heart: soft soil fills the lower right, two little bee pockets in the bottom corners
    {"rows": [".XXX.XXX.", "XXXXXXXXX", "XXXXXXXXX", "XXXXXSSSX", ".XXXSSSX.", "..XXSSS..", "...XSS...", "....S....", "XX.....XX", "XX.....XX"],
     "st": [["bee", 9, 0], ["bee", 9, 8]], "portals": [[3, 0, 8, 0], [4, 1, 8, 1], [4, 7, 8, 7], [3, 8, 8, 8]]},
    # 4 castle (second version): stones and hard soil instead of soft soil
    {"rows": ["XXXXXXXXX", "XHXXXXXHX", "XXXRXRXXX", ".HXXXXXH.", "..XXHXX..", "..XHXHX..", "..XXXXX..", ".XHX.XHX.", "XXX...XXX"], "st": [["bomb", 0, 4]]},
    # 5 ring vault: a ring of flowers around soft soil, stones and a few flowers in the middle, 3 holes at the bottom
    {"rows": ["XXXXXXXXX", "XHSSSSSHX", "XSSSSSSSX", "XSSXXXSSX", "XSSRRRSSX", "XSSXXXSSX", "XSSSSSSSX", "XHSSSSSHX", "XXX...XXX"], "st": []},
    # 6 twin hives: a flower row on top, hard soil blocks in the top corners, soft soil down the middle, big beehives in the bottom corners
    {"rows": ["XXXXXXXXX", "HHHXXXHHH", "HHHXSXHHH", ".XXXSXXX.", "..XXSXX..", "..XXXXX..", ".XXXXXXX.", "GGXXXXXGG", "GGXXXXXGG"], "st": []},
]

code = """
{ // NEW_SHAPES_PATCH: 6 new boards, and no board shape on more than 60 levels (patch-new-shapes.py)
  const D = %s, CAP = 60;
  const SWAP = [{}, { S: "I" }, { H: "W" }, { S: "E" }, { R: "H", S: "W" }];
  const busy = LV => LV.n <= 60 || LV.showcase || LV.n === 16 || LV.intro || LV.diff === "Tutorial";
  const used = {}; LEVELS.forEach(LV => { if (!LV.showcase && LV.n !== 16) used[LV.shape] = (used[LV.shape] || 0) + 1; });
  const rnd = mulberry(424242), picks = [];
  Object.keys(used).forEach(sh => {
    const over = used[sh] - CAP; if (over <= 0) return;
    const pool = LEVELS.filter(LV => String(LV.shape) === sh && !busy(LV));
    for (let i = pool.length - 1; i > 0; i--) { const j = Math.floor(rnd() * (i + 1)); [pool[i], pool[j]] = [pool[j], pool[i]]; }
    picks.push(...pool.slice(0, over));
  });
  picks.sort((a, b) => a.n - b.n);
  const per = D.map(() => 0); let k = Math.floor(rnd() * D.length);
  for (const LV of picks) {
    let di = k %% D.length; for (let t = 0; t < D.length && per[di] >= CAP; t++) di = (di + 1) %% D.length;
    if (per[di] >= CAP) break; per[di]++; k = di + 1;
    const d = D[di], n = LV.n;
    const gi = Math.floor((n - 1) / 50), mir = gi %% 2 === 1, sw = n > 200 ? SWAP[gi %% 5] : {};
    const W = d.rows[0].length, H = d.rows.length, top = Math.floor((ENVH - H) / 2), left = Math.floor((ENVW - W) / 2);
    const mc = c => mir ? W - 1 - c : c;
    const rows = d.rows.map(r => [...(mir ? [...r].reverse().join("") : r)].map(ch => sw[ch] || ch)
      .map(ch => ch === "W" && n < 151 ? "H" : ch === "G" && n < 111 ? "H" : ch).join(""));
    LV.layout = Array.from({ length: ENVH }, (_, r) => { const row = rows[r - top]; return row ? ".".repeat(left) + row + ".".repeat(ENVW - left - W) : ".".repeat(ENVW); });
    LV.rows = rows; LV.nudge = [(ENVW - W) %% 2 ? .5 : 0, (ENVH - H) %% 2 ? .5 : 0]; LV.fans = []; LV.chutes = []; LV.teleport = false;
    LV.portals = (d.portals || []).map(([a, b, c, e]) => [a + top, mc(b) + left, c + top, mc(e) + left]);
    LV.starterAt = d.st.map(([t, r, c]) => [t, r + top, mc(c) + left]);
    const f = LV.layout.join(""), cnt = re => (f.match(re) || []).length;
    const soil = cnt(/[SH]/g), ice = cnt(/[IE]/g), sw2 = cnt(/W/g), big = cnt(/G/g) / 4, goals = [];
    if (soil) goals.push({ k: "ground", n: soil });
    if (ice) goals.push({ k: "ice", n: ice });
    if (sw2) goals.push({ k: "swamp", n: sw2 });
    if (big) goals.push({ k: "hive", n: big, big: true });
    const hits = cnt(/S/g) + 2 * cnt(/H/g) + 3 * sw2 + ice + 6 * big;
    LV.moves = Math.max(LV.moves, 18 + Math.ceil(hits * .3));
    if (goals.length < 2) goals.push({ k: "color", c: LV.colors[n %% LV.colors.length], n: Math.round(LV.moves * .7) });
    LV.goals = goals; LV.stars = [LV.moves * 60, LV.moves * 220, LV.moves * 420];
    LV.shape = 100 + di; LV.newShape = di + 1;
  }
}
""" % json.dumps(D, separators=(",", ":"))

p = pathlib.Path(__file__).resolve().parent.parent / "www" / "index.html"
s = p.read_text(encoding="utf-8")
if "NEW_SHAPES_PATCH" in s: print("new shapes already added"); sys.exit(0)
if "SHOWCASE_LEVELS_PATCH" not in s: sys.exit("patch-new-shapes: run after patch-showcase-levels")
anchor = "function buildLayout(L) {"
if s.count(anchor) != 1: sys.exit("patch-new-shapes: anchor not found")
s = s.replace(anchor, code.strip() + "\n" + anchor, 1)
p.write_text(s, encoding="utf-8")
print("6 new board shapes; no shape on more than 60 levels")
