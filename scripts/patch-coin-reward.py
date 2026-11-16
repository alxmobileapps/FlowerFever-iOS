"""Bigger flower-coin reward per puzzle win: a new level gives 15 + 5 per star (20-30), a replay gives 5.
A rewarded ad still doubles it. Runs after the .patch files (it edits the final www/index.html).
"""
from pathlib import Path

path = Path("www/index.html")
src = path.read_text()
if "COIN_REWARD_PATCH" in src:
    print("coin reward patch already applied"); raise SystemExit(0)

def rep(before, after):
    global src
    if src.count(before) != 1:
        raise RuntimeError("patch-coin-reward: code changed: " + before[:70])
    src = src.replace(before, after)

rep("""  // flower coins: first win 5 + 2 per star, replays 2; water only for 3 stars. A rewarded ad doubles the coins.
  const fcGain = wasCh ? 0 : firstWin ? 5 + 2 * st : 2,""",
    """  // COIN_REWARD_PATCH flower coins: first win 15 + 5 per star, replays 5; water only for 3 stars. A rewarded ad doubles the coins.
  const fcGain = wasCh ? 0 : firstWin ? 15 + 5 * st : 5,""")
rep("""a new level gives ${FC_SVG}5 + 2 per star""", """a new level gives ${FC_SVG}15 + 5 per star""")
path.write_text(src)
print("coin reward patch applied")
