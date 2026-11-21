#!/usr/bin/env python3
"""When ads start (Nov 2026):
  - the banner under the board shows from level 11 (after level 10 is beaten)
  - between-level full-screen ads come from level 101 (after level 100), once every 10 rounds
Rewarded ads (watch an ad for a reward) are unchanged and stay available to everyone.
Runs after patch-quiet-ads.py (which writes the lines changed here)."""
import pathlib, sys

p = pathlib.Path(__file__).resolve().parent.parent / "www" / "index.html"
s = p.read_text(encoding="utf-8")
BANNER_FROM = 10   # level index (0-based): 10 = level 11
INTER_FROM = 100   # level index (0-based): 100 = level 101
INTER_EVERY = 10   # rounds between two full-screen ads
INTER_ON = True    # between-level (interstitial) ads on (Nov 22 2026)

def swap(old, new):
    global s
    if s.count(old) != 1:
        sys.exit(f"patch-ad-levels: expected 1 of {old!r}, found {s.count(old)}")
    s = s.replace(old, new)

swap("!mapOpen && booted && levelIdx >= 20;", f"!mapOpen && booted && levelIdx >= {BANNER_FROM};")
swap("booted && levelIdx >= 20 && targetLevel >= 20 &&", f"{'' if INTER_ON else 'false && '}booted && levelIdx >= {INTER_FROM} && targetLevel >= {INTER_FROM} &&")
swap("(save.adRounds ?? save.adWins ?? 0) >= 5;", f"(save.adRounds ?? save.adWins ?? 0) >= {INTER_EVERY};")
p.write_text(s, encoding="utf-8")
print(f"ads: banner from level {BANNER_FROM + 1}, between-level ads " + (f"from level {INTER_FROM + 1}, every {INTER_EVERY} rounds" if INTER_ON else "OFF"))
