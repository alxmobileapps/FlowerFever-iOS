#!/usr/bin/env python3
"""Battery: while Home or the Garden screen covers the board, stop redrawing the hidden board every frame.
The game itself keeps running; the board is drawn again on the first frame after Home/Garden closes."""
import pathlib, sys
p = pathlib.Path(__file__).resolve().parent.parent / "www" / "index.html"
s = p.read_text(encoding="utf-8")
if "IDLE_DRAW_PATCH" in s: print("idle draw already done"); sys.exit(0)
a = 'update(t, fastFwd ? dt * SHOWER_FAST_SPEED : dt); draw(t); drawParty(t, dt); syncBanner();'
if s.count(a) != 1: sys.exit("patch-idle-draw: anchor not found")
b = ('update(t, fastFwd ? dt * SHOWER_FAST_SPEED : dt); if (!(homeOpen || document.getElementById("gardenView"))) draw(t); '
     'drawParty(t, dt); syncBanner();   // IDLE_DRAW_PATCH: no board drawing behind Home/Garden')
s = s.replace(a, b, 1)
p.write_text(s, encoding="utf-8")
print("board is not redrawn while Home or Garden covers it")
