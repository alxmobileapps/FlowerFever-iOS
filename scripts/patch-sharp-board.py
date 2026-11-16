"""Sharper board: flowers are drawn at a higher resolution.

- The board is drawn at up to 2x the screen's CSS pixels on the normal setting (was 1.5x) and up to 3x on
  "High" (was 2x); "Low" goes from 1.25x to 1.5x. Phones today have 2.5-3x screens, so 1.5x looked soft.
Runs after the .patch files (it edits the final www/index.html).
"""
from pathlib import Path
path = Path("www/index.html"); src = path.read_text()
if "SHARP_BOARD_PATCH" in src:
    print("sharp board patch already applied"); raise SystemExit(0)
def rep(a, b):
    global src
    if src.count(a) != 1: raise RuntimeError("patch-sharp-board: code changed: " + a[:60])
    src = src.replace(a, b)
rep("const maxDPR = () => quality === 0 ? 1.25 : quality === 1 ? 1.5 : 2;",
    "const maxDPR = () => quality === 0 ? 1.5 : quality === 1 ? 2 : 3;   // SHARP_BOARD_PATCH")
path.write_text(src); print("sharp board patch applied")
