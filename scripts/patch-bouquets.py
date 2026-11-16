"""Garden basket and bouquet album (36 stickers in 3 albums), made for older players: few words, few taps.

- Tap a flower in bloom: it flies into the 🧺 Basket (no menu). "🌸 Pick all" picks every flower in bloom.
- Basket: pictures with counts. Tap one to sell one; "Sell extras" sells everything not needed for a bouquet.
  Flowers kept for bouquets show 💐 and are never sold by mistake.
- Album: 12 stickers per page. Each unmade sticker shows its flowers with have/need counts;
  when all are in the basket it shows "Make" — one tap makes it (+5 XP, +1 water). A full album gives a gift.
Runs after patch-garden-plants.py (it edits the final www/index.html). Sticker art and recipes: www/bouquets.js.
"""
from pathlib import Path

path = Path("www/index.html")
src = path.read_text()
if "BOUQUETS_PATCH" in src:
    print("bouquets patch already applied"); raise SystemExit(0)

def rep(before, after, count=1):
    global src
    n = src.count(before)
    if n != count:
        raise RuntimeError(f"patch-bouquets: expected {count} of: {before[:80]!r}, found {n}")
    src = src.replace(before, after)

rep('<script src="garden-plants.js"></script>', '<script src="garden-plants.js"></script>\n<script src="bouquets.js"></script>')

# --- tapping a flower in bloom picks it into the basket ---------------------------------------
rep("""      const gain0 = Math.round(sd.gain * beeBonus(f));
      sheetShow(`<img class="fpic" alt="" src="${plotImg(p, st)}"><div class="frare r${sd.r}">${sd.r}</div><h3>${sd.n} is in bloom!</h3>
        <div class="btns col"><button class="btn" id="sSell">${FC_SVG} Sell · +${gain0}${sd.t === "water" ? " · 💧+1" : ""} <small>(+${sellXP(sd)} XP)</small></button>
        <button class="btn alt" id="sMove">↔ Move · ${FC_SVG}${MOVE_COST}</button><button class="btn alt" data-x>Keep it</button></div>`,
        c => { c.querySelector("#sMove").onclick = startMove; c.querySelector("#sSell").onclick = () => { sheet.hidden = true; sellPlot(i, btn); }; });""",
    """      pickPlot(i, btn);""")

# --- buttons: Basket and Album, and "Pick all" when flowers are in bloom ------------------------
rep("""      btns.innerHTML = `<button class="btn alt" id="fHouse">🏠 House</button><button class="btn alt" id="fStore">🛍 Store</button><button class="btn" id="fPlay">▶ Play</button>`;""",
    """      btns.innerHTML = (window.BOUQUETS ? `<button class="btn bk" id="fBasket">🧺 Basket <b>${invCount()}</b></button><button class="btn bk" id="fAlbum">💐 Album${anyMake() ? `<i class="fdot"></i>` : ""}</button>` : "") + `<button class="btn alt" id="fHouse">🏠 House</button><button class="btn alt" id="fStore">🛍 Store</button><button class="btn" id="fPlay">▶ Play</button>`;
      { const nr = readyAll(); if (nr && window.BOUQUETS) hint.innerHTML = `<button class="fpickall" id="fPick">🌸 Pick all · ${nr}</button>`; }""")
rep("""      btns.querySelector("#fHouse").onclick = houseSheet; btns.querySelector("#fStore").onclick = storeSheet; btns.querySelector("#fPlay").onclick = close;""",
    """      btns.querySelector("#fHouse").onclick = houseSheet; btns.querySelector("#fStore").onclick = storeSheet; btns.querySelector("#fPlay").onclick = close;
      { const a = btns.querySelector("#fBasket"), b = btns.querySelector("#fAlbum"), c = hint.querySelector("#fPick"); if (a) a.onclick = basketSheet; if (b) b.onclick = () => albumSheet(); if (c) c.onclick = pickAll; }""")
rep("""btns.innerHTML = moving ? `<button class="btn alt" id="fCancel">✕ Cancel move</button>` : `<button class="btn alt" id="fBack">⬅ Back</button>`;""",
    """btns.innerHTML = moving ? `<button class="btn alt" id="fCancel">✕ Cancel move</button>` : `<button class="btn alt" id="fBack">⬅ Back</button>` + (window.BOUQUETS ? `<button class="btn bk" id="fBasket">🧺 <b>${invCount()}</b></button>` : "");
      { const a = btns.querySelector("#fBasket"); if (a) a.onclick = basketSheet; }""")

code = r'''
  // BOUQUETS_PATCH: basket (picked flowers) and the bouquet sticker album
  f.inv = f.inv || {}; f.stk = f.stk || {}; f.albDone = f.albDone || {};
  const BQ = window.BOUQUETS || [], BQA = window.BOUQUET_ALBUMS || [];
  const ALBUM_GIFT = [[5, 5, 300], [10, 10, 1000], [25, 20, 3000]];   // diamonds, water, coins for a full album
  const PLACE = { ground: "🌱 Bed", water: "💧 Pond", hanging: "🌿 Pergola", tree: "🌳 Tree" };
  const invCount = () => Object.keys(f.inv).reduce((a, k) => a + (SEEDS[k] ? f.inv[k] : 0), 0);
  const needFor = () => { const n = {}; BQ.forEach(b => { if (!f.stk[b.no]) b.ing.forEach(([q, id]) => { n[id] = Math.max(n[id] || 0, q); }); }); return n; };   // keep enough for one bouquet; the rest are extras
  const canMake = b => !f.stk[b.no] && b.ing.every(([q, id]) => (f.inv[id] || 0) >= q);
  const anyMake = () => BQ.some(canMake);
  const sellPrice = id => Math.round(SEEDS[id].gain * beeBonus(f));
  const readyAll = () => [...f.beds, ...Object.values(f.areas || {})].reduce((n, s) => n + (s.open ? s.plots.filter(p => plotState(p) === "ready").length : 0), 0);
  function flyToBasket(from, img) {
    try {
      const t = el.querySelector("#fBasket"); if (!t || !from) return;
      const r = from.getBoundingClientRect(), q = t.getBoundingClientRect(), im = document.createElement("img");
      im.src = img; im.alt = ""; im.className = "ffly"; im.style.left = (r.left + r.width / 2 - 26) + "px"; im.style.top = (r.top + r.height / 2 - 26) + "px"; el.appendChild(im);
      requestAnimationFrame(() => requestAnimationFrame(() => { im.style.transform = `translate(${q.left + q.width / 2 - r.left - r.width / 2}px,${q.top + q.height / 2 - r.top - r.height / 2}px) scale(.35)`; im.style.opacity = ".4"; }));
      setTimeout(() => im.remove(), 800);
    } catch (e) {}
  }
  function pickPlot(i, btn) {
    const s = holder(), p = s.plots[i]; if (!p || plotState(p) !== "ready") return;
    const sd = SEEDS[p.b], xp = sellXP(sd), wb = sd.t === "water" ? 1 : 0;
    s.plots[i] = null; f.inv[p.b] = (f.inv[p.b] || 0) + 1; f.water += wb; persist(); sfx("pick"); track("garden_harvest", { flower: p.b });
    flyToBasket(btn, brImg(p.b)); floatAt(btn, `🧺 +1${wb ? " 💧+1" : ""}<small>+${xp} XP</small>`);
    const reopen = area && !sheet.hidden && f.areas[area].plots.length > 1 ? area : null;
    render(); if (reopen) openArea(reopen); gainXP(xp);
  }
  function pickAll() {
    let n = 0, xp = 0, w = 0;
    const take = s => { if (s.open) s.plots.forEach((p, i) => { if (p && plotState(p) === "ready") { const sd = SEEDS[p.b]; f.inv[p.b] = (f.inv[p.b] || 0) + 1; xp += sellXP(sd); if (sd.t === "water") w++; s.plots[i] = null; n++; } }); };
    f.beds.forEach(take); Object.values(f.areas || {}).forEach(take); if (!n) return;
    f.water += w; persist(); sfx("create"); track("garden_pick_all", { n });
    const from = hint.querySelector("#fPick") || hint; flyToBasket(from, FARM_IMG.bud); floatAt(from, `🧺 +${n}${w ? ` 💧+${w}` : ""}<small>+${xp} XP</small>`);
    render(); gainXP(xp);
  }
  function basketSheet() {
    area = null;
    const need = needFor(), ids = Object.keys(f.inv).filter(k => f.inv[k] > 0 && SEEDS[k]).sort((a, b) => (need[b] ? 1 : 0) - (need[a] ? 1 : 0));
    let extra = 0; ids.forEach(k => { extra += Math.max(0, f.inv[k] - (need[k] || 0)) * sellPrice(k); });
    sheetShow(`<h3>🧺 Basket</h3>${ids.length ? `<div class="fbask">${ids.map(k => { const keep = Math.min(f.inv[k], need[k] || 0), more = f.inv[k] - keep;
        return `<button class="fbi${more ? "" : " kept"}" data-k="${k}" aria-label="${SEEDS[k].n}, ${f.inv[k]}${keep ? `, ${keep} kept for bouquets` : ""}"><img alt="" src="${brImg(k)}"><span class="fbn">${SEEDS[k].n}</span><b>×${f.inv[k]}</b>${keep ? `<i>💐${keep}</i>` : ""}<small>${more ? `${FC_SVG}${sellPrice(k)}` : "💐"}</small></button>`; }).join("")}</div>`
        : `<p class="fempty">🌸 → 🧺</p>`}
      <div class="btns col">${extra ? `<button class="btn" id="sSellX">${FC_SVG} Sell extras · +${extra}</button>` : ""}<button class="btn alt" id="sAlb">💐 Album</button><button class="btn alt" data-x>Close</button></div>`,
      c => { const sx = c.querySelector("#sSellX"); if (sx) sx.onclick = sellExtras; c.querySelector("#sAlb").onclick = () => albumSheet(); c.querySelectorAll(".fbi").forEach(b => b.onclick = () => sellOne(b.dataset.k, b)); });
  }
  function sellOne(k, b) {
    if ((f.inv[k] || 0) <= (needFor()[k] || 0)) { b.classList.remove("nope"); void b.offsetWidth; b.classList.add("nope"); return; }   // kept for a bouquet
    const g = sellPrice(k); f.inv[k]--; f.coins += g; persist(); sfx("create"); track("garden_sell_flower", { flower: k }); floatAt(b, `+${g} ${FC_SVG}`); bar(); render(); basketSheet();
  }
  function sellExtras() {
    const need = needFor(); let g = 0;
    Object.keys(f.inv).forEach(k => { const x = SEEDS[k] ? Math.max(0, f.inv[k] - (need[k] || 0)) : 0; if (x) { g += x * sellPrice(k); f.inv[k] -= x; } });
    if (!g) return; f.coins += g; persist(); sfx("create"); track("garden_sell_extras", { coins: g }); bar(); render(); basketSheet(); floatAt(el.querySelector(".fcbuy"), `+${g} ${FC_SVG}`);
  }
  let albPage = 0;
  function albumSheet(pg) {
    area = null; if (pg != null) albPage = Math.max(0, Math.min(BQA.length - 1, pg));
    const list = BQ.filter(b => b.album === albPage), A = BQA[albPage] || { n: "" }, done = list.filter(b => f.stk[b.no]).length;
    sheetShow(`<div class="falbh"><button class="fpg" id="aPrev" ${albPage ? "" : "disabled"} aria-label="Previous album">◀</button><div><h3>${A.n}</h3><small>💐 ${done} / ${list.length}</small></div><button class="fpg" id="aNext" ${albPage < BQA.length - 1 ? "" : "disabled"} aria-label="Next album">▶</button></div>
      <div class="falb">${list.map(b => { const made = !!f.stk[b.no], ok = canMake(b);
        return `<button class="fstk${made ? " made" : ok ? " ready" : ""}" data-no="${b.no}" aria-label="${b.n}${made ? ", made" : ok ? ", ready to make" : ""}"><img class="fsimg" alt="" src="${b.img}">${made ? "" : `<span class="fing">${b.ing.map(([q, id]) => `<i class="${(f.inv[id] || 0) >= q ? "ok" : ""}"><img alt="" src="${brImg(id)}"><b>${Math.min(f.inv[id] || 0, q)}/${q}</b></i>`).join("")}</span>`}${ok ? `<em>Make</em>` : ""}</button>`; }).join("")}</div>
      <div class="btns"><button class="btn alt" data-x>Close</button></div>`,
      c => { c.querySelector("#aPrev").onclick = () => albumSheet(albPage - 1); c.querySelector("#aNext").onclick = () => albumSheet(albPage + 1);
        c.querySelectorAll(".fstk").forEach(b => b.onclick = () => stickerTap(+b.dataset.no)); });
  }
  function stickerTap(no) {
    const b = BQ.find(x => x.no === no); if (!b) return;
    if (canMake(b)) { makeBouquet(b); return; }
    const made = !!f.stk[no];
    sheetShow(`<img class="fpic fstkpic${made ? "" : " grey"}" alt="" src="${b.img}"><h3>${b.n}</h3><p class="fsub">${b.occ}${made ? " · ✓" : ""}</p>
      ${made ? "" : `<div class="fneedl">${b.ing.map(([q, id]) => { const h = f.inv[id] || 0, sd = SEEDS[id]; return `<div class="${h >= q ? "ok" : ""}"><img alt="" src="${brImg(id)}"><span>${sd.n}<small>${PLACE[sd.t] || ""}</small></span><b>${Math.min(h, q)}/${q}</b></div>`; }).join("")}</div>`}
      <div class="btns"><button class="btn alt" id="sBack">Back</button></div>`, c => c.querySelector("#sBack").onclick = () => albumSheet());
  }
  function makeBouquet(b) {
    b.ing.forEach(([q, id]) => { f.inv[id] -= q; }); f.stk[b.no] = 1; f.water += 1; persist(); sfx("win"); track("garden_bouquet", { no: b.no });
    const full = BQ.filter(x => x.album === b.album).every(x => f.stk[x.no]) && !f.albDone[b.album];
    bar(); render();
    sheetShow(`<img class="fpic fstkpic pop" alt="" src="${b.img}"><h3>${b.n}</h3><p class="fbig">💐 +5 XP · 💧+1</p><div class="btns"><button class="btn" id="sOk">Lovely!</button></div>`,
      c => c.querySelector("#sOk").onclick = () => full ? albumGift(b.album) : albumSheet(b.album));
    gainXP(5);
  }
  function albumGift(a) {
    const [g, w, c] = ALBUM_GIFT[a] || [0, 0, 0]; f.albDone[a] = 1; f.water += w; f.coins += c; persist(); if (g) addGems(g); sfx("win"); track("garden_album_done", { album: a }); bar(); render();
    sheetShow(`<h3>🎉 ${(BQA[a] || {}).n}</h3><p>Album complete!</p><p class="fbig"><span class="fgem">${GEM_SVG}</span><b>+${g}</b> · 💧<b>+${w}</b> · ${FC_SVG}<b>+${c}</b></p><div class="btns"><button class="btn" data-x>Thank you!</button></div>`);
  }
'''
rep("  function sheetShow(html, wire) {", code + "  function sheetShow(html, wire) {")

css = """
.farm .fbtns{flex-wrap:wrap}.farm .fbtns .btn{flex:1 1 28%}.farm .fbtns .btn.bk{flex:1 1 40%;position:relative;background:linear-gradient(180deg,#fff8e8,#ffe9c2);color:#6b4a1e;box-shadow:0 0 0 2px #f2cf8a,0 4px 0 #e0b76a}
.farm .fbtns .btn.bk b{background:#e8467e;color:#fff;border-radius:999px;padding:1px 8px;margin-left:4px;font-size:15px}
.farm .fdot{position:absolute;right:10px;top:8px;width:12px;height:12px;border-radius:50%;background:#e8467e;box-shadow:0 0 0 2px #fff;animation:fdotp 1.2s ease-in-out infinite}
@keyframes fdotp{50%{transform:scale(1.35)}}
.farm .fpickall{border:0;border-radius:999px;padding:8px 18px;font:800 17px/1.2 var(--display);color:#fff;background:linear-gradient(180deg,#ff8ab4,#e8467e);box-shadow:0 3px 0 #b8325f;cursor:pointer}
.farm .ffly{position:fixed;width:52px;height:52px;object-fit:contain;z-index:30;pointer-events:none;transition:transform .7s cubic-bezier(.5,-.2,.6,1),opacity .7s}
.farm .fbask{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;margin:10px 0;max-height:46vh;overflow:auto;padding:3px}
.farm .fbi{position:relative;border:0;border-radius:14px;background:#fff6ea;box-shadow:0 0 0 2px #f0d9b8;padding:6px 4px;display:flex;flex-direction:column;align-items:center;cursor:pointer;font:800 15px/1.1 var(--display);color:#5a3a20}
.farm .fbi img{width:54px;height:54px;object-fit:contain}.farm .fbi .fbn{font:800 12px/1.15 var(--body);color:#5a3a20;text-align:center;overflow-wrap:anywhere;margin:2px 0 1px}.farm .fbi small{font:800 12px/1.2 var(--body);color:#8a6a50;display:flex;align-items:center;gap:2px}
.farm .fbi i{position:absolute;right:3px;top:3px;font:800 11px/1 var(--body);font-style:normal;background:#fff;border-radius:999px;padding:3px 5px;box-shadow:0 1px 3px rgba(0,0,0,.2)}
.farm .fbi.kept{background:#fdeef4;box-shadow:0 0 0 2px #f5c2d6}
.farm .fbi.nope{animation:fnope .35s}@keyframes fnope{25%{transform:translateX(-5px)}75%{transform:translateX(5px)}}
.farm .fempty{font-size:40px;text-align:center;margin:18px 0}
.farm .falbh{display:flex;align-items:center;justify-content:space-between;gap:8px;text-align:center}.farm .falbh h3{margin:0}.farm .falbh small{color:#8a6a50;font-weight:800}
.farm .fpg{border:0;border-radius:50%;width:44px;height:44px;background:#fde3ee;color:#e8467e;font-size:18px;cursor:pointer}.farm .fpg:disabled{opacity:.3}
.farm .falb{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin:10px 0;max-height:56vh;overflow:auto;padding:3px}
.farm .fstk{position:relative;border:0;border-radius:16px;background:#fff6ea;box-shadow:0 0 0 2px #f0d9b8;padding:6px 4px 5px;display:flex;flex-direction:column;align-items:center;gap:3px;cursor:pointer}
.farm .fstk .fsimg{width:100%;aspect-ratio:1;object-fit:contain;filter:grayscale(1) brightness(1.15) opacity(.45)}
.farm .fstk.made .fsimg{filter:drop-shadow(0 2px 3px rgba(0,0,0,.2))}.farm .fstk.made{background:#fff}
.farm .fstk.ready{box-shadow:0 0 0 3px #ffb81f,0 0 14px rgba(255,184,31,.7);animation:fglow 1.4s ease-in-out infinite}.farm .fstk.ready .fsimg{filter:none}
@keyframes fglow{50%{box-shadow:0 0 0 3px #ffb81f,0 0 22px rgba(255,184,31,.95)}}
.farm .fstk em{position:absolute;left:50%;top:38%;transform:translate(-50%,-50%);font:800 15px/1 var(--display);font-style:normal;color:#fff;background:linear-gradient(180deg,#ff8ab4,#e8467e);border-radius:999px;padding:7px 12px;box-shadow:0 3px 0 #b8325f}
.farm .fing{display:flex;flex-wrap:wrap;justify-content:center;gap:2px}.farm .fing i{display:flex;flex-direction:column;align-items:center;font-style:normal;opacity:.55}.farm .fing i.ok{opacity:1}
.farm .fing img{width:20px;height:20px;object-fit:contain}.farm .fing b{font:800 10px/1 var(--body);color:#6b4a2e}.farm .fing i.ok b{color:#2f8a3e}
.farm .fstkpic{width:150px;height:150px;object-fit:contain}.farm .fstkpic.grey{filter:grayscale(1) opacity(.5)}.farm .fstkpic.pop{animation:fpop .6s cubic-bezier(.3,1.6,.5,1)}
@keyframes fpop{0%{transform:scale(.2) rotate(-12deg)}100%{transform:none}}
.farm .fsub{margin:0;color:#8a6a50;font-weight:700}
.farm .fneedl{display:grid;gap:6px;margin:10px 0}.farm .fneedl div{display:grid;grid-template-columns:44px 1fr auto;align-items:center;gap:8px;background:#fff6ea;border-radius:12px;padding:4px 10px 4px 4px;text-align:left}
.farm .fneedl img{width:44px;height:44px;object-fit:contain}.farm .fneedl span{font:800 14px/1.2 var(--display);color:#5a3a20}.farm .fneedl small{display:block;font:700 12px/1.2 var(--body);color:#8a6a50}
.farm .fneedl b{font:800 16px/1 var(--display);color:#b8325f}.farm .fneedl .ok b{color:#2f8a3e}
@media (prefers-reduced-motion:reduce){.farm .fstk.ready,.farm .fdot{animation:none}.farm .ffly{transition:none}}
"""
rep(".farm .fbedbtn{z-index:4}", ".farm .fbedbtn{z-index:4}" + css)

path.write_text(src)
print("bouquets patch applied")
