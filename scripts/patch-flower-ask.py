"""Ask & Send a Flower: friends help each other finish bouquets (no two-way trading).

- Album: an unmade sticker shows "🙏 Ask" next to a missing Common or Uncommon flower. One tap asks ALL friends.
  One ask at a time (a new ask replaces the old one); it lasts 1 day or until a friend sends it.
- Friends: a friend who is asking shows "🌷 Send <name> a <flower>". One tap, then Send / Not now.
  If the flower is kept for your own bouquet, it asks "Send anyway?". The sender gets ⭐+2 Garden XP and 💧+1.
- Limits: Common and Uncommon only; 1 flower per friend a day; send up to 5 a day; receive up to 5 a day
  (more wait for tomorrow). Starts after the first flower is planted. Blocked players are ignored.
- The flower goes straight into the 🧺 Basket, with "Maria sent you a Pink Aster!" in the friends' gifts window.
Server: profiles/{pid}.ask = {f, at} and profiles/{pid}/flowers/{from}_{day} (firestore.rules).
Runs after patch-social.py, patch-bouquets.py and patch-ugc-safety.py (it edits the final www/index.html).
"""
from pathlib import Path

path = Path("www/index.html")
src = path.read_text()
if "FLOWER_ASK_PATCH" in src:
    print("flower ask patch already applied"); raise SystemExit(0)

def rep(before, after, count=1):
    global src
    n = src.count(before)
    if n != count:
        raise RuntimeError(f"patch-flower-ask: expected {count} of: {before[:80]!r}, found {n}")
    src = src.replace(before, after)

# --- my profile carries my open ask -------------------------------------------------------------
rep("glv: farmLevel(farm().xp).lv, g: gardenPublic(), at: Date.now() };",
    "glv: farmLevel(farm().xp).lv, g: gardenPublic(), at: Date.now(), ...(flAskLive(save.flAsk) ? { ask: { f: save.flAsk.f, at: save.flAsk.at } } : {}) };")

# --- home "Friends' Gardens" badge also lights up when a friend asks for a flower I have ------------
rep("const socBadge = () => { const n = socWaterNews; if (!n) return \"\"; const k = (n.names || []).length + (n.cnames || []).length; return k ? (n.cnames && n.cnames.length ? \"🎁\" : \"💧\") + k : \"\"; };",
    "const socBadge0 = () => { const n = socWaterNews; if (!n) return \"\"; const k = (n.names || []).length + (n.cnames || []).length + (n.fl || []).length; return k ? (n.fl && n.fl.length ? \"🌷\" : n.cnames && n.cnames.length ? \"🎁\" : \"💧\") + k : \"\"; };\n"
    "const socBadge = () => socBadge0() || (typeof flFriendAsks === \"function\" && flFriendAsks() ? \"🌷\" : \"\");")

# --- gifts window: flowers received -------------------------------------------------------------
rep("""  const w = n.names || [], c = n.cnames || [];
  sfx("create");""", """  const w = n.names || [], c = n.cnames || [], fl = n.fl || [];
  sfx("create");""")
rep("""    ${c.length ? `<h2>${who(c)} sent you ${FC_SVG}${n.coins}!</h2>` : ""}""",
    """    ${fl.length ? fl.map((x, j) => `<${j ? "p class=\\"fbig\\"" : "h2"} class="flgot"><img alt="" src="${brImg(x.f)}"><span><b>${socEsc(x.name)}</b> sent you a ${socEsc(SEEDS[x.f].n)}!</span></${j ? "p" : "h2"}>`).join("") + `<p class="llnote">It's in your 🧺 Basket.${n.flMax ? ` You can get ${FL_GET_MAX} flowers a day. More arrive tomorrow.` : ""}</p>` : ""}
    ${c.length ? `<${fl.length ? "p class=\\"fbig\\"" : "h2"}>${who(c)} sent you ${FC_SVG}${n.coins}!</${fl.length ? "p" : "h2"}>` : ""}""")
rep("""${c.length && !w.length ? "🎁 Say thank you" : "💧 Water back"}""",
    """${(c.length || fl.length) && !w.length ? "🎁 Say thank you" : "💧 Water back"}""")

# --- Friends list: "🌷 Send Maria a Pink Aster" under a friend who is asking -----------------------
rep("""<button class="frdel" data-i="${i}" aria-label="Remove">✕</button></div>`).join("")""",
    """<button class="frdel" data-i="${i}" aria-label="Remove">✕</button></div>${flAskRow(x, i)}`).join("")""")
rep("""    el.closest(".card").classList.add("frcard");
    el.querySelector("#frBack").onclick = back;""",
    """    el.closest(".card").classList.add("frcard");
    el.querySelector("#frBack").onclick = back;
    el.querySelector(".frlist").addEventListener("click", ev => { const b = ev.target.closest(".frask"); if (b) flSendAsk(fr[+b.dataset.i], again); });""")
rep("""Object.assign(x, { n: String(d.name || x.n || "").slice(0, 16), lv: d.lv, glv: d.glv, av: d.av });""",
    """Object.assign(x, { n: String(d.name || x.n || "").slice(0, 16), lv: d.lv, glv: d.glv, av: d.av, ask: d.ask || null }); flAskRowUpdate(el, x, i);""")

# --- collect flowers with the other gifts, live too ---------------------------------------------
rep("try { do { socAgain = false; await socClaimWater(); await socClaimCoins(); } while (socAgain); }",
    "try { do { socAgain = false; await socClaimWater(); await socClaimCoins(); await socClaimFlowers(); } while (socAgain); }")
rep("""for (const k of ["water", "coins"]) { try { socUnwatch.push(await S.watch(`profiles/${save.pid}/${k}`, ping)); }""",
    """for (const k of ["water", "coins", "flowers"]) { try { socUnwatch.push(await S.watch(`profiles/${save.pid}/${k}`, ping)); }""")
rep("setTimeout(async () => { if (!SOC()) return; socEnsure(); await socPublish(true); await socClaimAll(); socWatch(); }, 4000);",
    "setTimeout(async () => { if (!SOC()) return; socEnsure(); await socPublish(true); await socClaimAll(); socWatch(); flRefreshFriends(); }, 4000);")

# --- Album: "🙏 Ask" next to a missing Common/Uncommon flower -----------------------------------
rep("""      ${made ? "" : `<div class="fneedl">${b.ing.map(([q, id]) => { const h = f.inv[id] || 0, sd = SEEDS[id]; return `<div class="${h >= q ? "ok" : ""}"><img alt="" src="${brImg(id)}"><span>${sd.n}<small>${PLACE[sd.t] || ""}</small></span><b>${Math.min(h, q)}/${q}</b></div>`; }).join("")}</div>`}
      <div class="btns"><button class="btn alt" id="sBack">Back</button></div>`, c => c.querySelector("#sBack").onclick = () => albumSheet());""",
    """      ${made ? "" : `<div class="fneedl">${b.ing.map(([q, id]) => { const h = f.inv[id] || 0, sd = SEEDS[id], ask = h < q && typeof flAskBtn === "function" ? flAskBtn(id) : ""; return `<div class="${h >= q ? "ok" : ""}${ask ? " ask" : ""}"><img alt="" src="${brImg(id)}"><span>${sd.n}<small>${PLACE[sd.t] || ""}</small></span><b>${Math.min(h, q)}/${q}</b>${ask}</div>`; }).join("")}</div><p class="fasknote" id="sAskNote"></p>`}
      <div class="btns"><button class="btn alt" id="sBack">Back</button></div>`, c => { c.querySelector("#sBack").onclick = () => albumSheet();
        c.querySelectorAll(".fask").forEach(a => a.onclick = () => flAsk(a.dataset.f, c.querySelector("#sAskNote"), () => stickerTap(no))); });""")

code = r'''
/* FLOWER_ASK_PATCH: ask friends for a flower, send a flower to a friend who asks */
const FL_GIVE_MAX = 5, FL_GET_MAX = 5, FL_XP = 2, FL_ASK_MS = 24 * 3600 * 1000;
const flAskable = id => !!(SEEDS[id] && (SEEDS[id].r === "Common" || SEEDS[id].r === "Uncommon"));
const flAskLive = a => !!(a && flAskable(a.f) && +a.at > 0 && Date.now() - a.at < FL_ASK_MS && a.at < Date.now() + 3600000);
const flSentToday = pid => !!(save.flSent && save.flSent[pid] === dayKey());
const flGaveToday = () => save.flGave && save.flGave.d === dayKey() ? save.flGave.n : 0;
const flInv = () => { const f = farm(); f.inv = f.inv || {}; return f.inv; };
function flKeptNeed(id) {   // how many of this flower my own unmade bouquets need (the basket's 💐 rule)
  const st = farm().stk || {}; let n = 0;
  (window.BOUQUETS || []).forEach(b => { if (!st[b.no]) b.ing.forEach(([q, k]) => { if (k === id) n = Math.max(n, q); }); });
  return n;
}
// a friend who is asking, that I haven't helped today and haven't blocked
const flOpenAsk = x => x && x.p && !isBlocked(x.p) && flAskLive(x.ask) && !flSentToday(x.p) ? x.ask : null;
const flFriendAsks = () => (save.friends || []).some(x => { const a = flOpenAsk(x); return a && (flInv()[a.f] || 0) > 0; });

/* --- asking (Album) --- */
function flAskBtn(id) {
  if (!SOC() || !flAskable(id)) return "";
  const mine = flAskLive(save.flAsk) && save.flAsk.f === id;
  return mine ? `<em class="fask asked" aria-label="Asked friends">🙏 Asked</em>` : `<button class="fask" data-f="${id}" aria-label="Ask friends for ${socEsc(SEEDS[id].n)}">🙏 Ask</button>`;
}
async function flAsk(id, note, redo) {
  if (!flAskable(id)) return;
  const name = SEEDS[id].n, fr = (save.friends || []).filter(x => !isBlocked(x.p));
  if (!fr.length) {
    if (note) { note.innerHTML = `Add a friend first, then you can ask them for flowers.<br><button class="btn alt" id="sAskShare">📤 Share my Player ID</button>`;
      const b = note.querySelector("#sAskShare"); if (b) b.onclick = () => shareGarden(b); }
    return;
  }
  const old = flAskLive(save.flAsk) ? save.flAsk.f : "";
  save.flAsk = { f: id, at: Date.now() }; persist(); sfx("create"); track("flower_ask", { flower: id, rarity: SEEDS[id].r });
  const ok = await socPublish(true);
  redo();
  const n2 = document.getElementById("sAskNote");
  if (n2) n2.innerHTML = ok ? `🙏 You asked your friends for a <b>${socEsc(name)}</b>.${old && old !== id ? ` (Instead of the ${socEsc(SEEDS[old].n)}.)` : ""} It lasts 1 day.` : socEsc(socWhy(socLastErr));
}

/* --- sending (Friends) --- */
function flAskRow(x, i) {
  const a = flOpenAsk(x); if (!a) return "";
  return `<button class="frask" data-i="${i}" data-p="${socEsc(x.p)}"><img alt="" src="${brImg(a.f)}"><span>🌷 Send <b>${socEsc(x.n || pidShow(x.p))}</b> a ${socEsc(SEEDS[a.f].n)}</span></button>`;
}
function flAskRowUpdate(el, x, i) {
  if (!el || !el.isConnected) return;
  const old = el.querySelector(`.frask[data-i="${i}"]`), row = el.querySelector(`.frow[data-i="${i}"]`), html = flAskRow(x, i);
  if (old) { if (html) old.outerHTML = html; else old.remove(); } else if (html && row) row.insertAdjacentHTML("afterend", html);
  const e = document.querySelector("#nFriends .h3new"); if (e) e.textContent = socBadge();
}
async function flSend(pid, name, id) {
  const S = SOC(); if (!S) return { msg: "Friends' gardens work in the Flower Fever app." };
  if (!gardenStarted()) return { msg: "Plant your first flower in My Garden first. Then you can send flowers to friends." };
  if (!flAskable(id)) return { msg: "Only Common and Uncommon flowers can be sent." };
  if (flSentToday(pid)) return { msg: "You already sent a flower to this friend today." };
  if (flGaveToday() >= FL_GIVE_MAX) return { msg: `You've sent ${FL_GIVE_MAX} flowers today. You can send more tomorrow.` };
  if ((flInv()[id] || 0) < 1) return { msg: `You don't have a ${SEEDS[id].n} yet.` };
  if (!await socPublish()) return { msg: socWhy(socLastErr) };
  const today = dayKey();
  try { await S.set(`profiles/${pid}/flowers/${save.pid}_${today}`, { from: save.pid, name: save.nick, day: today, f: id, at: Date.now() }); }
  catch (e) { if (!isDenied(e)) return { msg: socWhy(e) }; save.flSent = { ...(save.flSent || {}), [pid]: today }; persist(); return { msg: "You already sent a flower to this friend today." }; }
  const f = farm(); flInv()[id]--; f.xp += FL_XP; f.water += 1;   // the flower leaves only after it is safely sent
  const s = {}; Object.entries(save.flSent || {}).forEach(([k, v]) => { if (v === today) s[k] = v; }); s[pid] = today; save.flSent = s;
  save.flGave = { d: today, n: flGaveToday() + 1 };
  addFriend({ p: pid, n: name }); persist(); track("flower_send", { flower: id, rarity: SEEDS[id].r });
  return { ok: true };
}
function flSendAsk(x, again) {
  const a = flOpenAsk(x); if (!a) { again(); return; }
  const id = a.f, sd = SEEDS[id], who = socEsc(x.n || pidShow(x.p)), have = flInv()[id] || 0, kept = have > 0 && have <= flKeptNeed(id);
  const left = FL_GIVE_MAX - flGaveToday();
  const body = have < 1 ? `<p>You don't have a <b>${socEsc(sd.n)}</b> yet.</p>`
    : left < 1 ? `<p>You've sent ${FL_GIVE_MAX} flowers today. You can send more tomorrow.</p>`
    : `<p>Send 1 <b>${socEsc(sd.n)}</b> to <b>${who}</b>?</p>${kept ? `<p class="llnote">💐 You need this flower for a bouquet.</p>` : ""}<p class="llnote">You have <b>${have}</b> · You get ⭐<b>+${FL_XP}</b> XP and 💧<b>+1</b></p>`;
  const can = have > 0 && left > 0;
  show(`<div class="ribbon">Send a flower</div><img class="flpic" alt="" src="${brImg(id)}"><h2>${who} needs a ${socEsc(sd.n)}</h2>${body}
    <div class="btns">${can ? `<button class="btn" id="flYes">${kept ? "Send anyway" : "Send"}</button>` : ""}<button class="btn alt" id="flNo">${can ? "Not now" : "OK"}</button></div>`, el => {
    el.querySelector("#flNo").onclick = again;
    const y = el.querySelector("#flYes"); if (!y) return;
    y.onclick = async () => { y.disabled = true; y.textContent = "Sending…"; const r = await flSend(x.p, x.n || pidShow(x.p), id);
      if (!r.ok) { y.remove(); el.querySelector("#flNo").textContent = "OK"; const p = el.querySelector("p"); if (p) p.textContent = r.msg; return; }
      sfx("create"); haptic("swap");
      show(`<div class="ribbon">Flower sent</div><img class="flpic" alt="" src="${brImg(id)}"><h2>${who} gets your ${socEsc(sd.n)}!</h2><p>They'll get it next time they play.</p><p class="fbig">⭐ <b>+${FL_XP}</b> XP · 💧 <b>+1</b></p><div class="btns"><button class="btn" id="fsOk">Lovely!</button></div>`, e2 => e2.querySelector("#fsOk").onclick = again); };
  });
}

/* --- receiving --- */
async function socClaimFlowers() {
  const S = SOC(); if (!S || !save.pid) return;
  let docs; try { docs = await S.list(`profiles/${save.pid}/flowers`); } catch (e) { return; }
  if (!docs.length) return;
  const today = dayKey(); if (!save.flGot || save.flGot.d !== today) save.flGot = { d: today, n: 0 };
  const got = []; let full = false, askDone = false;
  for (const w of docs.sort((a, b) => ((a.data || {}).at || 0) - ((b.data || {}).at || 0))) {
    const d = w.data || {}, bad = !flAskable(d.f) || (d.from && isBlocked(d.from));
    if (!bad && save.flGot.n >= FL_GET_MAX) { full = true; break; }   // today's limit: the rest stays for tomorrow
    try { await S.del(`profiles/${save.pid}/flowers/${w.id}`); } catch (e) { continue; }   // each flower counts once
    if (bad) continue;
    const name = String(d.name || "A friend").slice(0, 16);
    flInv()[d.f] = (flInv()[d.f] || 0) + 1; save.flGot.n++; got.push({ name, f: d.f });
    if (d.from) addFriend({ p: d.from, n: name, gb: today });
    if (flAskLive(save.flAsk) && save.flAsk.f === d.f) askDone = true;
  }
  if (askDone) { save.flAsk = null; }
  persist();
  if (askDone) socPublish(true);
  if (got.length) { const o = socWaterNews || {}; socWaterNews = { ...o, fl: [...(o.fl || []), ...got], flMax: full || o.flMax }; track("flower_got", { n: got.length }); }
}
// friends' open asks, for the home badge (quietly, a few at a time)
async function flRefreshFriends() {
  const S = SOC(); if (!S) return;
  for (const x of (save.friends || []).slice(0, 20)) { try { const d = await S.get("profiles/" + x.p); if (d) x.ask = d.ask || null; } catch (e) {} }
  const e = document.querySelector("#nFriends .h3new"); if (e) e.textContent = socBadge();
}

'''
rep("/* --- start: publish my profile, collect water gifts, and tell the player on the home screen --- */",
    code + "/* --- start: publish my profile, collect water gifts, and tell the player on the home screen --- */")

css = """
/* FLOWER_ASK_PATCH */
.farm .fneedl div.ask{grid-template-columns:44px 1fr auto auto}
.fask{border:0;border-radius:12px;padding:8px 10px;font:800 14px/1 var(--display);color:#fff;background:linear-gradient(180deg,#ff8fb8,#e8467e);box-shadow:0 3px 0 #b8325f;cursor:pointer;white-space:nowrap}
.fask.asked{background:#e9f6ea;color:#2f8a3e;box-shadow:none;font-style:normal}
.fasknote{margin:4px 0 0;font:700 14px/1.4 var(--body);color:#8a5e6e;min-height:0}
.fasknote:empty{display:none}
.fasknote .btn{margin-top:8px}
.frask{display:flex;align-items:center;gap:8px;width:100%;margin-top:-4px;border:0;border-radius:14px;padding:6px 12px 6px 6px;background:linear-gradient(180deg,#fff0f6,#ffd9e8);box-shadow:inset 0 -2px 0 #f3b6cd;text-align:left;cursor:pointer;font:700 15px/1.25 var(--body);color:#7a3a55}
.frask img{width:40px;height:40px;object-fit:contain;flex:none}
.flpic{display:block;width:110px;height:110px;object-fit:contain;margin:0 auto 4px}
h2.flgot,p.flgot{display:flex;align-items:center;justify-content:center;gap:8px}
.flgot img{width:56px;height:56px;object-fit:contain;flex:none}
</style>"""
i = src.find("</style>", src.find(".frow{"))
src = src[:i] + css + src[i + len("</style>"):]

path.write_text(src)
print("Ask & Send a Flower added")
