"""Bees go for every obstacle goal that is still open: swamps (swamp goal), beehives (hive goal) and ice blocks
(ice goal), not only soil. Before, a bee only chose soil when a soil goal was open, so swamps were never targeted."""
from pathlib import Path
path = Path("www/index.html"); src = path.read_text()
if "BEE_SWAMP_PATCH" in src: print("bee swamp already applied"); raise SystemExit(0)
a = '  if (goals.some(g => g.k === "ground" && g.left > 0)) for (let r = 0; r < ROWS; r++) for (let c = 0; c < COLS; c++) if (ground[r][c] > 0 && !reserved.has(r * COLS + c)) pri.push([r, c]);'
b = '''  // BEE_SWAMP_PATCH: any obstacle whose goal is still open (soil, swamp, beehive, ice block)
  const open = k => goals.some(g => g.k === k && g.left > 0), wantT = new Set([...(open("ground") ? ["S", "H"] : []), ...(open("swamp") ? ["W"] : []), ...(open("hive") ? ["B", "G"] : []), ...(open("ice") ? ["E"] : [])]);
  if (wantT.size) for (let r = 0; r < ROWS; r++) for (let c = 0; c < COLS; c++) if (ground[r][c] > 0 && wantT.has(groundType[r][c]) && !reserved.has(r * COLS + c)) pri.push([r, c]);'''
if src.count(a) != 1: raise RuntimeError("patch-bee-swamp: pickBeeTarget changed")
src = src.replace(a, b); path.write_text(src); print("bees also go for swamps, beehives and ice blocks")
