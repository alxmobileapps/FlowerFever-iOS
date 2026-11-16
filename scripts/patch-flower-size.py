"""Flowers and power-ups on the board are drawn at 90% of their old size (a little more space between them)."""
from pathlib import Path
path = Path("www/index.html"); src = path.read_text()
a = "function drawPiece(g, p, cx, cy, s, t) {\n  g.save(); g.translate(cx, cy); g.scale(s, s);"
b = "function drawPiece(g, p, cx, cy, s, t) {\n  g.save(); g.translate(cx, cy); g.scale(s * .9, s * .9);   // FLOWER_SIZE_PATCH: 90%"
if "FLOWER_SIZE_PATCH" in src: print("flower size patch already applied")
elif src.count(a) == 1: path.write_text(src.replace(a, b)); print("flower size patch applied")
else: raise RuntimeError("patch-flower-size: drawPiece changed")
