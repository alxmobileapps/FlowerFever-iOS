"""iPhone version of the game page (runs last, on the final www/index.html).

- Account: "Sign in with Apple" next to "Sign in with Google" (Apple requires it when another sign-in is offered);
  the texts say "account" instead of "Google account".
- Rating: Apple's own review window (iOS doesn't allow a custom "rate us" window or Play Store link).
- No "Google Play" in any text; share messages link to the App Store (when the app id is set).
"""
from pathlib import Path

path = Path("www/index.html")
src = path.read_text()
if "IOS_PATCH" in src:
    print("iOS patch already applied"); raise SystemExit(0)

def rep(before, after, count=1):
    global src
    if src.count(before) != count:
        raise RuntimeError(f"patch-ios: code changed ({src.count(before)}x): " + before[:80])
    src = src.replace(before, after)

APPLE_SVG = '<svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true"><path fill="#fff" d="M16.4 12.6c0-2.6 2.1-3.8 2.2-3.9-1.2-1.8-3.1-2-3.7-2-1.6-.2-3.1.9-3.9.9-.8 0-2-.9-3.3-.9-1.7 0-3.3 1-4.2 2.5-1.8 3.1-.5 7.7 1.3 10.2.9 1.2 1.9 2.6 3.2 2.6 1.3-.1 1.8-.8 3.3-.8 1.6 0 2 .8 3.3.8 1.4 0 2.3-1.3 3.1-2.5 1-1.4 1.4-2.8 1.4-2.9 0 0-2.7-1-2.7-4zM13.9 5c.7-.9 1.2-2 1.1-3.2-1 0-2.3.7-3 1.6-.7.8-1.2 2-1.1 3.1 1.2.1 2.3-.6 3-1.5z"/></svg>'

# --- account box: Apple + Google buttons, neutral wording ---
rep("""    : `<div class="acctbox"><b>☁ Save your progress</b><span>Sign in with Google to keep your levels, diamonds and garden safe, and play on any phone. (Optional)</span><button class="btn gsignin" id="aIn">""",
    """    : `<div class="acctbox"><b>☁ Save your progress</b><span>Sign in to keep your levels, diamonds and garden safe, and play on any device. (Optional)</span>${(A.providers || []).includes("apple") ? `<button class="btn asignin" id="aInApple">""" + APPLE_SVG + """<span>Sign in with Apple</span></button>` : ""}<button class="btn gsignin" id="aIn">""")
rep("""    ? `<div class="acctbox"><b>✅ Signed in with Google</b>""",
    """    ? `<div class="acctbox"><b>✅ Signed in with ${A.user.provider === "apple" ? "Apple" : "Google"}</b>""")
rep("""  const i = el.querySelector("#aIn"); if (i) i.onclick = () => acctSignIn(again);""",
    """  const i = el.querySelector("#aIn"); if (i) i.onclick = () => acctSignIn(again, "google");
  const ia = el.querySelector("#aInApple"); if (ia) ia.onclick = () => acctSignIn(again, "apple");""")
rep("""async function acctSignIn(after) {
  const A = ACCT(); if (!A) return;
  show(`<div class="ribbon">Google account</div><h2>Signing in…</h2><p>Choose your Google account in the window that opens.</p>`, () => {});
  try { await A.signIn(); }""",
    """async function acctSignIn(after, provider = "google") {   // IOS_PATCH
  const A = ACCT(); if (!A) return;
  show(`<div class="ribbon">Your account</div><h2>Signing in…</h2><p>${provider === "apple" ? "Confirm with your Apple ID in the window that opens." : "Choose your Google account in the window that opens."}</p>`, () => {});
  try { await A.signIn(provider); }""")
rep("""<div class="ribbon">Google account</div>""", """<div class="ribbon">Your account</div>""", 4)
rep("""Your progress now saves to your Google account. Sign in on any phone to keep playing.""",
    """Your progress now saves to your account. Sign in on any device to keep playing.""")
rep("""It stops saving to your Google account until you sign in again.""", """It stops saving to your account until you sign in again.""")
rep(""".acctbox .btn{margin-top:4px}""", """.acctbox .btn{margin-top:4px}
.btn.asignin{display:flex;align-items:center;justify-content:center;gap:10px;background:#000!important;color:#fff!important;box-shadow:0 3px 0 #333!important;font-size:17px}
.acctbox .btn.asignin span{color:#fff;font:800 17px/1.2 var(--body)}""")

# --- store texts ---
rep("""Buying diamonds works in the Flower Fever app from Google Play.""", """Buying diamonds works in the Flower Fever app.""")
rep("""Restoring works in the app from Google Play.""", """Restoring works in the Flower Fever app.""")

# --- rating: Apple's review window, at the same moments (level 16, then every ~30 levels, 3 times at most) ---
rep("""  const native = window.Capacitor?.isNativePlatform?.() && window.Capacitor?.getPlatform?.() === "android";""",
    """  const native = window.Capacitor?.isNativePlatform?.() && !!window.FlowerFeverReview;""")
rep("""  WK("ff.ratingPromptSeen", "1"); WK("ff.rateTimes", times + 1); WK("ff.rateLaterAt", save.unlocked);
  show(""", """  WK("ff.ratingPromptSeen", "1"); WK("ff.rateTimes", times + 1); WK("ff.rateLaterAt", save.unlocked);
  try { window.FlowerFeverReview(); } catch (e) {} setTimeout(next, 600); return;   // iOS decides itself whether to show it
  show(""")

rep("""<p>Share your experience on Google Play.</p>""", """<p>Share your experience.</p>""")
rep("""<button class="btn" id="ratePlay">Rate in Play Store</button>""", """<button class="btn" id="ratePlay">Rate Flower Fever</button>""")

# --- share messages: App Store link ---
rep("""const PLAY_URL = "https://play.google.com/store/apps/details?id=com.alxmobileapps.flowerfever";""",
    """const PLAY_URL = window.FLOWER_APPSTORE_ID ? "https://apps.apple.com/app/id" + window.FLOWER_APPSTORE_ID : "";""")

if "Google Play" in src.replace("Google Play purchase", ""):
    import re
    left = [m.start() for m in re.finditer("Google Play", src)]
    print("note: 'Google Play' still appears in", len(left), "places (comments)")
path.write_text(src)
print("iOS patch applied")
