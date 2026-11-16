"""Board sits near the top of the play area, and the Fast / Skip buttons sit just under the board.

Before: the board was centred in the space between the top bar and the banner, leaving a wide gap
above it, and Fast / Skip were pinned to the bottom of that space.
Runs after the .patch files (it edits the final www/index.html).
"""
from pathlib import Path

path = Path("www/index.html")
src = path.read_text()

def once(before, after):
    global src
    if src.count(after) == 1 and after not in before:
        return
    if src.count(before) != 1:
        raise RuntimeError("Board layout code changed; check patch-board-layout.py: " + before[:60])
    src = src.replace(before, after)

# 1) board near the top of the play area (the whole board, empty rows included, 20 px under the top bar; the top bar stays above the board so its buttons can always be tapped)
css = "#stage.boardTop{place-items:start center!important}#stage.boardTop>.frame{margin-top:20px}#app>.hud{z-index:7}\n"
once("canvas#board{display:block;", css + "canvas#board{display:block;")
once('<main id="stage">', '<main id="stage" class="boardTop">')
# keep tall boards inside the play area now that there is a 20 px gap above
once("(h - 6 - frameExtra) / ROWS", "(h - 26 - frameExtra) / (ROWS + Math.max(0, (L && L.nudge && L.nudge[1]) || 0))")
# short screens (landscape): let tiles get smaller rather than run under the banner
once("CELL = Math.max(20, Math.min(110,", "CELL = Math.max(12, Math.min(110,")

# 3) the board grid has empty rows around smaller levels: lift the board by those rows so the
#    flowers (not the empty space) start right under the top bar
once("""  const [nx, ny] = L.nudge || [0, 0];
  canvas.style.transform = nx || ny ? `translate(${nx * CELL}px,${ny * CELL}px)` : "";""",
     """  placeBoard();""")
once("""addEventListener("resize", () => { layout(); const [nx, ny] = (L && L.nudge) || [0, 0]; canvas.style.transform = nx || ny ? `translate(${nx * CELL}px,${ny * CELL}px)` : ""; });""",
     """function boardRows() {   // first and last row that has board cells
  let a = ROWS, z = -1;
  for (let r = 0; r < ROWS; r++) for (let c = 0; c < COLS; c++) if (mask[r] && (mask[r][c] === 1 || (ground[r] && ground[r][c] > 0))) { if (r < a) a = r; if (r > z) z = r; }
  return a > z ? [0, ROWS - 1] : [a, z];
}
function placeBoard() {
  const [nx, ny] = (L && L.nudge) || [0, 0], dy = ny;   // the whole board (empty rows included) sits 20 px under the top bar
  canvas.style.transform = nx || dy ? `translate(${nx * CELL}px,${dy * CELL}px)` : "";
  if (typeof positionShowerControls === "function") requestAnimationFrame(positionShowerControls);
}
addEventListener("resize", () => { layout(); if (L) placeBoard(); });""")

# 2) Fast / Skip right under the board (4 px gap), still inside the play area
anchor = '$("#stage").appendChild(skipBtn);'
code = """
function positionShowerControls(){
 const stage=document.getElementById('stage'),board=document.getElementById('board');
 if(!stage||!board)return;
 const s=stage.getBoundingClientRect(),b=board.getBoundingClientRect(),bottom=typeof boardRows==="function"?b.top+(boardRows()[1]+1)*CELL:b.bottom;
 const height=Math.max(ffBtn.offsetHeight,skipBtn.offsetHeight,38);
 const top=Math.max(0,Math.min(bottom-s.top+4,stage.clientHeight-height-6));
 for(const button of [ffBtn,skipBtn]){button.style.top=top+'px';button.style.bottom='auto';}
}
const showerControlsObserver=new ResizeObserver(()=>requestAnimationFrame(positionShowerControls));
showerControlsObserver.observe(document.getElementById('stage'));
showerControlsObserver.observe(canvas);
"""
if "function positionShowerControls()" not in src:
    once(anchor, anchor + code)
    once("skipBtn.hidden = false; ffBtn.hidden = false;",
         "skipBtn.hidden = false; ffBtn.hidden = false; requestAnimationFrame(positionShowerControls);")
path.write_text(src)
print("board layout patch applied")
