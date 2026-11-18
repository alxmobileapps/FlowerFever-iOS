#!/usr/bin/env python3
"""When ads start (Nov 2026):
  - the banner under the board shows from level 11 (after level 10 is beaten)
  - between-level full-screen ads come from level 51 (after level 50), still at most every 5 rounds
Rewarded ads (watch an ad for a reward) are unchanged and stay available to everyone.
Runs after patch-quiet-ads.py (which writes the lines changed here)."""
import pathlib, sys

p = pathlib.Path(__file__).resolve().parent.parent / "www" / "index.html"
s = p.read_text(encoding="utf-8")
BANNER_FROM = 10   # level index (0-based): 10 = level 11
INTER_FROM = 50    # level index (0-based): 50 = level 51
INTER_ON = False   # between-level (interstitial) ads switched off for now; set True to bring them back

def swap(old, new):
    global s
    if s.count(old) != 1:
        sys.exit(f"patch-ad-levels: expected 1 of {old!r}, found {s.count(old)}")
    s = s.replace(old, new)

swap("!mapOpen && booted && levelIdx >= 20;", f"!mapOpen && booted && levelIdx >= {BANNER_FROM};")
swap("booted && levelIdx >= 20 && targetLevel >= 20 &&", f"{'' if INTER_ON else 'false && '}booted && levelIdx >= {INTER_FROM} && targetLevel >= {INTER_FROM} &&")
p.write_text(s, encoding="utf-8")
print(f"ads: banner from level {BANNER_FROM + 1}, between-level ads " + (f"from level {INTER_FROM + 1}" if INTER_ON else "OFF"))
