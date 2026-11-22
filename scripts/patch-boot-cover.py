#!/usr/bin/env python3
"""App launch: cover the screen with the Home background until Home is drawn, so the level screen
(green board, moves bar) no longer flashes for a moment before Home appears.
Safety: the cover removes itself after 8 seconds even if something goes wrong."""
import pathlib, sys
p = pathlib.Path(__file__).resolve().parent.parent / "www" / "index.html"
s = p.read_text(encoding="utf-8")
if "BOOT_COVER_PATCH" in s: print("boot cover already done"); sys.exit(0)
def rep(a, b):
    global s
    if s.count(a) != 1: sys.exit("patch-boot-cover: anchor not found: " + a[:60])
    s = s.replace(a, b, 1)
rep('<body>', '<body>\n<div id="bootCover" style="position:fixed;inset:0;z-index:99999;background:#fdf6eb"></div>'
    '<script>/* BOOT_COVER_PATCH */setTimeout(function(){var c=document.getElementById("bootCover");if(c)c.remove();},8000);</script>')
rep('startLevel(startAt); showHome();',
    'startLevel(startAt); showHome(); requestAnimationFrame(() => { const bc = document.getElementById("bootCover"); if (bc) bc.remove(); });')
p.write_text(s, encoding="utf-8")
print("launch: no level-screen flash before Home")
