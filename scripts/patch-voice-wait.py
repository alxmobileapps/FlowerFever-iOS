"""Voices always finish.

- A voice never cuts off another: a new clip waits for the one playing (only the newest waiting clip is kept).
- Full-screen ads (interstitial and rewarded) wait until the voice has finished, so "In full bloom!" is heard in full.
- Out of moves: "You are very close!" (with its voice) only when little is left; when a lot of the goals are still
  open the heading is "Do you wish to continue?" (no "so close" voice).
Runs after the .patch files (it edits the final www/index.html).
"""
from pathlib import Path

path = Path("www/index.html")
src = path.read_text()
if "VOICE_WAIT_PATCH" in src:
    print("voice wait patch already applied"); raise SystemExit(0)

def rep(before, after):
    global src
    if src.count(before) != 1:
        raise RuntimeError("patch-voice-wait: code changed: " + before[:70])
    src = src.replace(before, after)

# when the current voice ends (ms clock), plus a hold for a voice that is about to start
rep("""function stopVoice() {
  voiceRequest++;""", """// VOICE_WAIT_PATCH: voices finish before the next one or a full-screen ad
let voiceEndAt = 0, voiceHoldAt = 0, voiceQueued = null;
const holdVoice = (ms, len = 1600) => { voiceHoldAt = Math.max(voiceHoldAt, T() + ms + len); };
function waitVoice(max = 3000) {
  const t0 = T();
  return new Promise(res => { const tick = () => { const left = Math.max(voiceEndAt, voiceHoldAt) - T(); if (left <= 0 || !soundOn || T() - t0 > max) res(); else setTimeout(tick, Math.min(left + 20, 200)); }; tick(); });
}
function stopVoice() {
  voiceEndAt = voiceHoldAt = 0; if (voiceQueued) { clearTimeout(voiceQueued); voiceQueued = null; }
  voiceRequest++;""")
rep("""  const a = ac(), buffer = voiceBuffer(key); if (!a || !buffer) return;
  try { if (voiceSrc) voiceSrc.stop(); } catch (_) {}""",
    """  const a = ac(), buffer = voiceBuffer(key); if (!a || !buffer) return;
  if (voiceSrc && T() < voiceEndAt) {   // let the voice that is playing finish; then say the newest one
    if (voiceQueued) clearTimeout(voiceQueued);
    voiceQueued = setTimeout(() => { voiceQueued = null; playClip(key, 6); }, voiceEndAt - T() + 60); return;
  }
  try { if (voiceSrc) voiceSrc.stop(); } catch (_) {}
  voiceEndAt = T() + (buffer.duration + .15) * 1000;""")

# full-screen ads wait for the voice
rep("""function showInterstitial() {
  const A = window.FlowerFeverAds;""", """function showInterstitial() { return waitVoice().then(showInterstitialNow); }
function showInterstitialNow() {
  const A = window.FlowerFeverAds;""")
rep("""function watchAdRaw(kind) {""", """function watchAdRaw(kind) { return waitVoice().then(() => watchAdRawNow(kind)); }
function watchAdRawNow(kind) {""")

# the win / lose voices start a little later: hold the ads for them too
rep("""busy = true; sfx("win"); setTimeout(() => say("In full bloom!"), 250);""",
    """busy = true; sfx("win"); holdVoice(250); setTimeout(() => say("In full bloom!"), 250);""")

# out of moves: "very close" only when little is left
rep("""sfx("lose"); setTimeout(() => say("So close!"), 950);""",
    """sfx("lose"); if (nearlyDone()) { holdVoice(950); setTimeout(() => say("So close!"), 950); }""")
rep("""    <h2>You are very close!</h2>""", """    <h2>${nearlyDone() ? "You are very close!" : "Do you wish to continue?"}</h2>""")
rep("""function showLose(again) {""", """// how much of the goals is still open (0 = all done, 1 = nothing done); "very close" = at most a quarter left
function nearlyDone() {
  const parts = goals.map(g => g.k === "score" ? Math.max(0, g.n - score) / Math.max(1, g.n) : Math.max(0, g.left) / Math.max(1, g.n));
  return !parts.length || parts.reduce((a, b) => a + b, 0) / parts.length <= .25;
}
function showLose(again) {""")
path.write_text(src)
print("voice wait patch applied")
