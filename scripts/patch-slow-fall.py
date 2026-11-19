"""Flowers fall 2x slower (board gravity): each fall takes twice as long.
Time to fall = half from the speed cap (VMAX / 2) and half from the pull (G / 4, since time ~ 1/sqrt(G)).
The diagonal slide also takes twice as long (110 -> 220 ms)."""
from pathlib import Path
path = Path("www/index.html"); src = path.read_text()
if "SLOW_FALL_PATCH" in src: print("slow fall already applied"); raise SystemExit(0)
def rep(a, b):
    global src
    n = src.count(a)
    if n != 1: raise RuntimeError(f"patch-slow-fall: expected 1 of {a!r}, found {n}")
    src = src.replace(a, b)
rep("const BEE_MS = 1000, G = .00011, VMAX = .03,", "const BEE_MS = 1000, G = .0000275, VMAX = .015, SLOW_FALL_PATCH = 2,")
rep("moveTween(p, r, c, 110); used.add(p.id);", "moveTween(p, r, c, 220); used.add(p.id);")
path.write_text(src); print("flowers fall 2x slower")
