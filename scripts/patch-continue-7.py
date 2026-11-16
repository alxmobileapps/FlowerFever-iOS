"""Continue gives +7 moves; the "Hurry!" warning comes at 4 moves left after a continue (was 2);
right after the warning, the lifeline button glows for 5 seconds.
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
rep("function hideLifelineTip() {", """// CONTINUE7_PATCH: the lifeline button glows for 5 seconds after the "Hurry!" warning
let lifeFlashT = 0;
function flashLifeline() {
  const b = document.getElementById("bLife"); if (!b) return;
  clearTimeout(lifeFlashT); b.classList.remove("llflash"); void b.offsetWidth;
  setTimeout(() => b.classList.add("llflash"), 900);
  lifeFlashT = setTimeout(() => b.classList.remove("llflash"), 5900);
}
function hideLifelineTip() {""")
rep(".llbig{display:flex;", """#bLife.llflash{animation:llflash .9s ease-in-out infinite;position:relative;z-index:3}
@keyframes llflash{0%,100%{box-shadow:0 0 0 3px #ffd23a,0 0 12px 4px rgba(255,210,58,.7);transform:scale(1)}50%{box-shadow:0 0 0 6px #ffd23a,0 0 26px 10px rgba(255,170,30,.9);transform:scale(1.14)}}
@media (prefers-reduced-motion:reduce){#bLife.llflash{animation:none;box-shadow:0 0 0 5px #ffd23a}}
.llbig{display:flex;""")
path.write_text(src)
print("continue +7 patch applied")
