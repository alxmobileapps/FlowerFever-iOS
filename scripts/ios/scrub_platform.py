#!/usr/bin/env python3
"""App Review 2.3.10: the iPhone app must not mention other platforms (Google Play, Android...).
Apple reads the strings inside the app binary, comments included. This runs last on the built web files:
it rewrites any such word (they are only left in code comments) and fails the build if one is still there."""
import re, sys
from pathlib import Path

# word edges that are not base64 characters, so embedded sound/picture data is never touched
NB, NA = r"(?<![A-Za-z0-9+/])", r"(?![A-Za-z0-9+/=])"
WORDS = [(r"Google Play Billing", "store billing"), (r"Google Play", "the store"), (r"Play Store", "store"),
         (r"Play Console", "store console"), (r"https?://play\.google\.com[^\"'\s`]*", ""), (NB + r"Android" + NA, "phone"), (NB + r"android" + NA + r"(?!['\"])", "phone")]
BAD = re.compile(r"google play|play store|play\.google|play console|" + NB + "android" + NA, re.I)
left = []
for f in sorted(Path("www").rglob("*")):
    if f.suffix not in (".html", ".js", ".css", ".json", ".txt"): continue
    s = f.read_text(errors="ignore"); o = s
    for a, b in WORDS: s = re.sub(a, b, s)
    if s != o: f.write_text(s); print("cleaned", f)
    for m in BAD.finditer(s):
        left.append(f"{f}: ...{s[max(0, m.start()-60):m.end()+40]!r}")
if left:
    print("Other-platform words still in the app (App Review 2.3.10):"); print("\n".join(left[:20])); sys.exit(1)
print("no other-platform words in the app")
