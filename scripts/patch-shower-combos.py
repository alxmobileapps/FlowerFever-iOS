"""Flower Shower combos, and water drops on pond plants.

1) When the Flower Shower sets off the power-ups already on the board, two power-ups side by side now
   combine exactly as if the player had swapped them (Rainbow + Bee, Rainbow + Rainbow, Bomb + Stripe...).
   Before, the second one was just cleared for points. In a group of three or more, they pair up one
   pair at a time; a lone one goes off on its own as before.
2) Pond plants get a gentle water ripple and drops falling around their base, at every stage.
Runs after patch-garden-plants.py (it edits the final www/index.html).
"""
from pathlib import Path

path = Path("www/index.html")
src = path.read_text()
if "SHOWER_COMBOS_PATCH" in src:
    print("shower combos patch already applied"); raise SystemExit(0)

def rep(before, after):
    global src
    n = src.count(before)
    if n != 1:
        raise RuntimeError(f"patch-shower-combos: expected 1 of: {before[:80]!r}, found {n}")
    src = src.replace(before, after)

rep("""    const p = specials[0];
    comboLevel = 1;
    // Collect the entire side-connected group before the blast or gravity changes the grid.
    const available = new Set(specials);
    available.delete(p);""", """    const p = specials[0];
    comboLevel = 1;
    // SHOWER_COMBOS_PATCH: a power-up next to another one combines with it, just like swapping the two
    const mate = [[0, 1], [0, -1], [1, 0], [-1, 0]].map(([dr, dc]) => grid[p.r + dr]?.[p.c + dc]).find(q => q && q !== p && specials.includes(q));
    if (mate) {
      p.marked = 0; mate.marked = 0;
      await sleep(CASCADE_SPECIAL_DELAY_MS);
      if (inShower) { await waitForShowerBeat(); if (showerSkip) break; beginShowerEffect(); }
      await doCombo(p, mate, [mate.r, mate.c]);
      await resolve(null);
      continue;
    }
    // Collect the entire side-connected group before the blast or gravity changes the grid.
    const available = new Set(specials);
    available.delete(p);""")

rep("""style="left:${c.l}%;top:${c.t}%;width:${c.w}%;height:${c.h}%">`; }).join("") : "";""",
    """style="left:${c.l}%;top:${c.t}%;width:${c.w}%;height:${c.h}%">` + (a.kind === "water" ? `<span class="fdrip" aria-hidden="true" style="left:${c.l - c.w * .15}%;top:${c.t + c.h * .45}%;width:${c.w * 1.3}%;height:${c.h * .8}%"><b></b><i></i><i></i><i></i></span>` : ""); }).join("") : "";""")

css = """
.farm .fdrip{position:absolute;pointer-events:none;z-index:1}
.farm .fdrip b{position:absolute;left:10%;right:10%;top:30%;height:40%;border-radius:50%;border:2.5px solid rgba(255,255,255,.95);box-shadow:0 0 4px rgba(120,200,255,.9);animation:fripple 2.4s ease-out infinite}
.farm .fdrip i{position:absolute;top:-60%;width:7px;height:10px;border-radius:50% 50% 50% 50%/60% 60% 40% 40%;background:linear-gradient(#ffffff,#4fb3ea);box-shadow:0 0 0 1px rgba(255,255,255,.9),0 1px 3px rgba(0,60,120,.4);opacity:0;animation:fdrop 2.4s ease-in infinite}
.farm .fdrip i:nth-of-type(1){left:22%;animation-delay:.2s}.farm .fdrip i:nth-of-type(2){left:52%;animation-delay:1s}.farm .fdrip i:nth-of-type(3){left:76%;animation-delay:1.7s}
@keyframes fripple{0%{transform:scale(.35);opacity:.9}100%{transform:scale(1.15);opacity:0}}
@keyframes fdrop{0%{transform:translateY(0);opacity:0}15%{opacity:1}70%{transform:translateY(160%);opacity:1}80%,100%{transform:translateY(170%) scale(1.4,.3);opacity:0}}
@media (prefers-reduced-motion:reduce){.farm .fdrip b,.farm .fdrip i{animation:none}}
"""
rep(".farm .fbedbtn{z-index:4}", ".farm .fbedbtn{z-index:4}" + css)

path.write_text(src)
print("shower combos patch applied")
