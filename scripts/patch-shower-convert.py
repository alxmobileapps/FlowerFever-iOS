#!/usr/bin/env python3
"""Flower Shower: all the moves left turn into power-ups first, then they all go off together.
Before, when every flower was already next to a power-up, the shower set off the first batch and then
converted the last 1-3 moves afterwards (seen most with fast forward). Now those last moves go on any flower."""
import pathlib, sys
p = pathlib.Path(__file__).resolve().parent.parent / "www" / "index.html"
s = p.read_text(encoding="utf-8")
if "SHOWER_CONVERT_PATCH" in s: print("shower convert already done"); sys.exit(0)
a = """    const spaced = ns.filter(p => !hasNearbySpecial(p.r, p.c));
    if (!spaced.length) {
      // Clear the current batch to make room, then retry the remaining moves.
      await popAllSpecials();
      let room = false;
      eachPiece(q => { if (q.type === "normal" && !q.frozen && !hasNearbySpecial(q.r, q.c)) room = true; });
      if (!room) {
        moves--;
        score += 900;
        updateHud();
      }
      continue;
    }
    const p = spaced[rnd(spaced.length)];"""
if s.count(a) != 1: sys.exit("patch-shower-convert: anchor not found")
b = """    let spaced = ns.filter(p => !hasNearbySpecial(p.r, p.c));
    if (!spaced.length) spaced = ns;   // SHOWER_CONVERT_PATCH: no spaced flower left: use any flower, never set off half the batch early
    const p = spaced[rnd(spaced.length)];"""
s = s.replace(a, b, 1)
p.write_text(s, encoding="utf-8")
print("shower: every move converts before anything goes off")
