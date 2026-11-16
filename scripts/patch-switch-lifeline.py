"""Special lifeline "Switch": swap any two flowers anywhere on the board (they don't have to be neighbours).

- 4th choice in "Pick a lifeline", marked SPECIAL, always 25 diamonds (not free, not the usual lifeline price).
- Once per level. The diamonds are taken only when the switch is actually made (picking it and then
  putting it away costs nothing).
- Tap a flower, then any other flower: they trade places, and any matches that forms go off.
  It doesn't use a move. Ice-covered flowers can't be switched.
Runs after the .patch files (it edits the final www/index.html).
"""
from pathlib import Path

path = Path("www/index.html")
src = path.read_text()
if "SWITCH_LIFELINE_PATCH" in src:
    print("switch lifeline patch already applied"); raise SystemExit(0)

def rep(before, after):
    global src
    if src.count(before) != 1:
        raise RuntimeError("patch-switch-lifeline: code changed: " + before[:70])
    src = src.replace(before, after)

# a hidden tray button that holds the icon (LIFE_IMG reads the picture from it)
rep("""const LIFE_IMG = k => ($({ shovel: "#bShovel", swap: "#bSwap", magic: "#bMagic" }[k]).querySelector("img") || {}).src || "";""",
    """const LIFE_IMG = k => ($({ shovel: "#bShovel", swap: "#bSwap", magic: "#bMagic", switch: "#bSwitch" }[k]).querySelector("img") || {}).src || "";""")
rep("""const BOOST_NAME = { shovel: "Garden trowel",""", """const BOOST_NAME = { switch: "Switch", shovel: "Garden trowel",""")
rep("""const BOOST_DESC = { shovel:""", """const BOOST_DESC = { switch: "Swap any two flowers anywhere on the board. Once per level.", shovel:""")
rep("""<button class="tbtn" id="bSwap" hidden""", """<button class="tbtn" id="bSwitch" hidden aria-label="Switch"><img alt="" src=""></button><button class="tbtn" id="bSwap" hidden""")

code = r"""
// SWITCH_LIFELINE_PATCH: special lifeline, two flowers anywhere trade places
const SWITCH_COST = 25;
let switchUsed = false;
(function drawSwitchIcon() {
  const S = 160, cv = document.createElement("canvas"); cv.width = cv.height = S; const g = cv.getContext("2d");
  const bg = g.createRadialGradient(S * .45, S * .38, 10, S / 2, S / 2, S * .5); bg.addColorStop(0, "#c9a5ff"); bg.addColorStop(1, "#7a3fe0");
  g.fillStyle = bg; g.beginPath(); g.arc(S / 2, S / 2, S * .46, 0, Math.PI * 2); g.fill(); g.lineWidth = 8; g.strokeStyle = "#fff"; g.stroke();
  const flower = (x, y, col) => { g.fillStyle = col; for (let i = 0; i < 5; i++) { const a = i * Math.PI * 2 / 5; g.beginPath(); g.arc(x + Math.cos(a) * 11, y + Math.sin(a) * 11, 10, 0, Math.PI * 2); g.fill(); } g.fillStyle = "#ffd23a"; g.beginPath(); g.arc(x, y, 7, 0, Math.PI * 2); g.fill(); };
  flower(S * .3, S * .32, "#ff7eb0"); flower(S * .7, S * .68, "#5ec3ff");
  g.strokeStyle = "#fff"; g.lineWidth = 9; g.lineCap = "round";
  const arrow = (x1, y1, x2, y2, bend) => { g.beginPath(); g.moveTo(x1, y1); g.quadraticCurveTo((x1 + x2) / 2 + bend, (y1 + y2) / 2 - bend, x2, y2); g.stroke();
    const a = Math.atan2(y2 - ((y1 + y2) / 2 - bend), x2 - ((x1 + x2) / 2 + bend)); g.beginPath(); g.moveTo(x2, y2); g.lineTo(x2 - 16 * Math.cos(a - .5), y2 - 16 * Math.sin(a - .5)); g.moveTo(x2, y2); g.lineTo(x2 - 16 * Math.cos(a + .5), y2 - 16 * Math.sin(a + .5)); g.stroke(); };
  arrow(S * .5, S * .26, S * .76, S * .46, 14); arrow(S * .5, S * .74, S * .24, S * .54, -14);
  const im = document.querySelector("#bSwitch img"); if (im) im.src = cv.toDataURL();
})();
async function pickSwitch() {
  if (switchUsed) { busy = true; show(`<div class="ribbon">Switch</div><h2>Already used</h2><p>You can use Switch once per level.</p><div class="btns"><button class="btn" id="lfNo">OK</button></div>`, el => el.querySelector("#lfNo").onclick = () => { hide(); busy = false; lastInput = T(); }); return; }
  busy = true;
  const gems = save.gems || 0;
  const how = await new Promise(res => show(`<div class="ribbon">Switch <span class="llsp">SPECIAL</span></div>${gemBal()}<h2>Switch two flowers?</h2><p>${BOOST_DESC.switch}</p>
    <div class="btns">${gems >= SWITCH_COST ? `<button class="btn lfgem" id="lfGem">${GEM_SVG}<span>Use ${SWITCH_COST} diamonds</span></button>` : `<p class="llnote">You need ${SWITCH_COST} diamonds.</p><button class="btn lfgem" id="lfShop">${GEM_SVG}<span>Get diamonds</span></button>`}
    <button class="btn alt" id="lfNo">Not now</button></div>`, el => {
      const on = (id, v) => { const x = el.querySelector(id); if (x) x.onclick = () => res(v); }; on("#lfGem", "gem"); on("#lfShop", "shop"); on("#lfNo", null); }));
  if (how === "shop") { const ok = await new Promise(res => showGems(r => res(r), SWITCH_COST)); if (!ok || (save.gems || 0) < SWITCH_COST) { hide(); busy = false; lastInput = T(); return; } }
  else if (!how) { hide(); busy = false; lastInput = T(); return; }
  hide(); busy = false; lastInput = T();
  boosterMode = "switch"; selected = null; swapFirst = null; syncTray(); praise("Tap two flowers");
}
async function doSwitch(r1, c1, r2, c2) {
  if ((save.gems || 0) < SWITCH_COST) { boosterMode = null; syncTray(); pickSwitch(); return; }
  busy = true; addGems(-SWITCH_COST); switchUsed = true; boosterMode = null; syncTray(); chainCount = 0; comboLevel = 1;
  track("lifeline_use", { type: "switch", pay: "gem", level: levelIdx + 1 });
  const a = grid[r1][c1], b = grid[r2][c2];
  grid[r1][c1] = b; grid[r2][c2] = a; a.r = r2; a.c = c2; b.r = r1; b.c = c1;
  moveTween(a, r2, c2, 520); moveTween(b, r1, c1, 520); sfx("swap"); haptic("boom");
  sparkleAt(r1, c1, 10); sparkleAt(r2, c2, 10); fxRing(r1, c1, 0, 2); fxRing(r2, c2, 0, 2);
  await sleep(560);
  if (findGroups().length) await resolve([[r2, c2], [r1, c1]]);
  await afterTurn();
}
"""
rep("""function openLifeline() {""", code + """function openLifeline() {""")

# the picker: a 4th, special choice
rep("""<div class="llbig">${["shovel", "swap", "magic"].map(k => `<button class="llb" data-k="${k}"><img alt="" src="${LIFE_IMG(k)}"><span><b>${BOOST_NAME[k]}</b><small>${BOOST_DESC[k]}</small></span></button>`).join("")}</div>""",
    """<div class="llbig">${["shovel", "swap", "magic"].map(k => `<button class="llb" data-k="${k}"><img alt="" src="${LIFE_IMG(k)}"><span><b>${BOOST_NAME[k]}</b><small>${BOOST_DESC[k]}</small></span></button>`).join("")}
      <button class="llb llspecial${switchUsed ? " used" : ""}" data-k="switch"><img alt="" src="${LIFE_IMG("switch")}"><span><b>${BOOST_NAME.switch} <i class="llsp">SPECIAL</i></b><small>${BOOST_DESC.switch}</small><em>${switchUsed ? "Used this level" : `${GEM_SVG} ${SWITCH_COST} diamonds`}</em></span></button></div>""")
rep("""    ok.onclick = () => { if (!pick) return; hide(); busy = false; useBooster(pick); };""",
    """    ok.onclick = () => { if (!pick) return; hide(); busy = false; if (pick === "switch") pickSwitch(); else useBooster(pick); };""")

# tapping the board while Switch is on
rep("""  if (boosterMode === "swap") {
    if (swapFirst &&""", """  if (boosterMode === "switch") {
    const p = grid[r][c];
    if (!p || p.frozen) { if (p) p.nope = T(); sfx("bad"); return; }
    if (!swapFirst) { swapFirst = [r, c]; selected = [r, c]; sfx("pick"); return; }
    if (swapFirst[0] === r && swapFirst[1] === c) { swapFirst = null; selected = null; return; }
    const f = swapFirst; swapFirst = null; selected = null; doSwitch(f[0], f[1], r, c); return;
  }
  if (boosterMode === "swap") {
    if (swapFirst &&""")

# once per level: reset when a level starts
rep("""  lifelineUsed = false; lifelineHinted = false; adLifeUsed = false; lifePaidUses = 0;""",
    """  lifelineUsed = false; lifelineHinted = false; adLifeUsed = false; lifePaidUses = 0; switchUsed = false;""")

css = """.llspecial{box-shadow:0 0 0 2px #b58cff,0 3px 0 #9a6ae8!important;background:linear-gradient(180deg,#fff,#f5efff)!important}
.llspecial em{display:block;font:800 13px/1.2 Nunito,sans-serif;font-style:normal;color:#6a3fc0;margin-top:3px}.llspecial em svg{width:14px;height:14px;vertical-align:-2px}
.llspecial.used{opacity:.55}
.llsp{display:inline-block;font:800 10px/1 Nunito,sans-serif;font-style:normal;letter-spacing:.06em;color:#fff;background:linear-gradient(180deg,#a678ff,#7a3fe0);border-radius:999px;padding:3px 7px;vertical-align:2px;margin-left:4px}
"""
rep(""".llbig{display:flex;flex-direction:column;gap:8px;margin:8px 0 6px}""", """.llbig{display:flex;flex-direction:column;gap:8px;margin:8px 0 6px}""" + css)

path.write_text(src)
print("switch lifeline patch applied")
