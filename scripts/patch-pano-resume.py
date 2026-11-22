#!/usr/bin/env python3
"""Home garden panorama: when the home screen is redrawn while the opening pan is still running
(e.g. the cloud save finishes loading a few seconds after launch), keep panning from where it was
instead of jumping straight to the current garden."""
import pathlib, sys
p = pathlib.Path(__file__).resolve().parent.parent / "www" / "index.html"
s = p.read_text(encoding="utf-8")
if "PANO_RESUME_PATCH" in s: print("pano resume already done"); sys.exit(0)
def rep(a, b):
    global s
    if s.count(a) != 1: sys.exit("patch-pano-resume: anchor not found: " + a[:60])
    s = s.replace(a, b, 1)
rep('let homeOpen = false, homeRaf = 0, panoramaIntroPlayed = false;',
    'let homeOpen = false, homeRaf = 0, panoramaIntroPlayed = false, panoT0 = null, panoStopped = false;   // PANO_RESUME_PATCH')
rep('let interrupted = false, introStart = null, center = 0, rightEnd = 0;',
    'let interrupted = panoStopped, introStart = panoT0, center = 0, rightEnd = 0;')
rep('''    interrupted = true;
    panoramaIntroPlayed = true;''', '''    interrupted = true; panoStopped = true;
    panoramaIntroPlayed = true;''')
rep('if (introStart === null) introStart = now;', 'if (introStart === null) introStart = panoT0 = now;')
rep('''    if (!interrupted && (introStart === null || performance.now() - introStart >= introDuration)) sc.scrollLeft = center;''',
    '''    if (!interrupted && introStart !== null && !reduceMotion && performance.now() - introStart < introDuration) { cancelAnimationFrame(homeRaf); homeRaf = requestAnimationFrame(animatePanorama); return; }
    if (!interrupted && (introStart === null || performance.now() - introStart >= introDuration)) sc.scrollLeft = center;''')
p.write_text(s, encoding="utf-8")
print("home panorama keeps going when the home screen is redrawn")
