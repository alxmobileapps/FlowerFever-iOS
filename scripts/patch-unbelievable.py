"""'Unbelievable!' praise: when one move (not the Flower Shower) sets off 20 or more matches and power-up blasts
in a row, the big praise "Unbelievable!" shows (shake, petals) with its voice line in all 4 voices
(resources/voices-unbelievable.json: Voice 1 calm, Voice 2 emotion, Voice 3 female, Voice 4 male). Once per move.
Runs after patch-voices4.py."""
import json
from pathlib import Path
path = Path("www/index.html"); src = path.read_text()
if "UNBELIEVABLE_PATCH" in src: print("Unbelievable already added"); raise SystemExit(0)
def rep(a, b):
    global src
    n = src.count(a)
    if n != 1: raise RuntimeError(f"patch-unbelievable: expected 1 of {a[:70]!r}, found {n}")
    src = src.replace(a, b)
clips = json.loads(Path("resources/voices-unbelievable.json").read_text())
rep("const VOICE_FOR = {", "/* UNBELIEVABLE_PATCH */ " + "".join(f"VOICE_BANKS.{k}.unbeliev = {json.dumps(v)}; " for k, v in clips.items()) + "\nconst VOICE_FOR = { \"Unbelievable!\": \"unbeliev\",")
rep("let inShower = false, bigShown = 0, roundMaxCascade = 0, chainCount = 0;", "let inShower = false, bigShown = 0, roundMaxCascade = 0, chainCount = 0, unbelievMove = false;")
rep("busy = true; selected = null; hint = null; lastInput = T(); comboLevel = 0; bigShown = 0; chainCount = 0;",
    "busy = true; selected = null; hint = null; lastInput = T(); comboLevel = 0; bigShown = 0; chainCount = 0; unbelievMove = false;")
rep("  if (cascades >= 2 && !inShower) praise(PRAISE[Math.min(6, cascades)]);\n  roundMaxCascade = Math.max(roundMaxCascade, chainCount);",
    "  if (!inShower && chainCount >= 20 && !unbelievMove) { unbelievMove = true; bigPraise(\"Unbelievable!\"); }   // 20+ in one move\n"
    "  else if (cascades >= 2 && !inShower) praise(PRAISE[Math.min(6, cascades)]);\n  roundMaxCascade = Math.max(roundMaxCascade, chainCount);")
path.write_text(src); print("Unbelievable! at 20+ in one move")
