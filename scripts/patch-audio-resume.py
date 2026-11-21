"""Sound comes back right away after switching apps (iPhone).
iOS puts the game's sound engine in an "interrupted" state when the app goes to the background; the game only
woke it from "suspended", so after returning it stayed silent until iOS freed it by itself (about 2 minutes).
Now it is woken from any non-running state, when the game becomes visible again and on the next tap."""
from pathlib import Path
path = Path("www/index.html"); src = path.read_text()
if "AUDIO_RESUME_PATCH" in src: print("audio resume already applied"); raise SystemExit(0)
def rep(a, b):
    global src
    if src.count(a) != 1: raise RuntimeError(f"patch-audio-resume: expected 1 of {a[:70]!r}, found {src.count(a)}")
    src = src.replace(a, b)
rep('  if (AC.state === "suspended") { const r = AC.resume(); if (r && r.catch) r.catch(() => {}); }\n  return AC;',
    '  if (AC.state !== "running" && AC.state !== "closed") { const r = AC.resume(); if (r && r.catch) r.catch(() => {}); }   // AUDIO_RESUME_PATCH: also "interrupted" (iOS)\n  return AC;')
rep("function route(node, wet) {", """// AUDIO_RESUME_PATCH: wake the sound engine when the game comes back, and on the next touch (iOS needs a tap sometimes)
function wakeAudio() {
  if (!soundOn || !AC || AC.state === "running" || AC.state === "closed" || document.hidden) return;
  try { const r = AC.resume(); if (r && r.then) r.then(() => { if (soundOn && AC.state === "running" && bgmWanted) music(true); }, () => {}); } catch (e) {}
}
document.addEventListener("visibilitychange", () => { if (!document.hidden) { wakeAudio(); setTimeout(wakeAudio, 400); setTimeout(wakeAudio, 1500); } });
addEventListener("pageshow", wakeAudio); addEventListener("focus", wakeAudio);
["touchend", "pointerdown", "keydown"].forEach(ev => addEventListener(ev, wakeAudio, { capture: true, passive: true }));
function route(node, wet) {""")
path.write_text(src); print("sound wakes up right after switching apps")
