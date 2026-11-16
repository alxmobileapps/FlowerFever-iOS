"""Rating window: a player who tapped "Not now" sees it again about 30 levels later (at most 3 times in all).
A player who tapped "Rate in Play Store" never sees it again. Runs after the .patch files (it edits the final www/index.html).
"""
from pathlib import Path

path = Path("www/index.html")
src = path.read_text()
if "RATE_AGAIN_PATCH" in src:
    print("rate again patch already applied"); raise SystemExit(0)

def rep(before, after):
    global src
    if src.count(before) != 1:
        raise RuntimeError("patch-rate-again: code changed: " + before[:70])
    src = src.replace(before, after)

rep("""  try { if (localStorage.getItem("ff.ratingPromptSeen")) { next(); return; } } catch (e) {}
  ratingPromptSeen = true; lastBigScreen = Date.now();
  try { localStorage.setItem("ff.ratingPromptSeen", "1"); } catch (e) {}""",
    """  // RATE_AGAIN_PATCH: "Not now" → ask again ~30 levels later (3 times at most); "Rate" → never again
  const RK = k => { try { return localStorage.getItem(k); } catch (e) { return null; } }, WK = (k, v) => { try { localStorage.setItem(k, String(v)); } catch (e) {} };
  if (RK("ff.rated")) { next(); return; }
  let times = +RK("ff.rateTimes") || 0, laterAt = +RK("ff.rateLaterAt") || 0;
  if (RK("ff.ratingPromptSeen") && !times) { times = 1; laterAt = save.unlocked; WK("ff.rateTimes", 1); WK("ff.rateLaterAt", laterAt); }   // saw it before this update
  if (times >= 3 || (times && save.unlocked < laterAt + 30)) { next(); return; }
  ratingPromptSeen = true; lastBigScreen = Date.now();
  WK("ff.ratingPromptSeen", "1"); WK("ff.rateTimes", times + 1); WK("ff.rateLaterAt", save.unlocked);""")
rep("""      openLink(PLAY_STORE_URL);
      next();""", """      try { localStorage.setItem("ff.rated", "1"); } catch (e) {}
      openLink(PLAY_STORE_URL);
      next();""")
path.write_text(src)
print("rate again patch applied")
