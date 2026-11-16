"""Bring players to the garden, teach the first planting, and show water when watering.

1) After level 10 (and once only), a small window appears on top of the level-complete window:
   "Plant, harvest and arrange flowers in your garden!" with a picture of the garden and
   "Visit garden" / "Do it later". Players who already use the garden don't see it.
2) The first time the garden opens: a short guided planting. Only the highlighted thing can be tapped:
   the flower bed (soil) -> an empty spot -> Cream Daisy -> Plant. Then: "It blooms in 5 minutes."
3) Watering a plant shows water drops falling on it and a splash on the soil.
Runs after patch-garden-plants.py and patch-share-garden.py (it edits the final www/index.html).
"""
from pathlib import Path

path = Path("www/index.html")
src = path.read_text()
if "GARDEN_TUTORIAL_PATCH" in src:
    print("garden tutorial patch already applied"); raise SystemExit(0)

def rep(before, after):
    global src
    n = src.count(before)
    if n != 1:
        raise RuntimeError(f"patch-garden-tutorial: expected 1 of: {before[:80]!r}, found {n}")
    src = src.replace(before, after)

# --- shared code: promo window, guided planting, water drops -------------------------------------------
code = r"""// GARDEN_TUTORIAL_PATCH
function gardenPromo(winEl) {
  try {
    if (levelIdx < 9 || save.gardenPromo || (save.farm && save.farm.seen)) return;
    save.gardenPromo = 1; persist();
    setTimeout(() => {
      if (!winEl.isConnected) return;
      const pic = window.GARDEN_OVERVIEW || (typeof FARM_IMG !== "undefined" && FARM_IMG.overview_nh) || "";
      const d = document.createElement("div"); d.className = "gpromo"; d.setAttribute("role", "dialog"); d.setAttribute("aria-label", "Your garden");
      d.innerHTML = `<div class="gpcard"><div class="gppic" style="background-image:url(${pic})"></div><h3>Plant, harvest and arrange flowers in your garden!</h3>
        <div class="gpbtns"><button class="btn" id="gpGo">🌷 Visit garden</button><button class="btn alt" id="gpLater">Do it later</button></div></div>`;
      document.body.appendChild(d); sfx("pick"); track("garden_promo_show", {});
      d.querySelector("#gpLater").onclick = () => { d.remove(); track("garden_promo_later", {}); };
      d.querySelector("#gpGo").onclick = () => { d.remove(); track("garden_promo_go", {}); const g = winEl.querySelector("#wGarden"); if (g) g.click(); };
    }, 1400);
  } catch (e) {}
}
function gardenTutorial(root, f) {
  if (f.tut) return;
  const anyPlant = [...f.beds, ...Object.values(f.areas || {})].some(s => (s.plots || []).some(Boolean));
  if (anyPlant) { f.tut = 1; persist(); return; }
  const DAISY = "daisy__cream";
  const ui = document.createElement("div"); ui.className = "gtut"; ui.innerHTML = `<div class="gtring"></div><div class="gthand" aria-hidden="true">👆</div><div class="gttip" role="status"></div>`;
  root.appendChild(ui);
  const ring = ui.querySelector(".gtring"), hand = ui.querySelector(".gthand"), tip = ui.querySelector(".gttip");
  let target = null, timer = 0;
  const vis = e => e && e.offsetParent && e.getBoundingClientRect().width > 0;
  const tappable = e => { if (!vis(e)) return false; const r = e.getBoundingClientRect(), h = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2); return !!h && (e === h || e.contains(h) || h.closest(".gtut")); };
  const step = () => {
    if (!root.isConnected) { stop(); return; }
    const sheet = root.querySelector(".fsheet"), open = sheet && !sheet.hidden;
    let t = null, msg = "";
    if ([...f.beds].some(s => (s.plots || []).some(Boolean))) { finish(); return; }
    if (open) {
      const plant = root.querySelector("#sPlant"), seed = root.querySelector(`.fseed[data-k="${DAISY}"]`);
      if (vis(plant)) { t = plant; msg = "Tap <b>Plant</b>"; }
      else if (seed) { if (!vis(seed) || seed.getBoundingClientRect().bottom > innerHeight - 90) seed.scrollIntoView({ block: "center" }); t = seed; msg = "Tap <b>Cream Daisy</b>"; }
      else if (root.querySelector("[data-x]")) { t = root.querySelector(".fsheet [data-x]"); msg = ""; }
    } else {
      const plot = [...root.querySelectorAll(".fplot.empty")].find(tappable), bed = root.querySelector('.fbedbtn[data-b="0"]');
      if (plot) { t = plot; msg = "Tap the soil to plant"; }
      else if (vis(bed)) { t = bed; msg = "Tap the soil to plant"; }
    }
    target = t;
    if (!t) { ui.hidden = true; return; }
    ui.hidden = false;
    const r = t.getBoundingClientRect(), pad = 6;
    Object.assign(ring.style, { left: r.left - pad + "px", top: r.top - pad + "px", width: r.width + pad * 2 + "px", height: r.height + pad * 2 + "px" });
    Object.assign(hand.style, { left: r.left + r.width / 2 - 6 + "px", top: r.bottom - 10 + "px" });
    tip.innerHTML = msg; tip.hidden = !msg;
    const below = r.bottom + 120 < innerHeight;
    Object.assign(tip.style, below ? { top: r.bottom + 58 + "px", bottom: "" } : { top: "", bottom: innerHeight - r.top + 14 + "px" });
  };
  // only the highlighted thing can be tapped while the guide is showing
  const guard = e => { if (!target || ui.hidden) return; if (target.contains(e.target)) return; e.preventDefault(); e.stopPropagation(); };
  ["pointerdown", "click", "touchstart"].forEach(ev => document.addEventListener(ev, guard, true));
  function stop() { clearInterval(timer); ["pointerdown", "click", "touchstart"].forEach(ev => document.removeEventListener(ev, guard, true)); ui.remove(); }
  function finish() {
    stop(); f.tut = 1; persist(); track("garden_tutorial_done", {});
    const d = document.createElement("div"); d.className = "gtdone"; d.innerHTML = `<b>🌱 Well done!</b><span>Your daisy blooms in 5 minutes. Come back and tap it to pick it.</span>`;
    root.appendChild(d); setTimeout(() => d.classList.add("out"), 4200); setTimeout(() => d.remove(), 4800);
  }
  timer = setInterval(step, 250); step();
}
function waterFx(r) {
  try {
    const d = document.createElement("div"); d.className = "wfx"; d.setAttribute("aria-hidden", "true");
    Object.assign(d.style, { left: r.left + "px", top: r.top + "px", width: r.width + "px", height: r.height + "px" }); d.style.setProperty("--h", Math.round(r.height * .75) + "px");
    d.innerHTML = '<span class="wcan">🚿</span>' + Array.from({ length: 9 }, (_, i) => `<i style="left:${18 + (i % 5) * 15}%;animation-delay:${(i * .09).toFixed(2)}s"></i>`).join("") + "<b></b><b></b>";
    document.body.appendChild(d); setTimeout(() => d.remove(), 1700);
  } catch (e) {}
}
let mapOpen = null;"""
rep("let mapOpen = null;", code)

# promo on the level-complete window (the Garden button line is added by patch-share-garden.py)
rep("""      el.querySelector("#wGarden").onclick = () => leaveWin(() => showMyGarden(() => startLevel(Math.min(LEVELS.length - 1, levelIdx + 1))));""",
    """      el.querySelector("#wGarden").onclick = () => leaveWin(() => showMyGarden(() => startLevel(Math.min(LEVELS.length - 1, levelIdx + 1))));
      gardenPromo(el);""")

# first garden visit: short welcome, then the guided planting
rep("""<p>Tap a flower bed, tap empty soil and choose a flower. Wait for it to bloom, then pick it for more coins. Rare flowers take longer but earn more.</p><p>Here are ${FC_SVG}<b>100</b> and 💧<b>5</b> to start!</p><div class="btns"><button class="btn" data-x>Let's plant!</button></div>`); }""",
    """<p>Here are ${FC_SVG}<b>100</b> and 💧<b>5</b> to start!</p><div class="btns"><button class="btn" data-x>Let's plant!</button></div>`); setTimeout(() => gardenTutorial(el, f), 400); }""")

# watering: drops on the plant
rep("""f.water--; p.ms -= l * .2; persist(); sheet.hidden = true; sfx("ice"); render(); gainXP(1); };""",
    """f.water--; p.ms -= l * .2; persist(); sheet.hidden = true; sfx("ice"); { const pb = btn && btn.getBoundingClientRect(); if (pb && pb.width) waterFx(pb); } render(); gainXP(1); };""")

css = """
.gpromo{position:fixed;inset:0;z-index:60;display:grid;place-items:center;padding:16px;background:rgba(60,20,40,.45);animation:gpin .35s ease-out}
@keyframes gpin{from{opacity:0}}
.gpcard{width:min(340px,100%);background:#fffaf3;border-radius:26px;padding:16px 16px 18px;text-align:center;box-shadow:0 18px 44px rgba(60,20,40,.4);animation:gppop .45s cubic-bezier(.3,1.5,.5,1)}
@keyframes gppop{from{transform:scale(.6) translateY(30px)}}
.gppic{height:170px;border-radius:18px;background-size:cover;background-position:50% 30%;box-shadow:inset 0 0 0 3px #fff,0 4px 12px rgba(60,40,20,.2)}
.gpcard h3{margin:14px 6px 12px;font:800 22px/1.2 var(--display, "Baloo 2", sans-serif);color:#5a2e44;text-wrap:balance}
.gpbtns{display:flex;flex-direction:column;gap:8px}
.gtut{position:fixed;inset:0;z-index:40;pointer-events:none}
.gtring{position:fixed;border-radius:16px;box-shadow:0 0 0 4px #ffd23a,0 0 0 9999px rgba(40,15,30,.55);transition:all .25s ease}
.gthand{position:fixed;font-size:44px;filter:drop-shadow(0 3px 4px rgba(0,0,0,.35));animation:gthand 1s ease-in-out infinite;transition:left .25s,top .25s}
@keyframes gthand{50%{transform:translateY(-14px)}}
.gttip{position:fixed;left:50%;transform:translateX(-50%);max-width:88vw;background:#fff;color:#5a2e44;border-radius:18px;padding:12px 18px;font:800 20px/1.25 var(--display, "Baloo 2", sans-serif);text-align:center;box-shadow:0 8px 22px rgba(0,0,0,.3);white-space:nowrap}
.gtdone{position:fixed;left:50%;bottom:110px;transform:translateX(-50%);z-index:41;width:min(330px,88vw);background:#fff;border-radius:20px;padding:14px 16px;text-align:center;box-shadow:0 10px 28px rgba(0,0,0,.3);display:flex;flex-direction:column;gap:4px;font:700 16px/1.3 var(--body, Nunito, sans-serif);color:#5a3a20;animation:gppop .4s cubic-bezier(.3,1.5,.5,1);transition:opacity .5s}
.gtdone b{font:800 20px var(--display, "Baloo 2", sans-serif);color:#2f8a3e}.gtdone.out{opacity:0}
.wfx{position:fixed;z-index:45;pointer-events:none}
.wfx .wcan{position:absolute;left:50%;top:-38%;font-size:30px;transform:translateX(-10%) rotate(-25deg);animation:wcan 1.6s ease-in-out both}
@keyframes wcan{0%{opacity:0;transform:translate(10%,-20%) rotate(0)}15%,75%{opacity:1;transform:translateX(-10%) rotate(-25deg)}100%{opacity:0}}
.wfx i{position:absolute;top:0;width:8px;height:12px;border-radius:50% 50% 50% 50%/60% 60% 40% 40%;background:linear-gradient(#fff,#47a9e6);box-shadow:0 0 0 1px rgba(255,255,255,.9);opacity:0;animation:wdrop .8s ease-in forwards}
@keyframes wdrop{0%{opacity:0;transform:translateY(0)}15%{opacity:1}85%{opacity:1;transform:translateY(calc(var(--h,60px) * 1))}100%{opacity:0;transform:translateY(70px) scale(1.5,.3)}}
.wfx b{position:absolute;left:15%;right:15%;bottom:8%;height:22%;border-radius:50%;border:3px solid rgba(120,200,255,.95);opacity:0;animation:wsplash .9s ease-out .55s forwards}
.wfx b+b{animation-delay:.8s}
@keyframes wsplash{0%{opacity:.95;transform:scale(.3)}100%{opacity:0;transform:scale(1.25)}}
@media (prefers-reduced-motion:reduce){.gthand,.wfx i,.wfx b,.wfx .wcan{animation:none}}
"""
rep(".farm .fbedbtn{z-index:4}", ".farm .fbedbtn{z-index:4}" + css)

path.write_text(src)
print("garden tutorial patch applied")
