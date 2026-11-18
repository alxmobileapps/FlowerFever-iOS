#!/usr/bin/env python3
"""Level background follows the garden: levels 1-50 use www/bg/g01.webp (Sunrise Nursery),
51-100 g02 (Dewdrop Garden) ... 951-1000 g20 (Grand Conservatory). Pictures supplied by the owner (Nov 2026).
Home and other screens keep the default background."""
import pathlib, sys

p = pathlib.Path(__file__).resolve().parent.parent / "www" / "index.html"
s = p.read_text(encoding="utf-8")

def swap(old, new):
    global s
    if s.count(old) != 1:
        sys.exit(f"patch-garden-bg: expected 1 of {old!r}, found {s.count(old)}")
    s = s.replace(old, new)

swap("function startLevel(i, asChallenge = false) {",
     """function gardenBg(i) {
  const st = document.body.style;
  if (i == null) { st.backgroundImage = st.backgroundSize = st.backgroundPosition = ""; return; }
  const g = Math.max(0, Math.min(19, Math.floor(i / 50))) + 1;
  st.backgroundImage = `url("bg/g${String(g).padStart(2, "0")}.webp")`;
  st.backgroundSize = "cover"; st.backgroundPosition = "center";
}
function startLevel(i, asChallenge = false) {""")
swap("levelIdx = i; syncBanner(); movesUsed = 0;", "levelIdx = i; syncBanner(); gardenBg(i); movesUsed = 0;")
p.write_text(s, encoding="utf-8")
print("garden backgrounds: 20 pictures, one per 50 levels")
