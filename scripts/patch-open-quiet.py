"""No interstitial ad in the first 5 minutes after the app is opened (the quiet time starts at app open).
Runs after patch-quiet-ads.py (it edits the final www/index.html).
"""
from pathlib import Path

path = Path("www/index.html")
src = path.read_text()
if "OPEN_QUIET_PATCH" in src:
    print("open quiet patch already applied"); raise SystemExit(0)

def rep(before, after):
    global src
    if src.count(before) != 1:
        raise RuntimeError("patch-open-quiet: code changed: " + before[:70])
    src = src.replace(before, after)

rep("""let lastBigScreen = 0;""", """let lastBigScreen = Date.now();   // OPEN_QUIET_PATCH: opening the app starts a 5-minute quiet time too""")
path.write_text(src)
print("open quiet patch applied")
