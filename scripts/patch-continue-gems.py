#!/usr/bin/env python3
"""Out of moves: the first continue in a level can be paid with an ad OR 3 diamonds (older players dislike ads).
Later continues in the same level are diamonds only and get pricier: 9, then 15, then 20."""
import pathlib, sys
p = pathlib.Path(__file__).resolve().parent.parent / "www" / "index.html"
s = p.read_text(encoding="utf-8")
if "CONTINUE_GEMS_PATCH" in s: print("continue gems already done"); sys.exit(0)
def rep(a, b):
    global s
    if s.count(a) != 1: sys.exit("patch-continue-gems: anchor not found: " + a[:60])
    s = s.replace(a, b, 1)
rep('const CONT_GEMS = [9, 15, 20];', 'const CONT_GEMS = [3, 9, 15, 20];   // CONTINUE_GEMS_PATCH: 1st continue = ad or 3 diamonds')
rep('const contCost = () => CONT_GEMS[Math.min(CONT_GEMS.length - 1, gemConts)];',
    'const contCost = () => CONT_GEMS[Math.min(CONT_GEMS.length - 1, +continued || 0)];')
rep('show(`<div class="ribbon">Out of moves</div>${adsLeft ? "" : gemBal()}',
    'show(`<div class="ribbon">Out of moves</div>${gemBal()}')
rep('<div class="btns">${adsLeft ? `<button class="btn" id="more">▶ Watch ad: +7 moves</button>` : `<button class="btn gembtn" id="gemMore">${GEM_SVG}<span>${cost}</span> Continue: +7 moves</button>`}',
    '<div class="btns">${adsLeft ? `<button class="btn" id="more">▶ Watch ad: +7 moves</button>` : ""}<button class="btn gembtn" id="gemMore">${GEM_SVG}<span>${cost}</span> Continue: +7 moves</button>')
p.write_text(s, encoding="utf-8")
print("continue: ad or 3 diamonds first, then 9, 15, 20")
