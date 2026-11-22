"""Switch lifeline: "Tap two flowers" is no longer a spoken praise word; it shows as a small window like the
"Only 5 moves left!" reminder (no voice), with OK. After OK the player taps the two flowers to swap."""
from pathlib import Path
path = Path("www/index.html"); src = path.read_text()
if "SWITCH_TIP_PATCH" in src: print("switch tip already applied"); raise SystemExit(0)
def rep(a, b):
    global src
    if src.count(a) != 1: raise RuntimeError(f"patch-switch-tip: expected 1 of {a[:70]!r}, found {src.count(a)}")
    src = src.replace(a, b)
rep('boosterMode = "switch"; selected = null; swapFirst = null; syncTray(); praise("Tap two flowers");',
    'boosterMode = "switch"; selected = null; swapFirst = null; syncTray(); switchTip();')
rep("function movesLeftFly() {", """// SWITCH_TIP_PATCH: the Switch lifeline explains itself in a small window (no voice)
function switchTip() {
  const old = document.getElementById("swTip"); if (old) old.remove();
  reminderOpen = true;
  const fr = $("#frame").getBoundingClientRect();
  const dim = document.createElement("div"); dim.className = "remdim"; document.body.appendChild(dim);
  const el = document.createElement("div"); el.className = "mleft lltip"; el.id = "swTip"; el.setAttribute("role", "alertdialog");
  el.innerHTML = `Tap <b>two</b> flowers<small>They will swap places 🔀</small><button class="remok">OK</button>`;
  document.body.appendChild(el);
  const w = el.offsetWidth, h = el.offsetHeight, sx = fr.left + fr.width / 2 - w / 2, sy = fr.top + fr.height * .42 - h / 2;
  const at = (x, y, sc, r = 0) => `translate(${x}px,${y}px) scale(${sc}) rotate(${r}deg)`;
  el.animate([{ transform: at(sx, sy, .3), opacity: 0 }, { transform: at(sx, sy, 1.1, -3), opacity: 1, offset: .6 }, { transform: at(sx, sy, 1, 0), opacity: 1 }], { duration: 380, easing: "ease-out", fill: "forwards" });
  const ok = el.querySelector(".remok"); setTimeout(() => ok.focus(), 400);
  ok.onclick = e => {
    e.stopPropagation(); ok.disabled = true; dim.remove();
    const an = el.animate([{ transform: at(sx, sy, 1, 0), opacity: 1 }, { transform: at(sx, sy, .6, 0), opacity: 0 }], { duration: 220, easing: "ease-in", fill: "forwards" });
    an.onfinish = () => { el.remove(); reminderOpen = false; lastInput = T(); };
  };
}
function movesLeftFly() {""")
path.write_text(src); print("Switch: Tap two flowers window (no voice)")
