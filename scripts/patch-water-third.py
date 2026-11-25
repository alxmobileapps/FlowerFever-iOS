#!/usr/bin/env python3
"""Water is earned at one third of the old rate (Nov 25 2026).
Every water reward (3-star wins, gift levels, chapters, harvests, bouquets, albums, garden level-ups) now
adds thirds of a drop; every 3 thirds become 1 drop. The game only ever shows the whole drops really added.
Water between friends (watering a friend's garden, sending a flower, gifts received) is unchanged.
Water players already have is kept. Runs after patch-win-revamp.py."""
import pathlib, sys

p = pathlib.Path(__file__).resolve().parent.parent / "www" / "index.html"
s = p.read_text(encoding="utf-8")


def swap(old, new, count=1):
    global s
    if s.count(old) != count:
        sys.exit(f"patch-water-third: expected {count} of {old[:70]!r}, found {s.count(old)}")
    s = s.replace(old, new)


# the one place water is earned: thirds are kept in farm().wq
swap("function farmReward(coins, water) { const f = farm(); f.coins += coins; f.water += water || 0; persist(); }",
     "function addWater(n) { const f = farm(); f.wq = (f.wq || 0) + (n || 0); const whole = Math.floor(f.wq / 3); f.wq -= whole * 3; f.water += whole; return whole; }   // WATER_THIRD_PATCH\n"
     "function farmReward(coins, water) { const f = farm(); f.coins += coins; const got = addWater(water || 0); persist(); return got; }")

# level complete: the window shows only the drops really added
swap("const fcGain = wasCh ? 0 : firstWin ? 15 + 5 * st : 5, wGain = !wasCh && st === 3 ? 1 : 0; if (fcGain) farmReward(fcGain, wGain);",
     "const fcGain = wasCh ? 0 : firstWin ? 15 + 5 * st : 5; let wGain = !wasCh && st === 3 ? 1 : 0; wGain = fcGain ? farmReward(fcGain, wGain) : 0;")
swap("farmReward(100, 3); giftFc = 100; giftW = 3;", "giftW = farmReward(100, 3); giftFc = 100;")
swap("farmReward(SPROUT_COINS, 1); giftFc = SPROUT_COINS; giftW = 1;", "giftW = farmReward(SPROUT_COINS, 1); giftFc = SPROUT_COINS;")

# garden: harvest, sell, pick all, bouquet, album, level-up gift
swap("f.water += wb;", "const wGot = addWater(wb);", count=2)
swap('${wb ? " 💧+1" : ""}', '${wGot ? ` 💧+${wGot}` : ""}', count=2)
swap('f.water += w; persist(); sfx("create"); track("garden_pick_all"', 'w = addWater(w); persist(); sfx("create"); track("garden_pick_all"')
swap("f.stk[b.no] = 1; f.water += 1;", "f.stk[b.no] = 1; const bqW = addWater(1);")
swap("💐 +5 XP · 💧+1</p>", "💐 +5 XP${bqW ? ` · 💧+${bqW}` : \"\"}</p>")
swap("f.albDone[a] = 1; f.water += w;", "f.albDone[a] = 1; const wGot = addWater(w);")
swap("<b>+${g}</b> · 💧<b>+${w}</b> · ${FC_SVG}", "<b>+${g}</b> · ${wGot ? `💧<b>+${wGot}</b> · ` : \"\"}${FC_SVG}")
swap("<p>Gift: 💧 +2 water</p>", "${(() => { const g = addWater(2); return g ? `<p>Gift: 💧 +${g} water</p>` : \"\"; })()}")
swap('</div>`); f.water += 2; persist(); bar(); }, 700);', '</div>`); persist(); bar(); }, 700);')

# texts that named the old amounts
swap("Your garden gift is here: ${FC_SVG}<b>+100</b> and 💧<b>+3</b></p>", "Your garden gift is here: ${FC_SVG}<b>+100</b> and 💧 water</p>")
swap("gives a gift (+20 flower coins and +1 water)", "gives a gift (+20 flower coins and water)")
swap("for a garden gift (+100 flower coins and +3 water)", "for a garden gift (+100 flower coins and water)")
swap("`your next gift: ${FC_SVG}+${SPROUT_COINS} 💧+1`", "`your next gift: ${FC_SVG}+${SPROUT_COINS} 💧`")

p.write_text(s, encoding="utf-8")
print("water: earned at 1/3 (thirds kept), friends' water unchanged")
