"""Four voices: Voice 1 (Calm, the default), Voice 2 (Emotion), Voice 3 (the old Female), Voice 4 (the old Male).
The new clips come from resources/voices-calm-emotion.json (cut from the Calm.mp3 / Emotion.mp3 recordings,
24 kHz mono 48 kbps like the others). A player who already picked Male or Female keeps that voice."""
import json
from pathlib import Path
path = Path("www/index.html"); src = path.read_text()
if "VOICES4_PATCH" in src: print("4 voices already added"); raise SystemExit(0)
def rep(a, b):
    global src
    n = src.count(a)
    if n != 1: raise RuntimeError(f"patch-voices4: expected 1 of {a[:70]!r}, found {n}")
    src = src.replace(a, b)
banks = json.loads(Path("resources/voices-calm-emotion.json").read_text())
rep("const VOICE_FOR = {", "/* VOICES4_PATCH */ Object.assign(VOICE_BANKS, " + json.dumps(banks, separators=(",", ":")) + ");\n"
    "const VOICE_LIST = [[\"calm\", \"Voice 1\"], [\"emotion\", \"Voice 2\"], [\"female\", \"Voice 3\"], [\"male\", \"Voice 4\"]];\nconst VOICE_FOR = {")
rep('let voiceStyle = "female", voiceRequest = 0;', 'let voiceStyle = "calm", voiceRequest = 0;')
rep('if (savedVoice === "male" || savedVoice === "female") voiceStyle = savedVoice;', 'if (savedVoice && VOICE_BANKS[savedVoice]) voiceStyle = savedVoice;')
rep('for (const style of ["male", "female"]) {', 'for (const style of Object.keys(VOICE_BANKS)) {')
rep('''      <button class="voice-option" type="button" data-voice="male" aria-pressed="${voiceStyle === "male"}">👨 Male</button>
      <button class="voice-option" type="button" data-voice="female" aria-pressed="${voiceStyle === "female"}">👩 Female</button>''',
    '''      ${VOICE_LIST.map(([v, label]) => `<button class="voice-option" type="button" data-voice="${v}" aria-pressed="${voiceStyle === v}">${label}</button>`).join("")}''')
rep(".voice-options{clear:both;display:flex;gap:8px}", ".voice-options{clear:both;display:grid;grid-template-columns:1fr 1fr;gap:8px}")
rep("Flower Fever original voice recordings (Male and Female)", "Flower Fever original voice recordings (4 voices)")
path.write_text(src); print("4 voices: Voice 1 (default) to Voice 4")
