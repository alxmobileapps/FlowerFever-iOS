"""Drawing order, top to bottom:
  1. praise words ("Amazing!", "Unbelievable!" ...) - above everything in the game (HUD, lifted pieces, board)
  2. lifted / glowing power-ups: Flower Shower power-ups waiting to go off, power-ups that were hit and wait
     for their turn, and power-ups growing just before they go off. They are drawn on the see-through layer
     over the board (patch-lift-overlay.py), so they are never cut off at the board's edge and never hidden
     behind a garden stone, soil or a neighbouring flower drawn after them.
  3. obstacles  4. the board.
Runs after patch-lift-overlay.py."""
from pathlib import Path
path = Path("www/index.html"); src = path.read_text()
if "LAYER_ORDER_PATCH" in src: print("layer order already applied"); raise SystemExit(0)
def rep(a, b, n=1):
    global src
    if src.count(a) != n: raise RuntimeError(f"patch-layer-order: expected {n} of {a[:70]!r}, found {src.count(a)}")
    src = src.replace(a, b)

rep("  const liftedNow = [], spinNow = [];", "  const liftedNow = [], spinNow = [], markedNow = [];   // LAYER_ORDER_PATCH")
rep("    if (p.charge) { chargingNow.push(p); continue; }",
    "    if (p.charge) { chargingNow.push(p); continue; }\n"
    "    if (p.marked && !p.fired && p.type !== \"normal\" && !p.falling && !p.tw) { markedNow.push(p); continue; }   // drawn on the lifted layer")
# open the lifted layer before the charging power-ups (and draw the marked ones there first) ...
rep("  for (const p of chargingNow) {\n    const k = Math.min(1, (t - p.charge) / CHARGE_MS)",
    """  { const ctx = liftLayer(S, liftedNow.length > 0 || spinNow.length > 0 || chargingNow.length > 0 || markedNow.length > 0) || boardRenderer.ctx;
  for (const p of markedNow) {   // a power-up that has been hit and is waiting for its turn
    const cx = (p.px + .5) * S, cy = (p.py + .5) * S, k = Math.min(1, (t - p.marked) / 180), pulse = .5 + .5 * Math.sin((t - p.marked) / 110);
    ctx.save(); ctx.globalAlpha = k;
    ctx.fillStyle = rg(ctx, cx, cy, S * .85, [[0, "rgba(255,250,200,.95)"], [.45, "rgba(255,210,60,.55)"], [1, "rgba(255,210,60,0)"]]); circle(ctx, cx, cy, S * (.72 + .08 * pulse)); ctx.fill();
    ctx.strokeStyle = `rgba(255,255,255,${.6 + .4 * pulse})`; ctx.lineWidth = S * .06; rrect(ctx, cx - S * .47, cy - S * .47, S * .94, S * .94, S * .22); ctx.stroke();
    ctx.strokeStyle = "rgba(255,190,30,.95)"; ctx.lineWidth = S * .03; rrect(ctx, cx - S * .47, cy - S * .47, S * .94, S * .94, S * .22); ctx.stroke();
    ctx.restore();
    const s = S * (1 + .08 * pulse * k); drawPiece(ctx, p, cx, cy, s, t);
    if (p.frozen) { ctx.save(); ctx.translate(cx, cy); ctx.scale(S, S); drawIce(ctx, t, p); ctx.restore(); }
  }
  for (const p of chargingNow) {
    const k = Math.min(1, (t - p.charge) / CHARGE_MS)""")
# ... and keep using it for the spinning / lifted ones (the old opening of the block goes away)
rep("  { const ctx = liftLayer(S, liftedNow.length > 0 || spinNow.length > 0) || boardRenderer.ctx;\n  for (const p of spinNow) {",
    "  for (const p of spinNow) {")
# praise words above everything in the game (the lifted layer is z-index 5, the HUD 7)
i = src.find("</style>", src.find("#praise{position:absolute"))
src = src[:i] + "\n#praise{z-index:25}   /* LAYER_ORDER_PATCH: praise words on top of everything in the game */\n" + src[i:]
path.write_text(src); print("layer order: praise > lifted power-ups > obstacles > board")
