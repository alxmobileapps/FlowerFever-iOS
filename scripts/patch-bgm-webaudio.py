"""Background music through the game's own sound engine (Web Audio), not an <audio> player.
An <audio> element makes the phone treat the game music like a song: "Flower Fever" shows up in the
music player of the Control Center / lock screen (iPhone) and the media notification (Android), with
play/pause buttons. Now the song is decoded once (mono, 22 kHz, light on memory) and looped in Web Audio.
`bgm` stays as a small stand-in object (paused / play() / pause() / currentTime) for the rest of the code.
Runs after the .patch files (it edits the final www/index.html).
"""
import re
from pathlib import Path

path = Path("www/index.html")
src = path.read_text()
if "BGM_WEBAUDIO_PATCH" in src:
    print("bgm webaudio patch already applied"); raise SystemExit(0)

start = src.index("function music(on) {")
end = src.index("function duckMusic(")
old = src[start:end]
assert "new Audio(BGM_SRC)" in old, "patch-bgm-webaudio: music() changed"

new = r"""// BGM_WEBAUDIO_PATCH: the music loops in Web Audio, so the phone doesn't show it as a song in its music player
let bgmBuf = null, bgmLoading = null, bgmNode = null, bgmStartedAt = 0, bgmOffset = 0, bgmWanted = false;
function bgmLoad() {
  if (bgmBuf || bgmLoading) return bgmLoading;
  const a = ac(); if (!a) return null;
  bgmLoading = (async () => {
    try {
      const raw = await (await fetch(BGM_SRC)).arrayBuffer();
      const full = await new Promise((res, rej) => { const p = a.decodeAudioData(raw, res, rej); if (p && p.then) p.then(res, rej); });
      // mono, 22 kHz: about a quarter of the memory of the decoded stereo song
      try {
        const rate = 22050, off = new (window.OfflineAudioContext || window.webkitOfflineAudioContext)(1, Math.ceil(full.duration * rate), rate);
        const s = off.createBufferSource(); s.buffer = full; s.connect(off.destination); s.start(0);
        bgmBuf = await new Promise((res, rej) => { const p = off.startRendering(); if (p && p.then) p.then(res, rej); else off.oncomplete = e => res(e.renderedBuffer); });
      } catch (e) { bgmBuf = full; }
    } catch (e) { bgmLoading = null; }
    return bgmBuf;
  })();
  return bgmLoading;
}
function bgmStop() {
  if (!bgmNode) return;
  try { bgmOffset = ((AC.currentTime - bgmStartedAt) + bgmOffset) % (bgmBuf ? bgmBuf.duration : 1); } catch (e) {}
  try { bgmNode.stop(); } catch (e) {}
  try { bgmNode.disconnect(); } catch (e) {}
  bgmNode = null;
}
function bgmStart() {
  if (bgmNode || !bgmBuf || !AC) return;
  bgmNode = AC.createBufferSource(); bgmNode.buffer = bgmBuf; bgmNode.loop = true; bgmNode.connect(bgmGain);
  bgmStartedAt = AC.currentTime; bgmNode.start(0, bgmOffset % bgmBuf.duration);
}
function music(on) {
  if (on && (!soundOn || !musicOn)) on = false;
  bgmWanted = !!on;
  if (on && !bgm) {
    const a = ac(); if (!a) return;
    bgmGain = a.createGain(); bgmGain.gain.value = 0; bgmGain.connect(a.destination);
    bgm = { get paused() { return !bgmNode; }, get currentTime() { return bgmNode && AC ? AC.currentTime - bgmStartedAt : 0; }, play() { music(true); }, pause() { bgmStop(); } };
  }
  if (!bgm) return;
  if (on) {
    if (!bgmBuf) { const p = bgmLoad(); if (p) p.then(() => { if (bgmWanted) music(true); }); return; }
    if (!bgmNode) { bgmStart(); const t = AC.currentTime; bgmGain.gain.cancelScheduledValues(t); bgmGain.gain.setValueAtTime(0, t); bgmGain.gain.linearRampToValueAtTime(BGM_VOL, t + 1.5); }
  } else bgmStop();
}
"""
src = src[:start] + new + src[end:]
path.write_text(src)
print("bgm webaudio patch applied")
