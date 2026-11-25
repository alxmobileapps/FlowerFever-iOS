#!/usr/bin/env python3
"""Level-complete window, made simpler for older players (approved Nov 25 2026):
  - smaller stars (the sunshine behind them stays); no row of goal tiles
  - one coin total: the level's coins plus any gift-level / chapter garden coins and water
  - a small green "watch a video: x2" button right beside the coins (it doubles the whole coin total);
    the first time ever, a short window explains it before the video
  - Next level, then four same-size buttons in two rows: Garden, Home, Share (+1 diamond), Replay
    (Map and the chapter's "Open My Garden" are gone; on gift levels the Garden button has a green running light)
  - no banner ad while this window is open
  - free lifelines from gifts are capped at 3 (bought ones are not capped)
Runs last, after every other patch."""
import pathlib, re, sys

p = pathlib.Path(__file__).resolve().parent.parent / "www" / "index.html"
s = p.read_text(encoding="utf-8")


def swap(old, new, count=1):
    global s
    if s.count(old) != count:
        sys.exit(f"patch-win-revamp: expected {count} of {old[:70]!r}, found {s.count(old)}")
    s = s.replace(old, new)


# ---- styles
swap("</head>", """<style>
.win .wstars{height:58px}
.win .wstars .rays{width:160px;height:160px;margin:-80px}
.win .wstars span{font-size:40px}
.win .wstars span:nth-child(3){font-size:52px;margin-bottom:4px}
.wrow{display:flex;justify-content:center;align-items:center;gap:10px;margin:6px 0 12px}
.wrow .wgems{margin:0}
.wx2{display:flex;align-items:center;gap:5px;height:40px;padding:0 12px 0 10px;border:0;border-radius:20px;background:linear-gradient(#7fd068,#4caf3e);color:#fff;font:900 19px "Baloo 2",sans-serif;box-shadow:inset 0 1.8px 0 rgba(255,255,255,.45),0 4px 0 #2f7d24;text-shadow:0 1px 0 rgba(0,0,0,.15);cursor:pointer}
.wx2:active{transform:translateY(3px);box-shadow:0 1px 0 #2f7d24}
.wx2:disabled{opacity:.6}
.wx2 .tv{width:26px;height:26px}
.wx2 svg:not(.tv){width:22px;height:22px}
.wgrid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;margin-top:16px}
.wgb{height:60px;border:0;border-radius:20px;background:#fff;color:#7a3a55;font:800 21px "Baloo 2",sans-serif;display:flex;align-items:center;justify-content:center;gap:7px;padding:0 6px;box-shadow:inset 0 -1.8px 0 #f3d6e2,0 4px 0 #f0bfd2;cursor:pointer}
.wgb:active{transform:translateY(3px);box-shadow:0 1px 0 #f0bfd2}
.wgb svg,.wgb img{width:29px;height:29px;flex-shrink:0}
.wgb small{font-size:16px;margin-left:0}
.wgb small+svg{width:22px;height:22px;margin-left:-4px}
@property --wa{syntax:'<angle>';inherits:false;initial-value:0deg}
.wgb.wglow{position:relative;color:#2f7d24;box-shadow:inset 0 -1.8px 0 #d3ecc8,0 4px 0 #a9d99a,0 0 14px rgba(90,200,70,.45)}
.wgb.wglow::before{content:"";position:absolute;inset:-4px;border-radius:24px;padding:4px;background:conic-gradient(from var(--wa),transparent 0 62%,#b8f5a4 74%,#4cc23a 86%,transparent 100%);-webkit-mask:linear-gradient(#000 0 0) content-box,linear-gradient(#000 0 0);-webkit-mask-composite:xor;mask-composite:exclude;animation:wrun 1.8s linear infinite;pointer-events:none}
@keyframes wrun{to{--wa:360deg}}
@media (prefers-reduced-motion:reduce){.wgb.wglow::before{animation:none;background:#4cc23a}}
</style></head>""")

# ---- no goal tiles
swap("""  const recap = goals.filter(g => g.icon).map(g => `<span class="wg"><img alt="" src="${g.icon}"><i>✓</i></span>`).join("");\n""", "")
swap("""    ${recap ? `<div class="wrecap">${recap}</div>` : ""}\n""", "")

# ---- gifts: amounts go into the one coin total; free lifelines capped at 3; no "Open My Garden"
swap("  save.rewarded = save.rewarded || {};\n", "  save.rewarded = save.rewarded || {};\n  let giftFc = 0, giftW = 0;\n")
swap("    save.freeLife = freeLives() + 1; save.rewarded[levelIdx] = 1;\n    farmReward(100, 3);",
     "    const lifeGift = freeLives() < 3; if (lifeGift) save.freeLife = freeLives() + 1; save.rewarded[levelIdx] = 1;\n    farmReward(100, 3); giftFc = 100; giftW = 3;")
swap("""Garden gift: <b>${FC_SVG}+100</b> and <b>💧+3</b> added 🌷<br>Gift: your next lifeline is <b>free</b> 🎁""",
     """Your garden gift is added 🌷<br>${lifeGift ? "Gift: your next lifeline is <b>free</b> 🎁" : "You already have 3 free lifelines 🎁"}""")
swap("""<button class="btn plantbtn" id="plant">🌷 Open My Garden</button></div>`;""", """</div>`;""")
swap("save.rewarded[levelIdx] = 1; farmReward(SPROUT_COINS, 1);", "save.rewarded[levelIdx] = 1; farmReward(SPROUT_COINS, 1); giftFc = SPROUT_COINS; giftW = 1;")
swap("""      <b>${FC_SVG}+${SPROUT_COINS}</b> · <b>💧+1</b><br>Finish <b>Level""", """      Finish <b>Level""")
swap("if (save.boostGift) { save.freeLife = freeLives() + 1;", "if (save.boostGift) { save.freeLife = Math.min(3, freeLives() + 1);")

# ---- one coin total, with the small video button beside it
swap("  let fcDoubled = false;\n", "  let fcDoubled = false;\n  const coinTot = fcGain + giftFc, waterTot = wGain + giftW;\n  winOpen = true; syncBanner();\n")
swap("""    ${fcGain ? `<div class="wgems wfc">${FC_SVG}<b>+${fcDoubled ? fcGain * 2 : fcGain}</b>${fcDoubled ? " (x2!)" : ""}${wGain ? " · 💧+1" : ""}</div>` : ""}""",
     """    ${coinTot || waterTot ? `<div class="wrow"><div class="wgems wfc">${coinTot ? `${FC_SVG}<b>+${fcDoubled ? coinTot * 2 : coinTot}</b>${fcDoubled ? " (x2!)" : ""}` : ""}${coinTot && waterTot ? " · " : ""}${waterTot ? `💧+${waterTot}` : ""}</div>${coinTot && !bonusDone && adLeft("x2") ? `<button class="wx2" id="wBonus" aria-label="Watch a video to double your coins"><svg class="tv" viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="#fff" stroke-width="2" stroke-linejoin="round"><rect x="2.5" y="5" width="19" height="14" rx="3"/><path d="M10 9.2v5.6l4.8-2.8z" fill="#fff"/></svg><b>x2</b>${FC_SVG}</button>` : ""}</div>` : ""}""")
swap("""    ${!fcGain ? "" : bonusDone ? `<div class="wbonus wdone">x2! +${fcGain} more ${FC_SVG} added</div>` : adLeft("x2") ? `<button class="btn alt wbonus" id="wBonus">▶ Watch ad: x2 ${FC_SVG}</button>` : ""}\n""", "")
swap("""const wb = el.querySelector("#wBonus"); if (wb) wb.onclick = async () => { wb.disabled = true; const ok = await watchAd("bonus"); if (ok) { adUsed("x2"); farmReward(fcGain, 0);""",
     """const wb = el.querySelector("#wBonus"); if (wb) wb.onclick = async () => { wb.disabled = true;
        if (!save.x2Seen) {   // the first time, say what the little video button does
          const go = await new Promise(res => show(`<div class="ribbon">Double your coins</div><h2>Watch a short video?</h2><p>Watch a short video to get <b>${FC_SVG}+${coinTot}</b> more coins.</p><div class="btns"><button class="btn" id="x2Go">▶ Watch video</button><button class="btn alt" id="x2No">Not now</button></div>`,
            e2 => { e2.querySelector("#x2Go").onclick = () => res(true); e2.querySelector("#x2No").onclick = () => res(false); }));
          save.x2Seen = 1; persist();
          if (!go) { render(); return; }
        }
        const ok = await watchAd("bonus"); if (ok) { adUsed("x2"); farmReward(coinTot, 0);""")

# ---- Next level, then Garden / Home / Share / Replay, all the same size (no Map)
m = re.search(r'    <div class="wsec">.*?</div>\n    <button class="wshare" id="wShare">.*?</button>\n', s)
if not m or s.count('<div class="wsec">') != 1:
    sys.exit("patch-win-revamp: win buttons changed; review before building")
s = s[:m.start()] + """    <div class="wgrid">
      <button class="wgb${giftFc ? " wglow" : ""}" id="wGarden" aria-label="My garden"><img alt="" src="${HOME_IMG.sproutpot}">Garden</button>
      <button class="wgb" id="wHome" aria-label="Home"><svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linejoin="round" stroke-linecap="round"><path d="M3.5 11 12 4l8.5 7"/><path d="M6 9.5V20h4.5v-5.5h3V20H18V9.5"/></svg>Home</button>
      <button class="wgb" id="wShare"><svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M12 15V3.5"/><path d="M7.5 8 12 3.5 16.5 8"/><path d="M5 12.5V19a1.5 1.5 0 0 0 1.5 1.5h11A1.5 1.5 0 0 0 19 19v-6.5"/></svg>Share${shareBonusToday() ? ` <small>+1</small>${GEM_SVG}` : ""}</button>
      <button class="wgb" id="again" aria-label="Play again"><svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M19.5 12a7.5 7.5 0 1 1-2.2-5.3"/><path d="M19.8 3.8v4.6h-4.6"/></svg>Replay</button>
    </div>
""" + s[m.end():]
swap("""      el.querySelector("#map").onclick = () => showMap(() => startLevel(Math.min(LEVELS.length - 1, levelIdx + 1)));\n""", "")

# ---- no banner ad while the level-complete window is open
swap("let bannerOn = null, booted = false;", "let bannerOn = null, booted = false, winOpen = false;")
swap("const want = adsAllowed() && !gardenOpen && !homeOpen && !mapOpen && booted &&", "const want = adsAllowed() && !winOpen && !gardenOpen && !homeOpen && !mapOpen && booted &&")
swap("  levelIdx = i; syncBanner();", "  winOpen = false; levelIdx = i; syncBanner();")

p.write_text(s, encoding="utf-8")
print("win window: smaller stars, one coin total + small x2 video button, 4 same-size buttons, no banner; gift lifelines max 3")
