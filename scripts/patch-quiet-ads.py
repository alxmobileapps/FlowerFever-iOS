"""No between-level (interstitial) ad right after a rewarded ad or the rating window.

If the player watched a rewarded ad (x2 coins, +5 moves, a life, a lifeline, diamonds) or saw the
"Rate Flower Fever" window in the last 5 minutes, the between-level ad is skipped for that level and
shown at a later level change instead (the count of finished rounds is kept, not reset).
Runs after the .patch files (it edits the final www/index.html).
"""
from pathlib import Path

path = Path("www/index.html")
src = path.read_text()
if "QUIET_ADS_PATCH" in src:
    print("quiet ads patch already applied"); raise SystemExit(0)

def rep(before, after):
    global src
    if src.count(before) != 1:
        raise RuntimeError("patch-quiet-ads: code changed: " + before[:70])
    src = src.replace(before, after)

rep("""function interstitialDue(asChallenge, targetLevel = levelIdx) {
  return booted &&""", """// QUIET_ADS_PATCH: time of the last rewarded ad / rating window
let lastBigScreen = 0;
const QUIET_MS = 5 * 60 * 1000;
function interstitialDue(asChallenge, targetLevel = levelIdx) {
  return Date.now() - lastBigScreen > QUIET_MS && booted &&""")
rep("""async function useBooster(m) {""", """function watchAdQuiet(kind) { lastBigScreen = Date.now(); return watchAdRaw(kind).finally(() => { lastBigScreen = Date.now(); }); }
async function useBooster(m) {""")
rep("""function watchAd(kind) {""", """const watchAd = kind => watchAdQuiet(kind);
function watchAdRaw(kind) {""")
rep("""  ratingPromptSeen = true;
  try { localStorage.setItem("ff.ratingPromptSeen", "1"); } catch (e) {}""", """  ratingPromptSeen = true; lastBigScreen = Date.now();
  try { localStorage.setItem("ff.ratingPromptSeen", "1"); } catch (e) {}""")
path.write_text(src)
print("quiet ads patch applied")
