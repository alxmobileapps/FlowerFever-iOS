"""Home: Daily Gift and Weekly Challenge share one row (two half cards) when the weekly challenge is open.
Without a weekly challenge the Daily Gift row stays full width. Runs after the other home patches."""
from pathlib import Path

path = Path("www/index.html")
src = path.read_text()
if "HOME_ROWS_PATCH" in src:
    print("home rows patch already applied"); raise SystemExit(0)

def rep(before, after, count=1):
    global src
    n = src.count(before)
    if n != count:
        raise RuntimeError(f"patch-home-rows: expected {count} of: {before[:90]!r}, found {n}")
    src = src.replace(before, after)

gift_btn = """${daily ? `<button class="h3collect" id="hCollect">Collect</button>` : adGemsLeft() ? `<button class="h3collect" id="hAd">▶ +${AD_GEMS}</button>` : `<button class="h3collect" id="hShop">Shop</button>`}"""
old = """    <div class="h3gift"><img alt="" src="${HOME_IMG.gift}"><span class="h3div"></span>
      <div class="h3gt"><b>Daily Gift</b><span>${daily ? `Day ${dailyAmount().day + 1}: ${dailyAmount().n} free diamond${dailyAmount().n > 1 ? "s" : ""}` : `Next gift in ${fmtWait(msToTomorrow())}`}</span></div>
      """ + gift_btn + """</div>
    ${weeklyLevel() >= 0 ? `<button class="h3row h3week" id="nWeek"><b class="h3trophy" aria-hidden="true">🏆</b><span>Weekly Challenge</span><em>${save.weekly === weekKey() ? "Done ✓" : "+10 💎"}</em><i>›</i></button>` : ""}"""
new = """    ${weeklyLevel() >= 0 ? `<div class="h3duo">
      <div class="h3gift h3half"><img alt="" src="${HOME_IMG.gift}"><div class="h3gt"><b>Daily Gift</b><span>${daily ? `Day ${dailyAmount().day + 1}: +${dailyAmount().n} 💎` : `Next in ${fmtWait(msToTomorrow())}`}</span></div>""" + gift_btn + """</div>
      <button class="h3row h3week h3half" id="nWeek"><b class="h3trophy" aria-hidden="true">🏆</b><span class="h3gt"><b>Weekly Challenge</b><span>${save.weekly === weekKey() ? "Done this week ✓" : "Win +10 💎"}</span></span><em class="h3wgo">${save.weekly === weekKey() ? "Play again" : "Play ›"}</em></button>
    </div>` : `<div class="h3gift"><img alt="" src="${HOME_IMG.gift}"><span class="h3div"></span>
      <div class="h3gt"><b>Daily Gift</b><span>${daily ? `Day ${dailyAmount().day + 1}: ${dailyAmount().n} free diamond${dailyAmount().n > 1 ? "s" : ""}` : `Next gift in ${fmtWait(msToTomorrow())}`}</span></div>
      """ + gift_btn + """</div>`}"""
rep(old, new)

css = """
/* HOME_ROWS_PATCH: Daily Gift | Weekly Challenge in one row */
.h3duo{display:flex;gap:calc(22 * var(--u));width:calc(871 * var(--u));margin-top:calc(26 * var(--u))}
.h3duo .h3half{flex:1 1 0;min-width:0;width:auto!important;height:auto!important;min-height:calc(210 * var(--u));margin:0!important;display:grid!important;grid-template-columns:auto 1fr;grid-template-rows:1fr auto;align-items:center;gap:calc(12 * var(--u)) calc(14 * var(--u));padding:calc(18 * var(--u)) calc(20 * var(--u))!important;box-sizing:border-box;text-align:left}
.h3duo .h3half>img{width:calc(92 * var(--u))}
.h3duo .h3half .h3gt{min-width:0}
.h3duo .h3half .h3gt b{font-size:calc(40 * var(--u));line-height:1.05;white-space:normal}
.h3duo .h3half .h3gt span{font-size:calc(28 * var(--u));white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.h3duo .h3half .h3collect,.h3duo .h3half .h3wgo{grid-column:1/-1;width:100%;min-width:0;height:calc(72 * var(--u));box-sizing:border-box}
.h3duo .h3week .h3trophy{font-size:calc(70 * var(--u))!important;width:calc(92 * var(--u))!important}
.h3duo .h3week>.h3gt span{color:#8a5e6e;font-weight:600}
.h3duo .h3week .h3wgo{display:flex;align-items:center;justify-content:center;font-style:normal;font-weight:800;font-size:calc(36 * var(--u))!important;border-radius:calc(40 * var(--u));padding:0!important;background:linear-gradient(180deg,#ffd77a,#f3a72a)!important;color:#5a3a10!important;box-shadow:0 calc(4 * var(--u)) 0 #c27a12}
"""
src = src.replace("</style>", css + "</style>", 1)
path.write_text(src)
print("Home: Daily Gift and Weekly Challenge in one row")
