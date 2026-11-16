"""The first planting in the garden is always possible.

The guided first planting only lets you tap the highlighted spot, the Cream Daisy and Plant. If the player had
already spent the garden's starting coins (for example as a gift to a friend before ever opening the garden),
"Not enough coins" appeared and the guide kept them stuck. Now, when the guide starts and the coins can't pay
for the daisy, the coins are topped up to its price ("Your first flower is on us").
Runs after patch-garden-tutorial.py (it edits the final www/index.html)."""
from pathlib import Path

path = Path("www/index.html")
src = path.read_text()
if "TUTORIAL_COINS_PATCH" in src:
    print("tutorial coins patch already applied"); raise SystemExit(0)
before = """  const DAISY = "daisy__cream";"""
if src.count(before) != 1:
    raise RuntimeError("patch-tutorial-coins: garden tutorial code changed; review before building")
after = """  const DAISY = "daisy__cream";
  { // TUTORIAL_COINS_PATCH: never get stuck in the guide without coins for the first daisy
    const need = (SEEDS[DAISY] && SEEDS[DAISY].cost) || 25;
    if (f.coins < need) { f.coins = need; persist(); setTimeout(() => { const d = document.createElement("div"); d.className = "gtdone"; d.innerHTML = `<b>🎁 Your first flower is on us!</b><span>Here are ${FC_SVG}${need} to plant it.</span>`; root.appendChild(d); setTimeout(() => d.classList.add("out"), 3000); setTimeout(() => d.remove(), 3600); }, 300); }
  }"""
path.write_text(src.replace(before, after))
print("First garden planting can always be paid")
