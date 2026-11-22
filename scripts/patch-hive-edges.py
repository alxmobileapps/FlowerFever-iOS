#!/usr/bin/env python3
"""Big beehive on the edge of the board: a side with no flower space next to it (board edge, a gap or a garden stone)
counts as already done, so a hive in a corner can always be broken with ordinary matches on its open sides."""
import pathlib, sys
p = pathlib.Path(__file__).resolve().parent.parent / "www" / "index.html"
s = p.read_text(encoding="utf-8")
if "HIVE_EDGES_PATCH" in s: print("hive edges already done"); sys.exit(0)
a = 'const h = { id: hives.length, big: true, r, c, sides: {} }; hives.push(h);'
if s.count(a) != 1: sys.exit("patch-hive-edges: anchor not found")
b = a + ('\n      { // HIVE_EDGES_PATCH: sides that face no flower space are already done\n'
         '        const open = (y, x) => !!(lay[y] && lay[y][x] && lay[y][x] !== "." && lay[y][x] !== "R");\n'
         '        const nb = { t: [[r - 1, c], [r - 1, c + 1]], b: [[r + 2, c], [r + 2, c + 1]], l: [[r, c - 1], [r + 1, c - 1]], r: [[r, c + 2], [r + 1, c + 2]] };\n'
         '        for (const k in nb) if (!nb[k].some(([y, x]) => open(y, x))) h.sides[k] = 2; }')
s = s.replace(a, b, 1)
p.write_text(s, encoding="utf-8")
print("big beehives: closed sides count as done")
