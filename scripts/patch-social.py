"""Player ID, friends' gardens, water gifts, and sharing wins and gardens.

- Every player gets a Player ID (FF-XXXXXX) and a nickname (free text, max 16 letters, checked for rude words).
  Their profile (nickname, level, stars, garden) is published to Firestore profiles/{ID} so others can look it up.
  Players who never signed in with Google use an anonymous Firebase user (www/native.js, window.FlowerFeverSocial).
- Friends: type a friend's ID to visit their garden (look only). Visited gardens are kept in a friends list.
- Water gift: water a friend's garden once a day. You get 💧+1 (up to 5 a day), they get 💧+1 when they next
  open the game (up to 10 a day), and they see who watered so they can water back.
- Coin gift: send 100 of your flower coins to a friend, once per friend a day (+2 Garden XP for you),
  after you have planted your first flower in My Garden.
  Each player can receive up to 300 coins a day; more gifts wait for the next day. Watering gives +1 Garden XP.
- Gifts arrive live while the game is open (Firestore listeners); the window shows on the Home screen.
- Share: a picture of a level win (level-complete window) or of your garden (Friends window), with your Player ID
  and the Google Play link. Shares the existing once-a-day +1 diamond with bouquet sharing.
- Home: a "Friends' Gardens" row under "View My Garden" (only in the app, where Firebase is set up).
Runs after the other patches (it edits the final www/index.html). The rules are in firestore.rules.
"""
from pathlib import Path

path = Path("www/index.html")
src = path.read_text()
if "SOCIAL_PATCH" in src:
    print("social patch already applied"); raise SystemExit(0)

def rep(before, after, count=1):
    global src
    n = src.count(before)
    if n != count:
        raise RuntimeError(f"patch-social: expected {count} of: {before[:90]!r}, found {n}")
    src = src.replace(before, after)

# --- publish the profile whenever the game saves --------------------------------------------------
rep("cloudSoon(); acctSoon(); }", "cloudSoon(); acctSoon(); if (typeof socSoon === \"function\") socSoon(); }")

# --- restoring / signing in on another phone: keep the friends list from both copies --------------
rep("""  m.freeLife = Math.max(+a.freeLife || 0, +b.freeLife || 0);
  return m;""", """  m.freeLife = Math.max(+a.freeLife || 0, +b.freeLife || 0);
  { const fr = [...(b.friends || [])]; (a.friends || []).forEach(x => { if (x && !fr.some(y => y.p === x.p)) fr.push(x); }); if (fr.length) m.friends = fr.slice(0, 60); }   // SOCIAL_PATCH
  return m;""")

# --- deleting the account also deletes the public profile ------------------------------------------
rep("const A = ACCT(); if (A && A.deleteData) await A.deleteData();",
    "const A = ACCT(); await socForget(); if (A && A.deleteData) await A.deleteData();")

# --- My Garden: a friend's garden can be opened to look at (visit mode) ----------------------------
rep("""function showMyGarden(onClose, plantCh) {
  busy = true; hide();
  onClose = onClose || (() => { busy = false; lastInput = T(); });
  const f = farm();""", """function showMyGarden(onClose, plantCh, visit) {
  busy = true; hide();
  onClose = onClose || (() => { busy = false; lastInput = T(); });
  const f = visit ? visit.farm : farm();""")
rep("""<div class="fchip" aria-label="Water">💧<b class="fwN"></b></div>""",
    """<div class="fchip" aria-label="Water">💧<b class="fwN"></b></div>${visit ? `<div class="fchip fvname">🌷 <b>${socEsc(visit.name)}</b></div>` : ""}""")
rep("""  let view = -1, moveFrom = null, moving = false, alive = true, area = null;""",
    """  let view = -1, moveFrom = null, moving = false, alive = true, area = null;
  if (visit) { el.classList.add("fvisit"); el.querySelector(".fcbuy").hidden = true; el.querySelector(".fwN").parentNode.hidden = true; }
  // a friend's garden: the same picture, nothing to tap, and a Water button
  function visitRender() {
    bar(); fit(); requestAnimationFrame(fit); view = -1;
    if (stage.dataset.bg !== "ov") { stage.dataset.bg = "ov"; stage.style.backgroundImage = `url(${window.GARDEN_OVERVIEW || FARM_IMG.overview_nh})`; }
    const hb = houseBox(f.house);
    stage.innerHTML = `<i class="fhshadow" style="left:${hb.l + hb.w * .08}%;top:${hb.t + hb.h * .9}%;width:${hb.w * .84}%;height:${hb.h * .14}%"></i><img class="fhouse" alt="" src="${FARM_HOUSE[f.house]}" style="left:${hb.l}%;top:${hb.t}%;width:${hb.w}%;height:${hb.h}%">` +
      BEDS.map((b, bi) => `<div class="fbed${f.beds[bi].open ? "" : " locked"}" data-b="${bi}">${f.beds[bi].open ? b.cells.map((_, i) => cellHTML(bi, i, false)).join("") : ""}</div>`).join("") + xareasHTML();
    stage.querySelectorAll("button").forEach(b => { b.disabled = true; b.tabIndex = -1; });
    stage.querySelectorAll(".flock").forEach(x => x.remove());
    const done = socWateredToday(visit.pid), gave = socGiftedToday(visit.pid);
    hint.innerHTML = `<b>${socEsc(visit.name)}</b>'s garden · Level ${visit.lv} · Garden Lv ${farmLevel(f.xp).lv}`;
    btns.innerHTML = `<button class="btn alt" id="fBack">⬅ Back</button><button class="btn fwater" id="vWater"${done ? " disabled" : ""}>${done ? "✓ Watered" : "💧 Water"}</button><button class="btn fgift" id="vGift"${gave ? " disabled" : ""}>${gave ? "✓ Gifted" : `🎁 ${FC_SVG}${COIN_GIFT}`}</button>`;
    btns.querySelector("#fBack").onclick = close;
    if (!done) btns.querySelector("#vWater").onclick = waterIt;
    if (!gave) btns.querySelector("#vGift").onclick = () => giftAsk(visit.pid, visit.name, ok => { if (!alive) return; render(); if (ok) { sfx("create"); haptic("swap"); sheetShow(`<h3>🎁 Gift sent!</h3><p><b>${socEsc(visit.name)}</b> gets ${FC_SVG}<b>${COIN_GIFT}</b> next time they play.</p><p class="fbig">⭐ <b>+${GIFT_XP}</b> Garden XP for you</p><div class="btns"><button class="btn" data-x>Lovely!</button></div>`); } }, (h, w) => sheetShow(h, w));
    spawnPets();
  }
  async function waterIt(e) {
    const b = e.currentTarget; b.disabled = true; b.textContent = "Watering…";
    const r = await socWater(visit.pid, visit.name);
    if (!alive) return;
    if (r && r.ok) {
      sfx("create"); haptic("swap"); render();
      for (let k = 0; k < 14; k++) { const d = document.createElement("i"); d.className = "fdrop"; d.textContent = "💧"; d.style.left = (15 + Math.random() * 70) + "%"; d.style.animationDelay = (Math.random() * .6) + "s"; stage.appendChild(d); setTimeout(() => d.remove(), 2200); }
      sheetShow(`<h3>💧 Watered!</h3><p><b>${socEsc(visit.name)}</b> gets 💧<b>+1</b> next time they play.</p>${r.got ? `<p class="fbig">You get 💧<b>+1</b> and ⭐<b>+${WATER_XP}</b> Garden XP!</p>` : `<p>You've had today's ${WATER_GIVE_MAX} water rewards. Come back tomorrow for more!</p>`}<div class="btns"><button class="btn" data-x>Lovely!</button></div>`);
    } else { b.disabled = false; b.textContent = "💧 Water"; sheetShow(`<h3>💧 Not watered</h3><p>${socEsc(r && r.msg || "Couldn't reach the garden. Check your internet and try again.")}</p><div class="btns"><button class="btn" data-x>OK</button></div>`); }
  }""")
rep("""  function render() {
    claimBlooms(); bar(); fit();""", """  function render() {
    if (visit) { visitRender(); return; }
    claimBlooms(); bar(); fit();""")
rep("""  if (!f.lvSeen) { f.lvSeen = farmLevel(f.xp).lv; persist(); } else if (farmLevel(f.xp).lv > f.lvSeen) levelUp(f.lvSeen);""",
    """  if (visit) {} else if (!f.lvSeen) { f.lvSeen = farmLevel(f.xp).lv; persist(); } else if (farmLevel(f.xp).lv > f.lvSeen) levelUp(f.lvSeen);""")
rep("""  if (!f.seen) { f.seen = 1;""", """  if (visit) {} else if (!f.seen) { f.seen = 1;""")

# --- level complete: a Share button --------------------------------------------------------------------
rep("""<button class="wpill" id="wGarden" aria-label="My garden"><span aria-hidden="true">🌷</span>Garden</button></div>""",
    """<button class="wpill" id="wGarden" aria-label="My garden"><span aria-hidden="true">🌷</span>Garden</button></div>
    <button class="wshare" id="wShare">📤 Share my win${shareBonusToday() ? ` <small>· <span class="fgem">${GEM_SVG}</span>+1</small>` : ""}</button>""")
rep("""      el.querySelector("#wHome").onclick = () => leaveWin(showHome);""",
    """      el.querySelector("#wHome").onclick = () => leaveWin(showHome);
      { const ws = el.querySelector("#wShare"); if (ws) ws.onclick = () => shareWin(ws, levelIdx + 1, st, score, wasCh); }""")

# --- Profile: Player ID and nickname -----------------------------------------------------------------
rep("""    ${acctBox()}
    <div class="btns"><button class="btn" id="prDone">Done</button></div>""", """    ${socProfileBox()}
    ${acctBox()}
    <div class="btns"><button class="btn" id="prDone">Done</button></div>""")
rep("""    el.querySelector("#prDone").onclick = back;""", """    el.querySelector("#prDone").onclick = back;
    socProfileWire(el, () => showProfile(back));""")

# --- Home: My Garden | Friends ---------------------------------------------------------------------------
rep("""<button class="h3row" id="nGarden"><img alt="" src="${HOME_IMG.sproutpot}"><span>View My Garden</span><em>Lv ${farmLevel(farm().xp).lv}</em><i>›</i></button>""",
    """<button class="h3row" id="nGarden"><img alt="" src="${HOME_IMG.sproutpot}"><span>View My Garden</span><em>Lv ${farmLevel(farm().xp).lv}</em><i>›</i></button>${SOC() ? `<button class="h3row" id="nFriends"><b class="h3fr" aria-hidden="true">👥</b><span>Friends' Gardens</span><em class="h3new">${socBadge()}</em><i>›</i></button>` : ""}""")
rep("""  el.querySelector("#nGarden").onclick = () => showMyGarden(back);""",
    """  el.querySelector("#nGarden").onclick = () => showMyGarden(back);
  { const nf = el.querySelector("#nFriends"); if (nf) nf.onclick = () => showFriends(back); }""")

code = r'''
/* ============ SOCIAL_PATCH: Player ID, friends' gardens, water gifts, sharing ============ */
const SOC = () => window.FlowerFeverSocial || null;
const PLAY_URL = "https://play.google.com/store/apps/details?id=com.alxmobileapps.flowerfever";
const WATER_GIVE_MAX = 5, WATER_GET_MAX = 10, FRIENDS_MAX = 60;
const COIN_GIFT = 100, COIN_GET_MAX = 300, WATER_XP = 1, GIFT_XP = 2;   // a coin gift: once per friend a day, paid from your own coins; you can receive up to 300 a day (the rest waits for tomorrow)
const socEsc = s => String(s == null ? "" : s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const dayKey = (d = new Date()) => `${d.getFullYear()}${String(d.getMonth() + 1).padStart(2, "0")}${String(d.getDate()).padStart(2, "0")}`;
const pidShow = p => p ? p.slice(0, 2) + "-" + p.slice(2) : "";
function pidNew() { let k = "FF"; const b = new Uint32Array(6); try { crypto.getRandomValues(b); } catch (e) { for (let i = 0; i < 6; i++) b[i] = Math.random() * 1e9; } for (let i = 0; i < 6; i++) k += SYNC_CHARS[b[i] % SYNC_CHARS.length]; return k; }
function pidParse(v) { v = String(v || "").toUpperCase().replace(/[^A-Z0-9]/g, ""); if (v.length === 6) v = "FF" + v; return /^FF[A-Z0-9]{6}$/.test(v) ? v : ""; }
function socEnsure() {   // a Player ID and a starting nickname for everyone
  let ch = false;
  if (!save.pid) { save.pid = pidNew(); ch = true; }
  if (!save.nick) { save.nick = "Gardener " + save.pid.slice(-4); ch = true; }
  if (ch) try { localStorage.setItem("petalpop.v1", JSON.stringify(save)); } catch (e) {}
}
const socWateredToday = pid => !!(save.watered && save.watered[pid] === dayKey());
const socBadge = () => { const n = socWaterNews; if (!n) return ""; const k = (n.names || []).length + (n.cnames || []).length; return k ? (n.cnames && n.cnames.length ? "🎁" : "💧") + k : ""; };
const socGiftedToday = pid => !!(save.gifted && save.gifted[pid] === dayKey());
const shareBonusToday = () => { const f = farm(); return f.shareDay !== new Date().toDateString(); };

// nicknames: free text, but no rude words (English and Filipino), checked after undoing look-alike letters
const NICK_BAD = ["fuck", "fuk", "fck", "shit", "bitch", "cunt", "asshole", "bastard", "whore", "slut", "nigg", "faggot", "retard", "rapist", "porn", "penis", "vagina", "boob", "puta", "putang", "tangina", "tanginamo", "gago", "ulol", "tarantado", "kantot", "kupal", "pakyu", "pakshet", "burat", "pokpok", "hindot", "punyeta", "pucha", "jakol", "bilat", "kingina", "inamo", "motherf", "dickhead", "pussy"];
const NICK_BAD_WORD = ["sex", "dick", "cock", "tanga", "bobo", "titi", "puke", "suso", "tae", "leche", "shet", "inutil", "kiki", "nazi", "hitler", "kill", "die"];
function nickProblem(v) {
  const t = String(v || "").replace(/\s+/g, " ").trim();
  if (t.length < 2) return "Please use at least 2 letters.";
  if (t.length > 16) return "Please use 16 letters or fewer.";
  if (/https?:|www\.|\.com|@/i.test(t)) return "Please don't use links or emails in your name.";
  const leet = t.toLowerCase().replace(/[4@]/g, "a").replace(/3/g, "e").replace(/[1!|]/g, "i").replace(/0/g, "o").replace(/[5$]/g, "s").replace(/7/g, "t");
  const joined = leet.replace(/[^a-z]/g, ""), words = leet.split(/[^a-z]+/).filter(Boolean);
  if (NICK_BAD.some(w => joined.includes(w)) || words.some(w => NICK_BAD_WORD.includes(w))) return "Please choose a kinder name 🌷";
  return "";
}

/* --- my public profile: nickname, level, stars, garden (only what's needed to draw it) --- */
function gardenPublic() {
  const f = farm(), pl = p => p && SEEDS[p.b] ? [p.b, Math.round(p.at), Math.round(p.ms)] : 0;
  const a = {}; Object.entries(f.areas || {}).forEach(([k, s]) => { a[k] = [s.open ? 1 : 0, (s.plots || []).map(pl)]; });
  return JSON.stringify({ h: f.house, x: f.xp || 0, pt: f.pets || {}, b: f.beds.map(s => [s.open ? 1 : 0, (s.plots || []).map(pl)]), a });
}
function profileData(uid) {
  return { uid, name: save.nick, av: +(save.avatar ?? 0) || 0, lv: save.unlocked || 1, stars: Object.values(save.stars || {}).reduce((a, b) => a + (b || 0), 0), glv: farmLevel(farm().xp).lv, g: gardenPublic(), at: Date.now() };
}
let socLast = "", socTimer = 0, socBusy = null, socAt = 0;
function socSoon() { if (!SOC()) return; clearTimeout(socTimer); socTimer = setTimeout(() => socPublish(), Date.now() - socAt > 120000 ? 8000 : 60000); }
const isDenied = e => /permission|denied|insufficient/i.test(String((e && (e.code || "")) + " " + ((e && e.message) || e || "")));
// say what really went wrong, so a setup problem isn't mistaken for bad internet
let socLastErr = null;
const socWhy = e => {
  const t = String((e && (e.code || "")) + " " + ((e && e.message) || e || ""));
  if (/not signed in|anonymous|operation-not-allowed|admin-restricted/i.test(t)) return "Friends' gardens can't sign in yet. (Firebase: turn on Anonymous sign-in.)";
  if (isDenied(e)) return "Friends' gardens are switched off on the server. (Firebase: publish the Firestore rules.)";
  return "Couldn't reach the garden. Check your internet and try again.";
};
async function socPublish(force) {
  const S = SOC(); if (!S) return false;
  if (socBusy) return socBusy;
  socBusy = (async () => {
    socEnsure();
    const uid = await S.uid(); if (!uid) { socLastErr = new Error("not signed in"); return false; }
    const d = profileData(uid), sig = JSON.stringify({ ...d, at: 0 });
    if (!force && sig === socLast) return true;
    try { await S.set("profiles/" + save.pid, d); socLast = sig; socAt = Date.now(); socLastErr = null; return true; }
    catch (e) {
      socLastErr = e;
      if (!isDenied(e)) return false;
      // the ID belongs to someone else (very rare), or to this player's other account: pick a new one
      let other = null; try { other = await S.get("profiles/" + save.pid); } catch (e2) { return false; }
      if (!other || other.uid === uid) return false;   // not a clash: leave the ID alone
      save.pid = pidNew(); if (/^Gardener [A-Z0-9]{4}$/.test(save.nick)) save.nick = "Gardener " + save.pid.slice(-4);
      try { localStorage.setItem("petalpop.v1", JSON.stringify(save)); } catch (e3) {}
      try { await S.set("profiles/" + save.pid, { ...d, name: save.nick }); socLast = sig; socAt = Date.now(); persist(); return true; } catch (e4) { return false; }
    }
  })();
  try { return await socBusy; } finally { socBusy = null; }
}
async function socForget() { const S = SOC(); if (!S || !save.pid) return; try { await S.del("profiles/" + save.pid); } catch (e) {} socLast = ""; }

/* --- friends list (gardens you visited, and friends who watered yours) --- */
function addFriend(x) {
  if (!x || !x.p || x.p === save.pid) return;
  save.friends = save.friends || [];
  const i = save.friends.findIndex(y => y.p === x.p), old = i >= 0 ? save.friends.splice(i, 1)[0] : {};
  save.friends.unshift({ ...old, ...x, at: Date.now() }); save.friends.length = Math.min(save.friends.length, FRIENDS_MAX);
}

/* --- water gifts --- */
let socWaterNews = null;
async function socWater(pid, name) {
  const S = SOC(); if (!S) return { msg: "Friends' gardens work in the Flower Fever app." };
  if (socWateredToday(pid)) return { msg: "You already watered this garden today." };
  if (!await socPublish()) return { msg: socWhy(socLastErr) };
  const today = dayKey();
  try { await S.set(`profiles/${pid}/water/${save.pid}_${today}`, { from: save.pid, name: save.nick, day: today, at: Date.now() }); }
  catch (e) { if (!isDenied(e)) return { msg: socWhy(e) }; save.watered = { ...(save.watered || {}), [pid]: today }; persist(); return { msg: "You already watered this garden today." }; }
  const w = {}; Object.entries(save.watered || {}).forEach(([k, v]) => { if (v === today) w[k] = v; }); w[pid] = today; save.watered = w;
  if (!save.waterGave || save.waterGave.d !== today) save.waterGave = { d: today, n: 0 };
  let got = 0; if (save.waterGave.n < WATER_GIVE_MAX) { save.waterGave.n++; got = 1; farm().water += 1; farm().xp += WATER_XP; }
  addFriend({ p: pid, n: name }); persist(); track("friend_water", { got });
  return { ok: true, got };
}
// coin gifts start once the player has planted their first flower (so new players don't give away their starting coins)
const gardenStarted = () => { const f = save.farm; return !!(f && (f.tut || [...(f.beds || []), ...Object.values(f.areas || {})].some(s => (s.plots || []).some(Boolean)))); };
const GIFT_LOCKED = "Plant your first flower in My Garden first. Then you can send coin gifts to friends.";
async function socGift(pid, name) {
  const S = SOC(); if (!S) return { msg: "Friends' gardens work in the Flower Fever app." };
  if (!gardenStarted()) return { msg: GIFT_LOCKED };
  if (socGiftedToday(pid)) return { msg: "You already sent a gift to this friend today." };
  if (farm().coins < COIN_GIFT) return { msg: `You need ${COIN_GIFT} flower coins to send a gift.`, short: true };
  if (!await socPublish()) return { msg: socWhy(socLastErr) };
  const today = dayKey();
  try { await S.set(`profiles/${pid}/coins/${save.pid}_${today}`, { from: save.pid, name: save.nick, day: today, n: COIN_GIFT, at: Date.now() }); }
  catch (e) { if (!isDenied(e)) return { msg: socWhy(e) }; save.gifted = { ...(save.gifted || {}), [pid]: today }; persist(); return { msg: "You already sent a gift to this friend today." }; }
  const f = farm(); f.coins -= COIN_GIFT; f.xp += GIFT_XP;   // the coins leave only after the gift is safely sent
  const g = {}; Object.entries(save.gifted || {}).forEach(([k, v]) => { if (v === today) g[k] = v; }); g[pid] = today; save.gifted = g;
  addFriend({ p: pid, n: name }); persist(); track("friend_gift", {});
  return { ok: true };
}
// "Send 100 coins to Rosa?" then send; show = where to draw the question (garden sheet or a window)
function giftAsk(pid, name, done, sheet) {
  if (!gardenStarted()) { sheet(`<h3>🎁 Gift ${FC_SVG}${COIN_GIFT}</h3><p>${GIFT_LOCKED}</p><div class="btns"><button class="btn alt" data-x>OK</button></div>`, () => {}); return; }
  const have = farm().coins, can = have >= COIN_GIFT;
  const html = `<h3>🎁 Gift ${FC_SVG}${COIN_GIFT}</h3><p>${can ? `Send <b>${COIN_GIFT}</b> of your flower coins to <b>${socEsc(name)}</b>?` : `You need ${FC_SVG}<b>${COIN_GIFT}</b> to send a gift.`}</p><p class="llnote">You have ${FC_SVG}<b>${have}</b>${can ? ` · You get ⭐<b>+${GIFT_XP}</b> Garden XP` : ""}</p>
    <div class="btns">${can ? `<button class="btn" id="gfYes">Send gift</button>` : ""}<button class="btn alt" id="gfNo" data-x>${can ? "Not now" : "OK"}</button></div>`;
  sheet(html, c => {
    const y = c.querySelector("#gfYes"); if (!y) return;
    y.onclick = async () => { y.disabled = true; y.textContent = "Sending…"; const r = await socGift(pid, name);
      if (r.ok) done(true); else { y.remove(); const p = c.querySelector("p"); if (p) p.textContent = r.msg; done(false); } };
  });
}
async function socClaimCoins() {
  const S = SOC(); if (!S || !save.pid) return;
  let docs; try { docs = await S.list(`profiles/${save.pid}/coins`); } catch (e) { return; }
  if (!docs.length) return;
  const today = dayKey(); if (!save.coinGot || save.coinGot.d !== today) save.coinGot = { d: today, n: 0 };
  const names = []; let gain = 0;
  for (const w of docs.sort((a, b) => ((a.data || {}).at || 0) - ((b.data || {}).at || 0))) {
    if (save.coinGot.n + COIN_GIFT > COIN_GET_MAX) break;   // today's limit: the rest stays for tomorrow
    try { await S.del(`profiles/${save.pid}/coins/${w.id}`); } catch (e) { continue; }   // each gift counts once
    const d = w.data || {}; if (d.name && !names.includes(d.name)) names.push(String(d.name).slice(0, 16));
    if (d.from) addFriend({ p: d.from, n: String(d.name || "").slice(0, 16), gb: today });
    save.coinGot.n += COIN_GIFT; gain += COIN_GIFT;
  }
  if (gain) { farm().coins += gain; persist(); }
  if (names.length) { const o = socWaterNews || { names: [], gain: 0 }; socWaterNews = { ...o, cnames: [...(o.cnames || []), ...names], coins: (o.coins || 0) + gain }; track("friend_gift_got", { n: names.length, gain }); }
}
async function socClaimWater() {
  const S = SOC(); if (!S || !save.pid) return;
  let docs; try { docs = await S.list(`profiles/${save.pid}/water`); } catch (e) { return; }
  if (!docs.length) return;
  const today = dayKey(); if (!save.waterGot || save.waterGot.d !== today) save.waterGot = { d: today, n: 0 };
  const names = []; let gain = 0;
  for (const w of docs) {
    try { await S.del(`profiles/${save.pid}/water/${w.id}`); } catch (e) { continue; }   // each gift counts once
    const d = w.data || {}; if (d.name && !names.includes(d.name)) names.push(String(d.name).slice(0, 16));
    if (d.from) addFriend({ p: d.from, n: String(d.name || "").slice(0, 16), wb: today });
    if (save.waterGot.n < WATER_GET_MAX) { save.waterGot.n++; gain++; }
  }
  if (gain) farm().water += gain;
  persist();
  if (names.length) { const o = socWaterNews || {}; socWaterNews = { ...o, names: [...(o.names || []), ...names], gain: (o.gain || 0) + gain }; track("friend_water_got", { n: names.length, gain }); }
}
function showWaterNews(back) {
  const n = socWaterNews; if (!n) return false; socWaterNews = null;
  const who = l => l.length === 1 ? `<b>${socEsc(l[0])}</b>` : l.length === 2 ? `<b>${socEsc(l[0])}</b> and <b>${socEsc(l[1])}</b>` : `<b>${socEsc(l[0])}</b> and ${l.length - 1} friends`;
  const w = n.names || [], c = n.cnames || [];
  sfx("create");
  show(`<div class="ribbon">Gifts from friends</div><div class="wdrops" aria-hidden="true">${c.length ? "🎁" : "💧"}🌷${w.length ? "💧" : "🎁"}</div>
    ${c.length ? `<h2>${who(c)} sent you ${FC_SVG}${n.coins}!</h2>` : ""}
    ${w.length ? `<${c.length ? "p class=\"fbig\"" : "h2"}>${who(w)} watered your garden!</${c.length ? "p" : "h2"}>${n.gain ? `<p class="fbig">💧 <b>+${n.gain}</b> water for you</p>` : `<p>You've had today's ${WATER_GET_MAX} water gifts.</p>`}` : ""}
    ${c.length && n.coins >= COIN_GET_MAX ? `<p class="llnote">You can get up to ${FC_SVG}${COIN_GET_MAX} a day. More gifts arrive tomorrow.</p>` : ""}
    <div class="btns"><button class="btn" id="wnBack">${c.length && !w.length ? "🎁 Say thank you" : "💧 Water back"}</button><button class="btn alt" id="wnOk">Lovely!</button></div>`, el => {
    el.querySelector("#wnOk").onclick = back;
    el.querySelector("#wnBack").onclick = () => showFriends(back);
  });
  return true;
}

/* --- Friends window --- */
const avImg = av => SPRITE_SRC[av] || flowerIcon(+av || 0);
function showFriends(back) {
  const S = SOC();
  if (!S) { show(`<div class="ribbon">Friends</div><h2>Friends' gardens</h2><p>Visit your friends' gardens in the Flower Fever app.</p><div class="btns"><button class="btn" id="frBack">OK</button></div>`, el => el.querySelector("#frBack").onclick = back); return; }
  socEnsure();
  const fr = save.friends || [], again = () => showFriends(back);
  show(`<div class="ribbon">Friends</div>
    <div class="cloudbox frme"><b>🌷 Your Player ID</b><code id="frMine">${pidShow(save.pid)}</code><span>Name: <b>${socEsc(save.nick)}</b> <button class="frlink" id="frName">✏️ Change</button></span>
      <div class="frrow2"><button class="btn alt" id="frCopy">Copy ID</button><button class="btn alt" id="frShare">📤 Share my garden</button></div></div>
    <p class="frlabel">Visit a friend's garden</p>
    <div class="frfind"><input class="codein" id="frId" maxlength="9" autocomplete="off" autocapitalize="characters" placeholder="FF-ABC234" aria-label="Friend's Player ID"><button class="btn" id="frGo">Visit</button></div>
    <p class="llnote" id="frMsg"></p>
    <div class="frlist">${fr.length ? fr.map((x, i) => `<div class="frow" data-i="${i}"><button class="frvisit" data-i="${i}"><img alt="" src="${avImg(x.av)}"><span><b>${socEsc(x.n || pidShow(x.p))}</b><small class="frinfo">${x.lv ? `Level ${x.lv}` : pidShow(x.p)}${x.glv ? ` · Garden Lv ${x.glv}` : ""}${x.wb === dayKey() ? " · watered you 💧" : ""}${x.gb === dayKey() ? " · sent you 🎁" : ""}</small></span></button>${socWateredToday(x.p) ? `<em class="frdone" aria-label="Watered today">✓💧</em>` : `<button class="frwater" data-i="${i}" aria-label="Water ${socEsc(x.n || "")}'s garden">💧</button>`}${socGiftedToday(x.p) ? `<em class="frdone" aria-label="Gift sent today">✓🎁</em>` : `<button class="frgift" data-i="${i}" aria-label="Gift ${COIN_GIFT} coins to ${socEsc(x.n || "")}">🎁</button>`}<button class="frdel" data-i="${i}" aria-label="Remove">✕</button></div>`).join("")
      : `<p class="frempty">Share your Player ID with family and friends, then visit each other's gardens and water them every day 💧 You can also send them 🎁 flower coins.</p>`}</div>
    <div class="btns"><button class="btn alt" id="frBack">Back</button></div>`, el => {
    el.closest(".card").classList.add("frcard");
    el.querySelector("#frBack").onclick = back;
    el.querySelector("#frName").onclick = () => nickWindow(again);
    el.querySelector("#frCopy").onclick = async e => { const b = e.currentTarget; let ok = false; try { await navigator.clipboard.writeText(pidShow(save.pid)); ok = true; } catch (er) {} b.textContent = ok ? "✓ Copied" : pidShow(save.pid); setTimeout(() => { b.textContent = "Copy ID"; }, 1800); };
    el.querySelector("#frShare").onclick = e => shareGarden(e.currentTarget);
    const inp = el.querySelector("#frId"), msg = el.querySelector("#frMsg");
    const go = () => { const p = pidParse(inp.value); if (!p) { msg.textContent = "A Player ID looks like FF-ABC234."; return; } if (p === save.pid) { msg.textContent = "That's your own ID 🙂"; return; } visitFriend(p, again, msg); };
    el.querySelector("#frGo").onclick = go; inp.onkeydown = e => { if (e.key === "Enter") go(); };
    el.querySelectorAll(".frvisit").forEach(b => b.onclick = () => visitFriend(fr[+b.dataset.i].p, again, msg));
    el.querySelectorAll(".frwater").forEach(b => b.onclick = async () => { const x = fr[+b.dataset.i]; b.disabled = true; b.textContent = "…";
      const r = await socWater(x.p, x.n);
      if (r.ok) { sfx("create"); b.outerHTML = `<em class="frdone">✓💧</em>`; msg.innerHTML = `💧 You watered <b>${socEsc(x.n || pidShow(x.p))}</b>'s garden!${r.got ? ` You get 💧+1 and ⭐+${WATER_XP} XP.` : ""}`; }
      else { b.disabled = false; b.textContent = "💧"; msg.textContent = r.msg; } });
    el.querySelectorAll(".frgift").forEach(b => b.onclick = () => { const x = fr[+b.dataset.i];
      giftAsk(x.p, x.n || pidShow(x.p), ok => { if (ok) { sfx("create"); show(`<div class="ribbon">Gift sent</div><div class="wdrops" aria-hidden="true">🎁</div><h2>${socEsc(x.n || pidShow(x.p))} gets ${FC_SVG}${COIN_GIFT}!</h2><p>They'll get it next time they play.</p><p class="fbig">⭐ <b>+${GIFT_XP}</b> Garden XP for you</p><div class="btns"><button class="btn" id="gsOk">Lovely!</button></div>`, e3 => e3.querySelector("#gsOk").onclick = again); } },
        (h, wire) => show(`<div class="ribbon">Gift</div>${h.replace(/<h3>/, "<h2>").replace(/<\/h3>/, "</h2>")}`, e2 => { e2.querySelectorAll("[data-x]").forEach(z => z.onclick = again); wire(e2); })); });
    el.querySelectorAll(".frdel").forEach(b => b.onclick = () => { const x = fr[+b.dataset.i];
      show(`<div class="ribbon">Friends</div><h2>Remove ${socEsc(x.n || pidShow(x.p))}?</h2><p>You can add them again any time with their Player ID: <b>${pidShow(x.p)}</b></p><div class="btns"><button class="btn" id="rmYes">Remove</button><button class="btn alt" id="rmNo">Cancel</button></div>`,
        e2 => { e2.querySelector("#rmNo").onclick = again; e2.querySelector("#rmYes").onclick = () => { save.friends = (save.friends || []).filter(y => y.p !== x.p); persist(); again(); }; }); });
    // freshen the names and levels in the list (quietly, a few at a time)
    fr.slice(0, 20).forEach(async (x, i) => { try { const d = await S.get("profiles/" + x.p); if (!d) return; Object.assign(x, { n: String(d.name || x.n || "").slice(0, 16), lv: d.lv, glv: d.glv, av: d.av });
      const row = el.querySelector(`.frow[data-i="${i}"]`); if (row && row.isConnected) { row.querySelector("b").textContent = x.n; const s = row.querySelector(".frinfo"); if (s) s.textContent = `Level ${x.lv} · Garden Lv ${x.glv}${x.wb === dayKey() ? " · watered you 💧" : ""}${x.gb === dayKey() ? " · sent you 🎁" : ""}`; row.querySelector("img").src = avImg(x.av); } } catch (e) {} });
  });
}
// the garden from a profile, in the shape My Garden draws (unknown flowers or houses from a newer version are left out)
function farmFromPublic(o) {
  const pl = a => Array.isArray(a) && SEEDS[a[0]] ? { b: a[0], at: +a[1] || 0, ms: +a[2] || 1 } : null;
  const f = { coins: 0, water: 0, xp: +o.x || 0, house: HOUSES.some(h => h[0] === o.h) ? o.h : "h1", pets: {}, beds: [], areas: {}, seen: 1, lvSeen: 1e9 };
  PETS.forEach(p => { const n = Math.min(p[4], Math.max(0, Math.floor(+(o.pt || {})[p[0]] || 0))); if (n) f.pets[p[0]] = n; });
  BEDS.forEach((b, i) => { const s = (o.b || [])[i]; f.beds[i] = { open: s && s[0] ? 1 : 0, plots: Array.from({ length: 9 }, (_, j) => s && s[1] ? pl(s[1][j]) : null) }; });
  Object.keys(XAREAS).forEach(k => { const s = (o.a || {})[k]; f.areas[k] = { open: s && s[0] ? 1 : 0, plots: Array.from({ length: XAREAS[k].cells.length }, (_, j) => s && s[1] ? pl(s[1][j]) : null) }; });
  return f;
}
async function visitFriend(pid, back, msgEl) {
  const S = SOC(); if (!S) return;
  if (msgEl) msgEl.textContent = "Opening garden…";
  let d = null;
  try { d = await S.get("profiles/" + pid); }
  catch (e) { if (msgEl && msgEl.isConnected) msgEl.textContent = socWhy(e); return; }
  if (!d) { if (msgEl && msgEl.isConnected) msgEl.textContent = `No garden found for ${pidShow(pid)}. Check the letters and try again.`; return; }
  let g = {}; try { g = JSON.parse(d.g || "{}"); } catch (e) {}
  const name = String(d.name || "Gardener").slice(0, 16);
  addFriend({ p: pid, n: name, lv: d.lv, glv: d.glv, av: d.av }); persist(); track("friend_visit", {});
  hide(); showMyGarden(back, null, { pid, name, lv: d.lv || 1, farm: farmFromPublic(g) });
}
function nickWindow(back) {
  show(`<div class="ribbon">Your name</div><h2>What should friends call you?</h2><p>Friends see this name when they visit your garden.</p>
    <input class="codein nickin" id="nkIn" maxlength="16" autocomplete="off" value="${socEsc(save.nick || "")}" aria-label="Your name"><p class="llnote" id="nkMsg"></p>
    <div class="btns"><button class="btn" id="nkSave">Save</button><button class="btn alt" id="nkBack">Cancel</button></div>`, el => {
    const inp = el.querySelector("#nkIn"), msg = el.querySelector("#nkMsg");
    el.querySelector("#nkBack").onclick = back;
    el.querySelector("#nkSave").onclick = () => { const v = inp.value.replace(/[<>&"]/g, "").replace(/\s+/g, " ").trim(), bad = nickProblem(v); if (bad) { msg.textContent = bad; return; }
      save.nick = v; persist(); socPublish(true); track("nickname_set", {}); back(); };
    setTimeout(() => { try { inp.focus(); inp.select(); } catch (e) {} }, 250);
  });
}
function socProfileBox() {
  if (!SOC()) return ""; socEnsure();
  return `<div class="cloudbox frme"><b>🌷 Player ID</b><code>${pidShow(save.pid)}</code><span>Name: <b>${socEsc(save.nick)}</b> <button class="frlink" id="prName">✏️ Change</button></span><div class="frrow2"><button class="btn alt" id="prFriends">👥 Friends' gardens</button></div></div>`;
}
function socProfileWire(el, again) {
  const n = el.querySelector("#prName"); if (n) n.onclick = () => nickWindow(again);
  const f = el.querySelector("#prFriends"); if (f) f.onclick = () => showFriends(again);
}

/* --- share pictures: a level win, or my garden --- */
const loadImg = src => new Promise(res => { if (!src) return res(null); const im = new Image(); im.onload = () => res(im); im.onerror = () => res(null); im.src = src; });
function drawStar(g, x, y, r, on) {
  g.beginPath(); for (let i = 0; i < 10; i++) { const a = -Math.PI / 2 + i * Math.PI / 5, rr = i % 2 ? r * .45 : r; g.lineTo(x + Math.cos(a) * rr, y + Math.sin(a) * rr); } g.closePath();
  g.fillStyle = on ? "#ffc83a" : "#f1dde6"; g.fill(); g.lineWidth = r * .1; g.strokeStyle = on ? "#e59a12" : "#e3c4d2"; g.stroke();
}
function idLine(g, S, y) {
  if (!SOC() || !save.pid) return;
  g.textAlign = "center"; g.fillStyle = "#7a3a55"; g.font = '800 40px "Baloo 2","Trebuchet MS",sans-serif'; g.fillText(`Visit my garden! Player ID: ${pidShow(save.pid)}`, S / 2, y);
}
// the game's own title, as on the home screen: "Flower" + spinning rainbow flower + "Fever" in Pacifico, white with a pink rim and a dark outline
async function drawGameLogo(g, cx, base, px) {
  try { await document.fonts.load(`400 ${px}px Pacifico`); } catch (e) {}
  const rb = await loadImg(SPRITE_SRC.rainbow), em = v => v * px;
  g.save(); g.font = `400 ${px}px Pacifico, cursive`; g.textBaseline = "alphabetic"; g.textAlign = "left";
  const w1 = g.measureText("Flower").width, w2 = g.measureText("Fever").width, rs = em(.6), gap1 = em(.03), gap2 = em(.05);
  const total = w1 + gap1 + rs + gap2 + w2, x1 = cx - total / 2, xr = x1 + w1 + gap2, x2 = xr + rs + gap1;
  const words = [["Flower", x1], ["Fever", x2]];
  const each = f => words.forEach(([t, x]) => f(t, x));
  g.shadowColor = "rgba(255,46,166,.6)"; g.shadowBlur = em(.26); g.fillStyle = "#ff3fae"; each((t, x) => g.fillText(t, x, base)); g.shadowBlur = 0; g.shadowColor = "transparent";
  g.fillStyle = "#5a0718";   // dark outline, like the home screen's text shadows
  [[.068, 0], [-.068, 0], [0, .068], [0, -.068], [.054, .054], [-.054, .054], [.054, -.054], [-.054, -.054], [.041, .081], [-.041, .081], [.081, .041], [-.081, .041], [0, .095]]
    .forEach(([dx, dy]) => each((t, x) => g.fillText(t, x + em(dx), base + em(dy))));
  g.lineJoin = "round"; g.strokeStyle = "#ff3fae"; g.lineWidth = em(.068); each((t, x) => g.strokeText(t, x, base));
  g.fillStyle = "#fff0fa"; each((t, x) => g.fillText(t, x, base));
  if (rb) { g.shadowColor = "rgba(255,200,40,.95)"; g.shadowBlur = em(.08); g.drawImage(rb, xr, base + em(.04) - rs, rs, rs); }
  g.restore();
}
async function winPng(lv, st, sc) {
  const S = 1080, c = document.createElement("canvas"); c.width = c.height = S; const g = c.getContext("2d");
  const bg = g.createLinearGradient(0, 0, 0, S); bg.addColorStop(0, "#fff6fa"); bg.addColorStop(1, "#fde3ee"); g.fillStyle = bg; g.fillRect(0, 0, S, S);
  g.fillStyle = "rgba(255,255,255,.8)"; g.beginPath(); g.arc(S / 2, 560, 400, 0, Math.PI * 2); g.fill();
  await drawGameLogo(g, S / 2, 190, 150);
  const fl = await loadImg(avImg(save.avatar ?? 0)); if (fl) { g.drawImage(fl, 110, 600, 150, 150); g.drawImage(fl, S - 260, 600, 150, 150); }
  g.textAlign = "center"; g.fillStyle = "#e8467e"; g.font = '800 64px "Baloo 2","Trebuchet MS",sans-serif'; g.fillText("I finished", S / 2, 345);
  g.fillStyle = "#5a2e44"; g.font = '800 170px "Baloo 2","Trebuchet MS",sans-serif'; g.fillText(`Level ${lv}`, S / 2, 520);
  [0, 1, 2].forEach(i => drawStar(g, S / 2 + (i - 1) * 170, 650 - (i === 1 ? 20 : 0), 70, i < st));
  g.fillStyle = "#a0607e"; g.font = '700 46px "Nunito","Trebuchet MS",sans-serif'; g.fillText(`Score ${Number(sc || 0).toLocaleString()}`, S / 2, 800);
  idLine(g, S, 930);
  g.textAlign = "right"; g.fillStyle = "rgba(232,70,126,.85)"; g.font = '800 34px "Baloo 2","Trebuchet MS",sans-serif'; g.fillText("🌷 Flower Fever", S - 36, S - 34);
  return c.toDataURL("image/png");
}
async function gardenPng() {
  const f = farm(), W = 1080, H0 = Math.round(W * OV_H / OV_W), band = 290, c = document.createElement("canvas"); c.width = W; c.height = H0 + band; const g = c.getContext("2d");
  const bg = await loadImg(window.GARDEN_OVERVIEW || FARM_IMG.overview_nh); if (bg) g.drawImage(bg, 0, 0, W, H0);
  const box = b => [b.l / 100 * W, b.t / 100 * H0, b.w / 100 * W, b.h / 100 * H0];
  const hb = houseBox(f.house), hi = await loadImg(FARM_HOUSE[f.house]); if (hi) { const [x, y, w, h] = box(hb); g.drawImage(hi, x, y, w, h); }
  // a plant stands on the bottom of its cell, like in the game
  const plant = async (p, cell, kind) => {
    const st = plotState(p); if (st === "empty") return; const im = await loadImg(plotImg(p, st)); if (!im) return;
    const [x, y, w, h] = box(cell);
    if (kind === "bed") {
      const k = st === "sprout" ? [.12, .76, .14, .8] : st === "bud" ? [.08, .84, .10, 1] : [.04, .92, .08, 1.18];
      let dw = w * k[1], dh = dw * im.height / im.width; if (dh > h * k[3]) { dh = h * k[3]; dw = dh * im.width / im.height; }
      g.drawImage(im, x + w * k[0] + (w * k[1] - dw) / 2, y + h * (1 - k[2]) - dh, dw, dh);
    } else {
      const sc = st === "sprout" ? (kind === "tree" ? .45 : .8) : st === "bud" && kind === "tree" ? .65 : 1;
      let dw = w, dh = dw * im.height / im.width; if (dh > h) { dh = h; dw = dh * im.width / im.height; } dw *= sc; dh *= sc;
      g.drawImage(im, x + (w - dw) / 2, y + h - dh, dw, dh);
    }
  };
  for (let bi = 0; bi < BEDS.length; bi++) { const s = f.beds[bi]; if (!s.open) continue; for (let i = 0; i < BEDS[bi].cells.length; i++) if (s.plots[i]) await plant(s.plots[i], BEDS[bi].cells[i], "bed"); }
  if (XAREA_ON()) for (const [k, a] of Object.entries(XAREAS)) { const s = f.areas[k]; if (!s || !s.open) continue; for (let i = 0; i < a.cells.length; i++) if (s.plots[i]) await plant(s.plots[i], a.cells[i], a.kind); }
  const bb = g.createLinearGradient(0, H0, 0, H0 + band); bb.addColorStop(0, "#fff6fa"); bb.addColorStop(1, "#fde3ee"); g.fillStyle = bb; g.fillRect(0, H0, W, band);
  g.textAlign = "center"; g.fillStyle = "#5a2e44"; g.font = '800 64px "Baloo 2","Trebuchet MS",sans-serif';
  g.fillText(SOC() && save.nick ? `${save.nick}'s garden` : "My garden", W / 2, H0 + 78);
  g.fillStyle = "#a0607e"; g.font = '700 40px "Nunito","Trebuchet MS",sans-serif'; g.fillText(`Garden Level ${farmLevel(f.xp).lv} · Puzzle Level ${save.unlocked || 1}`, W / 2, H0 + 135);
  idLine(g, W, H0 + 196);
  g.textAlign = "center"; g.fillStyle = "rgba(232,70,126,.85)"; g.font = '800 34px "Baloo 2","Trebuchet MS",sans-serif'; g.fillText("🌷 Flower Fever", W / 2, H0 + band - 26);
  return c.toDataURL("image/png");
}
async function sharePng(png, file, text) {
  const N = window.FlowerFeverShare;
  if (N) { try { return await N.share(png, file, text); } catch (e) { return false; } }
  try { const blob = await (await fetch(png)).blob(), fl = new File([blob], file, { type: "image/png" });
    if (navigator.canShare && navigator.canShare({ files: [fl] })) { await navigator.share({ files: [fl], text }); return true; } } catch (e) { return false; }
  try { const a = document.createElement("a"); a.href = png; a.download = file; document.body.appendChild(a); a.click(); a.remove(); return true; } catch (e) { return false; }
}
function shareReward(btn) {   // the same once-a-day +1 diamond as sharing a bouquet
  const f = farm(), today = new Date().toDateString(); if (f.shareDay === today) return;
  f.shareDay = today; persist(); addGems(1); sfx("create");
  const s = btn && btn.querySelector("small"); if (s) s.remove();
  if (btn && btn.isConnected) { const r = btn.getBoundingClientRect(), d = document.createElement("div"); d.className = "socfloat"; d.innerHTML = `+1 <span class="fgem">${GEM_SVG}</span>`; d.style.left = (r.left + r.width / 2) + "px"; d.style.top = r.top + "px"; document.body.appendChild(d); setTimeout(() => d.remove(), 1400); }
}
const idText = () => SOC() && save.pid ? ` Visit my garden with my Player ID ${pidShow(save.pid)}.` : "";
async function shareWin(btn, lv, st, sc, ch) {
  btn.disabled = true; const keep = btn.innerHTML; btn.textContent = "Getting picture…";
  if (SOC()) { socEnsure(); socPublish(); }
  const png = await winPng(lv, st, sc);
  const ok = png && await sharePng(png, `flower-fever-level-${lv}.png`, `I finished Level ${lv} in Flower Fever! ${"⭐".repeat(st)}${idText()} 🌷 ${PLAY_URL}`);
  btn.disabled = false; btn.innerHTML = keep;
  if (ok) { track("share_win", { level: lv }); shareReward(btn); }
}
async function shareGarden(btn) {
  btn.disabled = true; const keep = btn.innerHTML; btn.textContent = "Getting picture…";
  if (SOC()) { socEnsure(); socPublish(); }
  const png = await gardenPng();
  const ok = png && await sharePng(png, "flower-fever-my-garden.png", `Come see my garden in Flower Fever! 🌷${idText()} ${PLAY_URL}`);
  btn.disabled = false; btn.innerHTML = keep;
  if (ok) { track("share_garden", {}); shareReward(btn); }
}

/* --- start: publish my profile, collect water gifts, and tell the player on the home screen --- */
setTimeout(async () => { if (!SOC()) return; socEnsure(); await socPublish(true); await socClaimAll(); socWatch(); }, 4000);
let socClaiming = false, socAgain = false;
async function socClaimAll() {   // both first, then one window
  if (socClaiming) { socAgain = true; return; }
  socClaiming = true;
  try { do { socAgain = false; await socClaimWater(); await socClaimCoins(); } while (socAgain); } finally { socClaiming = false; }
  const e = document.querySelector("#nFriends .h3new"); if (e) e.textContent = socBadge();
}
// gifts arrive live while the game is open (Firestore listeners on my water and coin gifts)
let socWatchPid = "", socUnwatch = [], socWatchT = 0;
async function socWatch() {
  const S = SOC(); if (!S || !S.watch || !save.pid || socWatchPid === save.pid) return;
  socUnwatch.forEach(f => f()); socUnwatch = []; socWatchPid = save.pid;
  const ping = n => { if (n > 0) { clearTimeout(socWatchT); socWatchT = setTimeout(socClaimAll, 600); } };
  for (const k of ["water", "coins"]) { try { socUnwatch.push(await S.watch(`profiles/${save.pid}/${k}`, ping)); } catch (e) { socWatchPid = ""; } }
}
setInterval(() => { if (socWaterNews && !socClaiming && homeOpen && overlay.hidden && !document.getElementById("gardenView")) showWaterNews(() => { hide(); showHome(); }); }, 2500);
document.addEventListener("visibilitychange", () => { if (!SOC()) return; if (document.hidden) socPublish(); else setTimeout(() => { socClaimAll(); socWatch(); }, 1500); });

'''
rep("/* ============ Home screen ============ */", code + "/* ============ Home screen ============ */")

css = """
/* SOCIAL_PATCH */
.h3fr{flex:none;font-size:calc(74 * var(--u));width:calc(104 * var(--u));text-align:center;line-height:1}
.h3new:not(:empty){background:#d8eefc!important;color:#1d5f8a}
.frcard{max-height:92vh;overflow:auto}
.frme{gap:6px!important}
.frme code{font:800 30px/1.1 ui-monospace,Menlo,monospace;letter-spacing:.12em;color:#5a2e44;user-select:all}
.frme span{font-size:15px!important}
.frlink{border:0;background:#fde3ee;color:#7a3a55;border-radius:999px;padding:3px 10px;font:800 13px/1.2 var(--body);cursor:pointer;margin-left:4px}
.frrow2{display:flex;gap:8px;width:100%;margin-top:6px}
.frrow2 .btn{flex:1;font-size:16px;padding:11px 8px 9px}
.frlabel{margin:14px 0 0;font:800 17px/1.2 var(--display);color:#5a2e44}
.frfind{display:flex;gap:8px;align-items:center}
.frfind .codein{flex:1;min-width:0;font-size:20px;margin:6px 0}
.frfind .btn{flex:none;font-size:18px;padding:13px 16px 10px}
#frMsg:empty{display:none}
.frlist{display:flex;flex-direction:column;gap:8px;margin:8px 0 4px}
.frow{display:flex;align-items:center;gap:6px;background:#fff;border-radius:16px;padding:6px 8px;box-shadow:inset 0 -2px 0 #f3d6e2}
.frvisit{flex:1;min-width:0;display:flex;align-items:center;gap:10px;border:0;background:none;padding:2px;text-align:left;cursor:pointer;color:inherit}
.frvisit img{width:44px;height:44px;flex:none}
.frvisit span{display:flex;flex-direction:column;min-width:0}
.frvisit b{font:800 18px/1.15 var(--display);color:#5a2e44;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.frvisit small{font:700 13px/1.25 var(--body);color:#9a6a80}
.frwater{flex:none;width:52px;height:46px;border:0;border-radius:14px;background:linear-gradient(180deg,#8fd3ff,#4aa8e8);box-shadow:0 4px 0 #2f7fbf;font-size:24px;cursor:pointer}
.frgift{flex:none;width:52px;height:46px;border:0;border-radius:14px;background:linear-gradient(180deg,#ffd77a,#f3a72a);box-shadow:0 4px 0 #c27a12;font-size:24px;cursor:pointer}
.frdone{flex:none;font-style:normal;font:800 14px/1 var(--body);color:#3a9a3e;width:44px;text-align:center}
.frow .frwater,.frow .frgift{width:46px}
.frdel{flex:none;border:0;background:none;color:#c9a3b5;font-size:18px;padding:6px;cursor:pointer}
.codein.nickin{text-transform:none;letter-spacing:0;font:800 22px/1.1 var(--display)}
.frempty{background:#fff;border-radius:16px;padding:14px;margin:0;font:700 15px/1.4 var(--body);color:#8a5e6e}
.wshare{display:flex;align-items:center;justify-content:center;gap:6px;margin:12px auto 0;border:0;border-radius:999px;background:#fff;box-shadow:inset 0 -1.7px 0 #f3d6e2,0 3.9px 0 #f0bfd2;font:800 17px/1 var(--display);color:#7a3a55;cursor:pointer;padding:12px 22px 10px}
.wshare small{font-size:14px}
.wdrops{font-size:44px;letter-spacing:.1em;margin:4px 0 0}
.farm .fvname{max-width:46%;overflow:hidden;white-space:nowrap;font:800 17px/1 var(--display);color:#5a2e44;padding:8px 12px}
.farm .fvname b{overflow:hidden;text-overflow:ellipsis}
.farm.fvisit .fbtns .btn{flex:1 1 28%;padding-left:6px;padding-right:6px;font-size:17px;display:flex;align-items:center;justify-content:center;gap:3px;white-space:nowrap}
.farm.fvisit .fbtns .btn .fcoin{width:20px;height:20px}
.farm .fbtns .btn.fgift{background:linear-gradient(180deg,#ffd77a,#f3a72a);color:#5a3a10;box-shadow:inset 0 2px 0 rgba(255,255,255,.4),0 5px 0 #c27a12}
.farm .fbtns .btn.fwater{background:linear-gradient(180deg,#8fd3ff,#4aa8e8);box-shadow:inset 0 2px 0 rgba(255,255,255,.4),0 5px 0 #2f7fbf}
.farm.fvisit .fplot,.farm.fvisit .fareabtn{cursor:default}
.farm.fvisit .fplot:disabled,.farm.fvisit .fareabtn:disabled{opacity:1;color:inherit}
.fdrop{position:absolute;top:-6%;font-style:normal;font-size:26px;z-index:6;pointer-events:none;animation:fdropFall 1.5s ease-in forwards}
@keyframes fdropFall{from{transform:translateY(0);opacity:0}15%{opacity:1}to{transform:translateY(560%);opacity:0}}
.socfloat{position:fixed;z-index:60;transform:translate(-50%,-100%);font:800 22px/1 var(--display);color:#3a9a3e;pointer-events:none;animation:socUp 1.3s ease-out forwards}
@keyframes socUp{to{transform:translate(-50%,-260%);opacity:0}}
"""
src = src.replace("</style>", css + "</style>", 1)

path.write_text(src)
print("Player ID, friends' gardens, water gifts and sharing added")
