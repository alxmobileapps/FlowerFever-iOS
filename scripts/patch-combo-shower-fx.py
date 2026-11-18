#!/usr/bin/env python3
"""Two effects (Nov 2026):
1. Striped bloom + Bouquet combo: the Bouquet first grows while it spins for 1 second, then the
   striped beams go out in all directions (same blast as before).
2. Flower Shower: every power-up that is sitting still on the board (including the ones made from
   the moves left) is lifted and highlighted, like a tapped tile, until it goes off."""
import pathlib, sys

p = pathlib.Path(__file__).resolve().parent.parent / "www" / "index.html"
s = p.read_text(encoding="utf-8")

def swap(old, new):
    global s
    if s.count(old) != 1:
        sys.exit(f"patch-combo-shower-fx: expected 1 of {old[:70]!r}, found {s.count(old)}")
    s = s.replace(old, new)

# 1) Bouquet grows and spins for 1 s before the stripe + bouquet blast
swap('    a.fired = b.fired = true; countSpecial("stripe", r, c); countSpecial("wrap", r, c);\n    destroy(a); destroy(b); praise("Gorgeous!");',
     '    a.fired = b.fired = true; countSpecial("stripe", r, c); countSpecial("wrap", r, c);\n'
     '    { const bq = kind(a) === "wrap" ? a : b; bq.spinGrow = T(); sfx("charge"); await sleep(inShower && showerSkip ? 150 : 1000); bq.spinGrow = 0; }\n'
     '    destroy(a); destroy(b); praise("Gorgeous!");')
swap('  const liftedNow = [];', '  const liftedNow = [], spinNow = [];')
swap('    if (p.charge) { chargingNow.push(p); continue; }',
     '    if (p.spinGrow) { spinNow.push(p); continue; }\n    if (p.charge) { chargingNow.push(p); continue; }')
swap('  for (const p of liftedNow) {', r'''  for (const p of spinNow) {   // the Bouquet in a Striped bloom + Bouquet combo: grows while it spins
    const k = Math.min(1, (t - p.spinGrow) / 1000), e = 1 - Math.pow(1 - k, 2);
    const cx = (p.px + .5) * S, cy = (p.py + .5) * S, s = S * (1 + 1.2 * e);
    ctx.fillStyle = rg(ctx, cx, cy, s * .9, [[0, `rgba(255,255,255,${.8 * e})`], [.5, `rgba(255,220,240,${.45 * e})`], [1, "rgba(255,255,255,0)"]]);
    circle(ctx, cx, cy, s * .9); ctx.fill();
    ctx.save(); ctx.translate(cx, cy); ctx.rotate(e * TAU * 2.5); drawPiece(ctx, p, 0, 0, s, t); ctx.restore();
  }
  for (const p of liftedNow) {''')

# 2) Flower Shower: idle power-ups are lifted + highlighted
swap('  for (const k in liftT) if (!liftKeys.has(+k)) delete liftT[k];',
     '  if (inShower) for (let r = 0; r < ROWS; r++) for (let c = 0; c < COLS; c++) {   // Flower Shower: power-ups waiting to go off hover\n'
     '    const q = grid[r] && grid[r][c];\n'
     '    if (q && q.type !== "normal" && !q.falling && !q.tw && !q.charge && !q.fired && !q.spinGrow && Math.abs(q.py - r) < .01 && Math.abs(q.px - c) < .01) liftKeys.add(r * COLS + c);\n'
     '  }\n'
     '  for (const k in liftT) if (!liftKeys.has(+k)) delete liftT[k];')

p.write_text(s, encoding="utf-8")
print("combo + shower effects: bouquet spin before stripe+bouquet, shower power-ups hover")
