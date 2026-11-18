#!/usr/bin/env python3
"""Lifted (floating) power-ups and the spinning Bouquet flower are drawn on a
transparent layer that is bigger than the board, so a piece on the edge row or
column is shown whole instead of being cut off at the board's edge."""
import sys
p = sys.argv[1] if len(sys.argv) > 1 else "www/index.html"
s = open(p, encoding="utf-8").read()

def rep(old, new):
    global s
    if s.count(old) != 1:
        sys.exit(f"patch-lift-overlay: anchor found {s.count(old)}x: {old[:60]!r}")
    s = s.replace(old, new)

HELPER = r'''let liftCv = null, liftG = null, liftOn = false, liftTo = 0;
function liftLayer(S, on) {   // a see-through layer over the board with a margin around it
  if (!liftCv) {
    liftCv = document.createElement("canvas"); liftCv.setAttribute("aria-hidden", "true");
    liftCv.style.cssText = "position:fixed;left:0;top:0;pointer-events:none;z-index:5;display:none";
    document.body.appendChild(liftCv); liftG = liftCv.getContext("2d");
  }
  clearTimeout(liftTo);
  const b = on && canvas.offsetParent ? canvas.getBoundingClientRect() : null;
  if (!b || !b.width) {
    if (liftOn) { liftG.setTransform(1, 0, 0, 1, 0, 0); liftG.clearRect(0, 0, liftCv.width, liftCv.height); liftCv.style.display = "none"; liftOn = false; }
    return null;
  }
  liftTo = setTimeout(() => liftLayer(S, false), 150);   // board stopped drawing: hide the layer
  const sc = b.width / (S * COLS), M = Math.ceil(S * sc * .7);
  const w = Math.ceil(b.width + 2 * M), h = Math.ceil(b.height + 2 * M), pw = Math.round(w * DPR), ph = Math.round(h * DPR);
  if (liftCv.width !== pw || liftCv.height !== ph) { liftCv.width = pw; liftCv.height = ph; liftCv.style.width = w + "px"; liftCv.style.height = h + "px"; }
  liftCv.style.transform = `translate(${b.left - M}px,${b.top - M}px)`;
  if (!liftOn) { liftCv.style.display = "block"; liftOn = true; }
  liftG.setTransform(1, 0, 0, 1, 0, 0); liftG.clearRect(0, 0, pw, ph);
  liftG.setTransform(DPR * sc, 0, 0, DPR * sc, M * DPR, M * DPR);
  return liftG;
}
function draw(t) {'''
rep("function draw(t) {", HELPER)
rep("  for (const p of spinNow) {",
    "  { const ctx = liftLayer(S, liftedNow.length > 0 || spinNow.length > 0) || boardRenderer.ctx;\n  for (const p of spinNow) {")
rep("  }\n  chargingNow.length = 0;", "  }\n  }\n  chargingNow.length = 0;")
open(p, "w", encoding="utf-8").write(s)
print("patch-lift-overlay: ok")
