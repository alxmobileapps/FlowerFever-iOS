#!/usr/bin/env python3
"""Goal and obstacle rules (Nov 2026).

1. Soft + hard soil: on boards that have soil but less than 10% of their spaces, soft soil is added
   until it is 10-15% (and the soil goal covers all of it). Boards at 10% or more are not touched.
   Hard soil is never added (boards that already have more than 5 keep them).
2. Power-up goals: "swap two power-ups together" at most 1, "build / make and pop power-ups" at most 3.
3. Beehive goal (one per level at most): a board with the big 2x2 hive always gets "Free the big
   beehive"; about half the boards with only small hives get "Break a beehive".
4. New obstacle: the swamp (1x1, "W" in layouts). It blocks its space like hard soil and takes
   3 hits (a match right next to it, a power-up or a bee = 1 hit each). When it breaks, a Rainbow
   flower appears in its place. From level 151, on 1 board in 3, 1-3 swamps; every other one of
   those boards also has "Break all swamps" as a goal.
Levels with a hand-made layout (like level 16) are left as they are."""
import pathlib, sys

p = pathlib.Path(__file__).resolve().parent.parent / "www" / "index.html"
s = p.read_text(encoding="utf-8")

def swap(old, new):
    global s
    if s.count(old) != 1:
        sys.exit(f"patch-goals-swamp: expected 1 of {old[:70]!r}, found {s.count(old)}")
    s = s.replace(old, new)

# ---- level rules, applied once when a level's board is first laid out ----
swap("  return (L.layout = out);\n}", r"""  tuneLevel(L, out);
  return (L.layout = out);
}
function tuneLevel(L, out) {   // goal + obstacle rules (patch-goals-swamp.py)
  const R = mulberry(L.n * 977 + 13), g = out.map(r => [...r]);
  const cnt = re => g.reduce((a, row) => a + row.filter(ch => re.test(ch)).length, 0);
  const tiles = cnt(/[^.]/);
  const fanRows = new Set((L.fans || []).map(f => f.r));
  const starter = new Set((L.starterAt || []).map(([, r, c]) => r * ENVW + c));
  const portalCells = new Set(); (L.portals || []).forEach(q => { portalCells.add(q[0] * ENVW + q[1]); portalCells.add(q[2] * ENVW + q[3]); });
  const top = []; for (let c = 0; c < ENVW; c++) { let r = 0; while (r < ENVH && g[r][c] === ".") r++; top[c] = r; }
  const free = (r, c) => g[r] && g[r][c] === "X" && r > top[c] + 1 && !fanRows.has(r) && !starter.has(r * ENVW + c) && !portalCells.has(r * ENVW + c);
  const near = (r, c, set) => [[1, 0], [-1, 0], [0, 1], [0, -1]].some(([y, x]) => g[r + y] && set.includes(g[r + y][c + x]));
  // 1) soft + hard soil reaches 10-15% of the spaces on boards that already have some soil
  const soil = cnt(/[SH]/);
  if (soil > 0 && soil < Math.ceil(tiles * .10)) {
    let add = Math.max(0, Math.min(Math.floor(tiles * .15), Math.ceil(tiles * (.10 + R() * .05))) - soil);
    for (let pass = 0; pass < (L.teleport ? 1 : 2) && add > 0; pass++) {   // split boards: only next to soil already there
      const cand = [];
      for (let r = 0; r < ENVH; r++) for (let c = 0; c < ENVW; c++) if (free(r, c) && (pass || near(r, c, "SH"))) cand.push([r, c]);
      while (add > 0 && cand.length) { const [r, c] = cand.splice(Math.floor(R() * cand.length), 1)[0]; if (g[r][c] === "X") { g[r][c] = "S"; add--; } }
    }
    const n = cnt(/[SH]/), gg = L.goals.find(x => x.k === "ground");
    if (gg) gg.n = n; else if (L.goals.length < 4) L.goals.push({ k: "ground", n });
  }
  // 2) power-up goals stay small
  L.goals.forEach(x => { if (x.k === "combo") x.n = Math.min(1, x.n); if (x.k === "make" || x.k === "special") x.n = Math.min(3, x.n); });
  // 3) one beehive goal at most
  const big = cnt(/G/) > 0, small = cnt(/B/) > 0;
  if (!L.goals.some(x => x.k === "hive") && L.goals.length < 4 && (big || (small && L.n % 2 === 0))) L.goals.push({ k: "hive", n: 1, big });
  // 4) swamps from level 151, on 1 board in 3
  if (L.n >= 151 && (L.n - 151) % 3 === 0 && !L.teleport) {
    const want = 1 + Math.floor(R() * 3), cand = [];
    for (let r = 0; r < ENVH; r++) for (let c = 0; c < ENVW; c++) if (free(r, c)) cand.push([r, c]);
    let placed = 0;
    while (placed < want && cand.length) { const [r, c] = cand.splice(Math.floor(R() * cand.length), 1)[0]; if (g[r][c] === "X" && !near(r, c, "W")) { g[r][c] = "W"; placed++; } }
    if (placed && (L.n - 151) % 6 === 0 && L.goals.length < 4) L.goals.push({ k: "swamp", n: placed });
    if (placed && L.n === 151) L.intro = "swamp";
  }
  for (let r = 0; r < ENVH; r++) out[r] = g[r].join("");
}""")

# ---- the swamp on the board: 3 hits, then a Rainbow flower ----
swap('ch === "H" || ch === "B" ? 2 : 0', 'ch === "H" || ch === "B" ? 2 : ch === "W" ? 3 : 0')
swap('"SHEBG".includes(ch)', '"SHEBGW".includes(ch)')
swap("const hp = ground[r] && ground[r][c]; if (!hp) return;",
     'const hp = ground[r] && ground[r][c]; if (!hp) return;\n  const wasSwamp = groundType[r][c] === "W"; if (wasSwamp) d = 1;')
swap('for (const g of goals) if (g.k === (wasIce ? "ice" : "ground") && g.left > 0) { g.left--; flyIcon(g, r, c); break; }',
     'for (const g of goals) if (g.k === (wasIce ? "ice" : wasSwamp ? "swamp" : "ground") && g.left > 0) { g.left--; flyIcon(g, r, c); break; }\n'
     '    if (wasSwamp && grid[r] && !grid[r][c]) { const np = newPiece(-1, "bomb"); np.r = r; np.c = c; np.px = c; np.py = r; np.pop = T(); np.shield = true; grid[r][c] = np; sparkleAt(r, c, 22); sfx("create"); }')
swap("    else ctx.drawImage(soilSprite(ty, ty === \"H\" && hp === 1, Math.round(S * DPR)), c * S + sh, r * S, S, S);",
     "    else if (ty === \"W\") ctx.drawImage(swampSprite(hp, Math.round(S * DPR)), c * S + sh, r * S, S, S);\n"
     "    else ctx.drawImage(soilSprite(ty, ty === \"H\" && hp === 1, Math.round(S * DPR)), c * S + sh, r * S, S, S);")
swap("function soilSprite(type, cracked, S) {", r"""const swampCache = {};
function swampSprite(hp, S) {
  const k = hp + ":" + S; if (swampCache[k]) return swampCache[k];
  const cv = document.createElement("canvas"); cv.width = cv.height = S; const g = cv.getContext("2d"); g.translate(S / 2, S / 2); g.scale(S, S); drawSwamp(g, hp);
  return (swampCache[k] = cv);
}
function drawSwamp(g, hp) {   // a murky pond with a lily pad; it dries and cracks as it is hit (3 = full, 1 = one hit left)
  hp = Math.max(1, Math.min(3, hp || 3));
  rrect(g, -.45, -.45, .9, .9, .18);
  const cols = hp === 3 ? [[0, "#5fa58c"], [.55, "#2f6f5c"], [1, "#1d4a3c"]] : hp === 2 ? [[0, "#78a982"], [.55, "#4a7a5a"], [1, "#30553d"]] : [[0, "#a0a877"], [.55, "#76804e"], [1, "#4f5632"]];
  g.fillStyle = rg2(g, -.12, -.18, 0, 0, .72, cols); g.fill();
  g.lineWidth = .03; g.strokeStyle = "rgba(10,40,30,.55)"; g.stroke();
  g.save(); g.clip();
  g.strokeStyle = "rgba(220,255,240,.35)"; g.lineWidth = .025;
  [[-.18, -.2, .16], [.16, .1, .12], [-.12, .22, .1]].forEach(([x, y, rr], i) => { if (i < hp) { g.beginPath(); g.ellipse(x, y, rr, rr * .45, 0, 0, TAU); g.stroke(); } });
  g.fillStyle = hp === 1 ? "#8fa04a" : "#5dbb4a"; g.beginPath(); g.moveTo(.22, -.08); g.arc(.22, -.08, .15, .35, TAU - .35); g.closePath(); g.fill();
  g.strokeStyle = "rgba(20,70,20,.6)"; g.lineWidth = .015; g.beginPath(); g.moveTo(.22, -.08); g.lineTo(.33, -.13); g.stroke();
  g.strokeStyle = "#3e6a2a"; g.lineWidth = .03; g.lineCap = "round";
  [[-.34, .4, -.38, .02], [-.27, .4, -.24, .1]].forEach(([x1, y1, x2, y2]) => { g.beginPath(); g.moveTo(x1, y1); g.quadraticCurveTo(x1 - .02, (y1 + y2) / 2, x2, y2); g.stroke(); });
  g.fillStyle = "#7a4a22"; [[-.38, .02], [-.24, .1]].forEach(([x, y]) => { g.beginPath(); g.ellipse(x, y + .05, .025, .06, 0, 0, TAU); g.fill(); });
  if (hp < 3) {   // cracks
    g.strokeStyle = "rgba(40,30,10,.75)"; g.lineWidth = .028;
    const cr = hp === 2 ? [[[-.05, -.42], [.02, -.18], [-.06, .02]]] : [[[-.05, -.42], [.02, -.18], [-.06, .02], [.05, .2]], [[.42, .15], [.2, .2], [.08, .36]], [[-.42, -.1], [-.22, -.04], [-.12, .1]]];
    cr.forEach(pts => { g.beginPath(); pts.forEach(([x, y], i) => i ? g.lineTo(x, y) : g.moveTo(x, y)); g.stroke(); });
  }
  g.restore();
}
function soilSprite(type, cracked, S) {""")

# ---- beehive goal counting ----
swap('  popups.push({ x: cx + .5, y: cy + .5, text: h.big ? "8 bees!" : "Bees!"',
     '  if (!inShower) for (const g of goals) if (g.k === "hive" && g.left > 0 && (!g.big || h.big)) { g.left--; flyIcon(g, cy, cx); break; }\n'
     '  popups.push({ x: cx + .5, y: cy + .5, text: h.big ? "8 bees!" : "Bees!"')

# ---- goal icons, names and help ----
swap("ICONS.rock = iconURL(",
     'ICONS.swamp = iconURL((g, S) => { g.translate(S / 2, S / 2); g.scale(S, S); drawSwamp(g, 3); });\n'
     'ICONS.hive = hiveSprite(0, 96).toDataURL();\n'
     "ICONS.rock = iconURL(")
swap('g.k === "ground" ? ICONS.ground : ""', 'g.k === "ground" ? ICONS.ground : g.k === "hive" ? ICONS.hive : g.k === "swamp" ? ICONS.swamp : ""')
swap('g.k === "combo" ? "power-up combos" : g.t}', 'g.k === "combo" ? "power-up combos" : g.k === "hive" ? "beehive" : g.k === "swamp" ? "swamp" : g.t}')
swap('  else if (g.k === "ice") { icon = `<img alt="" src="${g.icon}">`; title = `Thaw all',
     '  else if (g.k === "hive") { icon = `<img alt="" src="${g.icon}">`; title = g.big ? `Free the big beehive` : `Break a beehive`;\n'
     '    body = g.big ? `Make <strong>2 matches against each of the 4 sides</strong> of the big hive. When all sides are done, 8 busy bees fly out and the goal is complete.` : `Make matches right next to a small beehive, or hit it with a power-up, until it breaks and the bees fly out. Any small hive counts.`; }\n'
     '  else if (g.k === "swamp") { icon = `<img alt="" src="${g.icon}">`; title = `Break all ${g.n} swamp${g.n > 1 ? "s" : ""}`;\n'
     '    body = `A swamp blocks its space and takes <strong>3 hits</strong>: a match right next to it, a power-up or a bee. When it breaks, a <strong>Rainbow flower</strong> appears in its place!`; }\n'
     '  else if (g.k === "ice") { icon = `<img alt="" src="${g.icon}">`; title = `Thaw all')
swap('    : g.k === "combo" ? `swap two power-ups together',
     '    : g.k === "hive" ? (g.big ? "free the big beehive" : "break a beehive")\n'
     '    : g.k === "swamp" ? `break all ${g.n} swamp${g.n > 1 ? "s" : ""}`\n'
     '    : g.k === "combo" ? `swap two power-ups together')
swap('g.k === "make" ? "power-ups" : g.k === "combo" ? (g.left > 1 ? "combos" : "combo")',
     'g.k === "make" ? "power-ups" : g.k === "hive" ? "beehive" : g.k === "swamp" ? (g.left > 1 ? "swamps" : "swamp") : g.k === "combo" ? (g.left > 1 ? "combos" : "combo")')
swap('  shape: () => `<div class="legend"><img alt="" src="${ICONS.shape}">',
     '  swamp: () => `<div class="legend"><img alt="" src="${ICONS.swamp}"><div><b>Swamps</b> block a space and take 3 hits: a match right next to one, a power-up or a bee. When a swamp breaks, a <b>Rainbow flower</b> appears in its place!</div></div>`,\n'
     '  shape: () => `<div class="legend"><img alt="" src="${ICONS.shape}">')

p.write_text(s, encoding="utf-8")
print("goals: soil 10-15%, power-up caps, beehive goal; swamp obstacle from level 151")
