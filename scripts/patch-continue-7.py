"""Continue gives +7 moves; the "Hurry!" warning comes at 4 moves left after a continue (was 2);
right after the warning, a light runs around the lifeline button until all goals are done (or the level ends).
Runs after the .patch files (it edits the final www/index.html).
"""
from pathlib import Path

path = Path("www/index.html")
src = path.read_text()
if "CONTINUE7_PATCH" in src:
    print("continue +7 patch already applied"); raise SystemExit(0)

def rep(before, after, count=1):
    global src
    n = src.count(before)
    if n != count:
        raise RuntimeError(f"patch-continue-7: expected {count} of {before[:60]!r}, found {n}")
    src = src.replace(before, after)

rep('moves: "+5 moves"', 'moves: "+7 moves"')
rep("Tip: continuing with +5 moves keeps your progress.", "Tip: continuing with +7 moves keeps your progress.", 2)
rep("Watch ad: +5 moves", "Watch ad: +7 moves")
rep("Continue: +5 moves", "Continue: +7 moves")
rep("Continuing with +5 moves costs", "Continuing with +7 moves costs")
rep("moves += 5; hurried = false;", "moves += 7; hurried = false;", 3)
rep("""moves <= (continued ? 2 : 5) && !goalsDone()) { hurried = true; praise("Hurry!"); sfx("hurry"); setTimeout(movesLeftFly, 650); }""",
    """moves <= (continued ? 4 : 5) && !goalsDone()) { hurried = true; praise("Hurry!"); sfx("hurry"); setTimeout(movesLeftFly, 650); flashLifeline(); }""")
rep("function hideLifelineTip() {", """// CONTINUE7_PATCH: after the "Hurry!" warning a light runs around the lifeline button until the goals are done
let lifeFlashT = 0, lifeFlashLv = -1, lifeLvTok = 0;
function stopLifeFlash() { clearInterval(lifeFlashT); lifeFlashT = 0; const b = document.getElementById("bLife"); if (b) b.classList.remove("llflash"); }
function flashLifeline() {
  const b = document.getElementById("bLife"); if (!b) return;
  stopLifeFlash(); lifeFlashLv = lifeLvTok;
  setTimeout(() => { if (lifeFlashLv === lifeLvTok && !goalsDone()) b.classList.add("llflash"); }, 900);
  lifeFlashT = setInterval(() => { if (goalsDone() || lifeFlashLv !== lifeLvTok || !b.isConnected) stopLifeFlash(); }, 500);   // cheap check, twice a second
}
function hideLifelineTip() {""")
rep("function startLevel(i, asChallenge = false) {", "function startLevel(i, asChallenge = false) {\n  stopLifeFlash(); lifeLvTok++;")
rep(".llbig{display:flex;", """/* running light: one small ring layer; only its gradient angle moves (no layout, no big repaints) */
@property --llrun{syntax:"<angle>";inherits:false;initial-value:0deg}
#bLife.llflash::before{content:"";position:absolute;inset:-8px;border-radius:20px;padding:5px;pointer-events:none;z-index:1;
  background:conic-gradient(from var(--llrun),transparent 0 22%,#ff4f9a 34%,#fff 49%,transparent 50% 72%,#ff4f9a 84%,#fff 99%,transparent 100%);
  -webkit-mask:linear-gradient(#000 0 0) content-box,linear-gradient(#000 0 0);-webkit-mask-composite:xor;mask:linear-gradient(#000 0 0) content-box exclude,linear-gradient(#000 0 0);
  animation:llrun 1.1s linear infinite}
@keyframes llrun{to{--llrun:360deg}}
@media (prefers-reduced-motion:reduce){#bLife.llflash::before{animation:none;background:#ffd23a}}
.llbig{display:flex;""")
path.write_text(src)
print("continue +7 patch applied")
