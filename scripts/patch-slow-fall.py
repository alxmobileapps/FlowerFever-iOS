"""Board falling speed: 0.75x the original (it was 0.5x, then +50%).
Speed cap VMAX x0.75 (.03 -> .0225) and pull G x0.5625 (.00011 -> .000061875, since time ~ 1/sqrt(G)).
The diagonal slide takes 110 / 0.75 = 147 ms. The end-of-level Fast button is 3x (was 2x)."""
from pathlib import Path
path = Path("www/index.html"); src = path.read_text()
if "SLOW_FALL_PATCH" in src: print("slow fall already applied"); raise SystemExit(0)
def rep(a, b):
    global src
    n = src.count(a)
    if n != 1: raise RuntimeError(f"patch-slow-fall: expected 1 of {a!r}, found {n}")
    src = src.replace(a, b)
rep("const BEE_MS = 1000, G = .00011, VMAX = .03,", "const BEE_MS = 1000, G = .000061875, VMAX = .0225, SLOW_FALL_PATCH = 2,")
rep("moveTween(p, r, c, 110); used.add(p.id);", "moveTween(p, r, c, 147); used.add(p.id);")
rep("const SHOWER_FAST_SPEED = 2;", "const SHOWER_FAST_SPEED = 3;")
path.write_text(src); print("flowers fall at 0.75x speed; Fast-forward 3x")
