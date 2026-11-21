"""Album: "🌱 Plant all I need" on a bouquet that is not made yet.
Plants every missing flower in one tap: what the bouquet needs, minus what is in the Basket and what is already
growing, each in a free spot of the right kind (Bed, Pond, Pergola, Tree). It plants what it can and says plainly
why the rest was not planted: locked seeds (Garden Level / chapter), no free spot of that kind, not enough coins
or water. A summary with the cost comes first; nothing is planted before "Plant". Runs after patch-flower-ask.py."""
from pathlib import Path
path = Path("www/index.html"); src = path.read_text()
if "PLANT_ALL_PATCH" in src: print("plant all already added"); raise SystemExit(0)
def rep(a, b):
    global src
    if src.count(a) != 1: raise RuntimeError(f"patch-plant-all: expected 1 of {a[:70]!r}, found {src.count(a)}")
    src = src.replace(a, b)

# the button on an unmade bouquet
rep("""<p class="fasknote" id="sAskNote"></p>`}
      <div class="btns"><button class="btn alt" id="sBack">Back</button></div>`, c => { c.querySelector("#sBack").onclick = () => albumSheet();""",
    """<p class="fasknote" id="sAskNote"></p>`}
      <div class="btns col">${made || !plantNeed(b).length ? "" : `<button class="btn" id="sPlantAll">🌱 Plant all I need</button>`}<button class="btn alt" id="sBack">Back</button></div>`, c => { c.querySelector("#sBack").onclick = () => albumSheet();
        const pa = c.querySelector("#sPlantAll"); if (pa) pa.onclick = () => plantAll(no);""")

code = r'''
  // PLANT_ALL_PATCH: plant every missing flower of a bouquet in one tap
  function plantNeed(b) {   // [[seed, how many more to plant]]: needed - in the Basket - already growing
    const growing = {}; [...f.beds, ...Object.values(f.areas || {})].forEach(s => s.open && s.plots.forEach(p => { if (p && p.b) growing[p.b] = (growing[p.b] || 0) + 1; }));
    return b.ing.map(([q, id]) => [id, q - (f.inv[id] || 0) - (growing[id] || 0)]).filter(([id, n]) => n > 0 && SEEDS[id]);
  }
  function freeSpots(kind) {   // free plots of one kind, in garden order
    const out = [];
    if (kind === "ground") f.beds.forEach(s => { if (s.open) s.plots.forEach((p, i) => { if (!p) out.push([s, i]); }); });
    else if (XAREA_ON()) Object.entries(XAREAS).forEach(([k, a]) => { const s = f.areas[k]; if (a.kind === kind && s && s.open) s.plots.forEach((p, i) => { if (!p) out.push([s, i]); }); });
    return out;
  }
  const PLACE_NAME = { ground: "Bed", water: "Pond", hanging: "Pergola", tree: "Tree" };
  function plantPlan(b) {
    const lv = farmLevel(f.xp).lv, spots = {}, plan = [], why = [];
    let coins = f.coins, water = f.water, cost = 0, wcost = 0;
    for (const [id, n] of plantNeed(b)) {
      const sd = SEEDS[id], kind = sd.t || "ground";
      if (chLocked(sd)) { why.push(`🔒 <b>${sd.n}</b> ×${n}: finish puzzle chapter ${sd.ch} to unlock these seeds.`); continue; }
      if (sd.lv > lv) { why.push(`🔒 <b>${sd.n}</b> ×${n}: unlocks at Garden Level ${sd.lv} (you are Level ${lv}).`); continue; }
      if (!(kind in spots)) spots[kind] = freeSpots(kind);
      let k = 0, noSpot = 0, noCoin = 0, noWater = 0;
      for (let j = 0; j < n; j++) {
        if (!spots[kind].length) { noSpot++; continue; }
        if (coins < sd.cost) { noCoin++; continue; }
        if (water < (sd.w || 0)) { noWater++; continue; }
        const [s, i] = spots[kind].shift(); coins -= sd.cost; water -= sd.w || 0; cost += sd.cost; wcost += sd.w || 0; plan.push([s, i, id]); k++;
      }
      const place = PLACE_NAME[kind] || "spot";
      if (noSpot) why.push(`🪴 <b>${sd.n}</b> ×${noSpot}: no free ${place} spot. ${kind === "ground" ? "Pick ready flowers or open another bed." : XAREA_ON() && Object.values(XAREAS).some(a => a.kind === kind) ? `Pick ready flowers or open a ${place}.` : `You don't have a ${place} yet.`}`);
      if (noCoin) why.push(`${FC_SVG} <b>${sd.n}</b> ×${noCoin}: not enough coins (${FC_SVG}${sd.cost} each).`);
      if (noWater) why.push(`💧 <b>${sd.n}</b> ×${noWater}: not enough water (💧${sd.w} each).`);
    }
    return { plan, why, cost, wcost };
  }
  function plantAll(no) {
    const b = BQ.find(x => x.no === no); if (!b) return;
    const { plan, why, cost, wcost } = plantPlan(b);
    const count = {}; plan.forEach(([, , id]) => { count[id] = (count[id] || 0) + 1; });
    const list = Object.entries(count).map(([id, n]) => `<div><img alt="" src="${brImg(id)}"><span>${SEEDS[id].n}</span><b>×${n}</b></div>`).join("");
    const whyHTML = why.length ? `<div class="fpawhy"><b>${plan.length ? "Not planted:" : "Nothing can be planted right now:"}</b>${why.map(w => `<p>${w}</p>`).join("")}</div>` : "";
    const poor = why.some(w => w.includes("not enough coins") || w.includes("not enough water"));
    if (!plan.length) {
      sheetShow(`<h3>🌱 ${b.n}</h3>${whyHTML}<div class="btns col">${poor ? `<button class="btn" id="sPlay">▶ Play a level</button>` : ""}<button class="btn alt" id="sBack">Back</button></div>`,
        c => { c.querySelector("#sBack").onclick = () => stickerTap(no); const pl = c.querySelector("#sPlay"); if (pl) pl.onclick = close; });
      return;
    }
    sheetShow(`<h3>🌱 Plant ${plan.length} seed${plan.length > 1 ? "s" : ""}?</h3><p class="fsub">For ${b.n}</p>
      <div class="fneedl fpalist">${list}</div>
      <p class="fbig">Cost: ${FC_SVG}<b>${cost}</b>${wcost ? ` · 💧<b>${wcost}</b>` : ""}</p>${whyHTML}
      <div class="btns col"><button class="btn" id="sPlantGo">🌱 Plant</button><button class="btn alt" id="sBack">Back</button></div>`,
      c => { c.querySelector("#sBack").onclick = () => stickerTap(no);
        c.querySelector("#sPlantGo").onclick = () => {
          const again = plantPlan(b); if (!again.plan.length) { plantAll(no); return; }
          for (const [s, i, id] of again.plan) { const sd = SEEDS[id]; if (s.plots[i]) continue;
            f.coins -= sd.cost; f.water -= sd.w || 0; s.plots[i] = { b: id, at: Date.now(), ms: Math.round(sd.min * 60000 * growMul(f)) }; }
          persist(); sfx("dirt"); track("garden_plant_all", { n: again.plan.length, bouquet: no }); render();
          sheetShow(`<h3>🌱 Planted ${again.plan.length} seed${again.plan.length > 1 ? "s" : ""}!</h3><p>They are growing in your garden. Come back when they bloom.</p>${again.why.length ? `<div class="fpawhy"><b>Not planted:</b>${again.why.map(w => `<p>${w}</p>`).join("")}</div>` : ""}
            <div class="btns"><button class="btn" data-x>OK</button></div>`);
        }; });
  }
'''
rep("\n  // SHARE_GARDEN_PATCH: a 1080 x 1080 picture of a made bouquet, to save or share", code + "\n  // SHARE_GARDEN_PATCH: a 1080 x 1080 picture of a made bouquet, to save or share")
css = """
/* PLANT_ALL_PATCH */
.fpawhy{margin:10px 0 4px;padding:10px 12px;border-radius:14px;background:#fff4e5;box-shadow:inset 0 0 0 2px #ffd9a8;text-align:left;font:700 15px/1.35 var(--body);color:#7a4a1a}
.fpawhy>b{display:block;margin-bottom:4px;color:#a0521a}
.fpawhy p{margin:4px 0}
.fpawhy svg{width:1em;height:1em;vertical-align:-.12em}
.fpalist{margin-top:6px}
</style>"""
i = src.find("</style>", src.find(".fneedl{"))
src = src[:i] + css + src[i + len("</style>"):]
path.write_text(src); print("Plant all I need added")
