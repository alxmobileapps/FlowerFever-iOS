#!/usr/bin/env python3
"""Showcase boards: 6 hand-made board designs (towers, lantern, gem, blanket, corner vault, funnel with chutes),
placed on 1 level in every 20 from level 60 to 1000 (60, 80, ... 200, then 220 ... 1000).
Each garden (50 levels) changes them: mirrored left/right, and obstacles swapped
(ice -> beehives, soft soil -> swamp, stones -> hard soil ...), so the same shape never looks the same.
Before level 151 (where swamp is introduced) swamp becomes hard soil; beehives only from level 201.
Moves = the level's own moves, raised if the board has a lot to clear. Goals come from what is on the board.
X flower, . no space, S soft soil, H hard soil, W swamp, R garden stone, I frozen flower, E ice block, B beehive."""
import json, pathlib, sys

D = [
    {"rows": [".X.X.X.", ".XSXSX.", "RXSXSXR", "XXHXHXX", "RXHXHXR", "XXHXHXX", "HXHXHXH", "XXXXXXX", "WEWEWEW"], "bombs": [[0, 1], [0, 3], [0, 5]]},
    {"rows": ["..XX.XX..", ".RSSXSSR.", "XXHIXIHXX", ".HXXXXXH.", ".XXXXXXX.", "..XXHXX..", "..XXHXX..", "...XXX..."], "bombs": [[3, 4]]},
    {"rows": ["..XX.XX..", ".XHEXEHX.", "RIXXXXXIR", "XIXXXXXIX", "XHHXXXHHX", "RHHEXEHHR", ".XHEXEHX.", "..XX.XX.."], "bombs": [[3, 4]]},
    {"rows": ["XXXXXXXXX", "XXXXXXXXX", "XXHXXXHXX", "XHXHXHXHX", "HXHXWXHXH", "XHXWXWXHX", "HXWXWXWXH", "XWXWXWXWX", "WXWXXXWXW"], "bombs": []},
    {"rows": ["XXXXXXX..", "XXXXXXX..", "XXXXXXXIH", "XXXXXXXIH", "XXHXXXHXH", ".XHHWHHXH", ".XHWXWHXH", ".XHHWHHXH", ".XXXXXXXX"], "bombs": [[4, 4]]},
    {"rows": ["XXXXXXXXX", "XXXXXXXXX", "XXXXXXXXX", "XXXXXXXXX", ".XXXXXXX.", "...XXX...", ".........", "XXXXXXXXX", "IXRXIXRXI", "HXHIXIHXH"], "bombs": [],
     "portals": [[3, 0, 7, 0], [4, 1, 7, 1], [4, 2, 7, 2], [5, 3, 7, 3], [5, 4, 7, 4], [5, 5, 7, 5], [4, 6, 7, 6], [4, 7, 7, 7], [3, 8, 7, 8]]},
]

code = """
{ // SHOWCASE_LEVELS_PATCH: 6 hand-made boards on every 20th level from 60 (patch-showcase-levels.py)
  const D = %s;
  // obstacle swaps per garden (index = garden number %% 5); "" = keep
  const SWAP = [{}, { I: "B", E: "E" }, { S: "W" }, { R: "H", E: "I" }, { I: "B", S: "W", R: "S" }];
  const HARDISH = ["Hard", "Expert"], easyPick = [0, 1, 2, 5], hardPick = [3, 4, 0, 5];
  let ke = 0, kh = 0;
  for (let n = 60; n <= LEVELS.length; n += 20) {
    const LV = LEVELS[n - 1]; if (!LV) continue;
    const hard = HARDISH.includes(LV.diff), d = D[hard ? hardPick[kh++ %% 4] : easyPick[ke++ %% 4]];
    const gi = Math.floor((n - 1) / 50), mir = gi %% 2 === 1, sw = n > 200 ? SWAP[gi %% 5] : {};
    const W = d.rows[0].length, H = d.rows.length, top = Math.floor((ENVH - H) / 2), left = Math.floor((ENVW - W) / 2);
    const mc = c => mir ? W - 1 - c : c;
    let rows = d.rows.map(r => [...(mir ? [...r].reverse().join("") : r)].map(ch => sw[ch] || ch).map(ch => ch === "W" && n < 151 ? "H" : ch).join(""));
    LV.layout = Array.from({ length: ENVH }, (_, r) => { const row = rows[r - top]; return row ? ".".repeat(left) + row + ".".repeat(ENVW - left - W) : ".".repeat(ENVW); });
    LV.rows = rows; LV.nudge = [(ENVW - W) %% 2 ? .5 : 0, (ENVH - H) %% 2 ? .5 : 0]; LV.fans = []; LV.shape = 0;
    LV.portals = (d.portals || []).map(([a, b, c, e]) => [a + top, mc(b) + left, c + top, mc(e) + left]);
    LV.starterAt = d.bombs.map(([r, c]) => ["bomb", r + top, mc(c) + left]);
    const f = LV.layout.join(""), cnt = re => (f.match(re) || []).length;
    const soil = cnt(/[SH]/g), ice = cnt(/[IE]/g), sw2 = cnt(/W/g), hv = cnt(/B/g);
    const goals = [];
    if (soil) goals.push({ k: "ground", n: soil });
    if (ice) goals.push({ k: "ice", n: ice });
    if (sw2) goals.push({ k: "swamp", n: sw2 });
    if (hv) goals.push({ k: "hive", n: hv, big: false });
    const hits = cnt(/S/g) + 2 * cnt(/H/g) + 3 * sw2 + ice + 2 * hv;
    LV.moves = Math.max(LV.moves, 18 + Math.ceil(hits * .3));
    if (goals.length < 2) goals.push({ k: "color", c: LV.colors[n %% LV.colors.length], n: Math.round(LV.moves * .7) });
    LV.goals = goals; LV.stars = [LV.moves * 60, LV.moves * 220, LV.moves * 420];
    if (LV.intro === "hive" && !hv) LV.intro = null;
    LV.showcase = true;
  }
}
""" % json.dumps(D, separators=(",", ":"))

p = pathlib.Path(__file__).resolve().parent.parent / "www" / "index.html"
s = p.read_text(encoding="utf-8")
if "SHOWCASE_LEVELS_PATCH" in s: print("showcase levels already added"); sys.exit(0)
anchor = "function buildLayout(L) {"
if s.count(anchor) != 1: sys.exit("patch-showcase-levels: anchor not found")
s = s.replace(anchor, code.strip() + "\n" + anchor, 1)
p.write_text(s, encoding="utf-8")
print("showcase boards on every 20th level from 60")
