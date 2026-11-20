"""Tablets: the board ends at 70% of the screen height at most, so there is room under it.
A screen counts as a tablet when it is less than 1.8x taller than wide (phones are about 2x; tablets 1.33-1.67).
Phones are unchanged."""
from pathlib import Path
path = Path("www/index.html"); src = path.read_text()
if "TABLET_BOARD_PATCH" in src: print("tablet board already applied"); raise SystemExit(0)
a = 'const st = $("#stage"), w = st.clientWidth, h = st.clientHeight;'
b = ('const st = $("#stage"), w = st.clientWidth, TABLET_BOARD_PATCH = innerHeight / innerWidth < 1.8,   // tablet: board ends at 70% of the screen\n'
     '    h = TABLET_BOARD_PATCH ? Math.max(120, Math.min(st.clientHeight, Math.round(innerHeight * .70 - st.getBoundingClientRect().top))) : st.clientHeight;')
if src.count(a) != 1: raise RuntimeError("patch-tablet-board: layout() changed")
path.write_text(src.replace(a, b)); print("tablet: board up to 70% of the screen")
