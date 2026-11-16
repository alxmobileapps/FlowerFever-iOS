"""Windows (level complete, out of moves, settings...) always fit the screen, also in landscape
and on short screens: a window taller than the screen is shrunk to fit instead of running off the bottom.
Runs after the .patch files (it edits the final www/index.html).
"""
from pathlib import Path

path = Path("www/index.html")
src = path.read_text()
code = """// FIT_OVERLAY_PATCH: shrink a window that is taller than the screen so its buttons stay visible
(function () {
  let raf = 0;
  const fit = () => { raf = 0; document.querySelectorAll("#overlay > .card").forEach(c => {
    c.style.zoom = ""; const h = c.offsetHeight, room = innerHeight - 36;
    if (h > room && h > 0) c.style.zoom = Math.max(.5, room / h).toFixed(3);
  }); };
  const soon = () => { if (!raf) raf = requestAnimationFrame(fit); };
  const start = () => { const o = document.getElementById("overlay"); if (!o) return setTimeout(start, 500);
    new MutationObserver(soon).observe(o, { childList: true, subtree: true, attributes: true, attributeFilter: ["hidden", "class"] }); soon(); };
  addEventListener("resize", soon); start();
})();
let mapOpen = null;"""
if "FIT_OVERLAY_PATCH" in src:
    print("fit overlay patch already applied")
elif src.count("let mapOpen = null;") == 1:
    path.write_text(src.replace("let mapOpen = null;", code)); print("fit overlay patch applied")
else:
    raise RuntimeError("patch-fit-overlay: anchor not found")
