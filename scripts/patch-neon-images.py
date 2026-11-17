#!/usr/bin/env python3
"""iPhone only: show the home logo words and the praise words as pictures (www/neon/*.webp).

Safari draws the neon text (outline + glow) differently from Android, so these pictures were
rendered in Chrome from the same styles; the iPhone now looks exactly like the Android app.
Sizes are in em, so the pictures take the same space the text did (a logo word sits on the
text baseline with a short margin box, so it does not make the title line taller). Any word without a picture
still shows as text. Regenerate the pictures with tools/neon.py if the styles or words change."""
import json, pathlib, sys

root = pathlib.Path(__file__).resolve().parent.parent
p = root / "www" / "index.html"
s = p.read_text(encoding="utf-8")
meta = json.loads((root / "www" / "neon" / "neon.json").read_text(encoding="utf-8"))

def must(old, new, count=1):
    global s
    if s.count(old) != count:
        sys.exit(f"patch-neon-images: expected {count} of {old[:70]!r}, found {s.count(old)}")
    s = s.replace(old, new)

helpers = (
    "\nvar NEON = " + json.dumps(meta, separators=(",", ":")) + ";\n"
    "function neonWord(t) { const m = NEON.logo[t]; if (!m) return t;\n"
    "  return `<img class=\"neonw\" alt=\"\" src=\"neon/${m.src}\" style=\"width:${m.w}em;height:${m.h}em;margin:-${(m.h - m.m + m.va - .3).toFixed(4)}em -${m.m}em -${(m.m - m.va).toFixed(4)}em;vertical-align:baseline\">`; }\n"
    "function neonPraise(t) { const m = NEON.praise[t]; if (!m) return null;\n"
    "  return `<img class=\"neonp\" alt=\"\" src=\"neon/${m.src}\" style=\"width:${m.w}em;height:${m.h}em;margin:-${m.pt}em -${m.pr}em -${m.pb}em -${m.pl}em\">`; }\n"
)
# defined at the start of the game script, before anything can draw the home screen or a praise word
must('<script>\n(() => {\n"use strict";\n', '<script>\n(() => {\n"use strict";\n' + helpers)
must('<h1 class="h3name" aria-label="Flower Fever">Flower<img class="h3rb" alt="" src="${SPRITE_SRC.rainbow}">Fever</h1>',
     '<h1 class="h3name" aria-label="Flower Fever">${neonWord("Flower")}<img class="h3rb" alt="" src="${SPRITE_SRC.rainbow}">${neonWord("Fever")}</h1>')
must('praiseEl.innerHTML = `<span class="pw">${t}</span>',
     'praiseEl.innerHTML = `<span class="pw">${neonPraise(text) || t}</span>')
if "</style>" not in s: sys.exit("patch-neon-images: no </style>")
s = s.replace("</style>", "#praise .pw img.neonp,.h3name img.neonw{display:inline-block;max-width:none;pointer-events:none;-webkit-user-drag:none}\n#praise .pw img.neonp{display:block}\n</style>", 1)
p.write_text(s, encoding="utf-8")
print("neon pictures: logo + %d praise words" % len(meta["praise"]))
