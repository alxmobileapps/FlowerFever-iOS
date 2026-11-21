"""The app itself never scrolls or bounces: the Home screen, windows and the game stay put when dragged.
Only real lists that are longer than their box (choose-a-level map, seed shop, basket, album, friends list ...)
can still be moved with a finger. Also undoes any page shift the browser makes by itself (e.g. scrollIntoView)."""
from pathlib import Path
path = Path("www/index.html"); src = path.read_text()
if "NO_SCROLL_PATCH" in src: print("no-scroll already applied"); raise SystemExit(0)
css = """
/* NO_SCROLL_PATCH: the page itself can never move */
html,body{position:fixed;inset:0;width:100%;height:100%;overflow:hidden;overscroll-behavior:none}
</style>"""
i = src.find("</style>"); src = src[:i] + css + src[i + len("</style>"):]
js = """<script>
/* NO_SCROLL_PATCH */
(() => {
  const LISTS = ".mscroll,.h3scroll,.gds,.levels,.fseeds,.fhouses,.fstore,.fbask,.falb,.frlist,.farm .fcard,.frcard";
  const canMove = el => el && (el.scrollHeight > el.clientHeight + 1 || el.scrollWidth > el.clientWidth + 1);
  // a finger drag only moves a list that really is longer than its box; everything else stays still (no bounce)
  document.addEventListener("touchmove", e => {
    if (e.touches && e.touches.length > 1) { if (e.cancelable) e.preventDefault(); return; }   // no pinch zoom
    const t = e.target && e.target.closest ? e.target.closest(LISTS) : null;
    if (!canMove(t) && e.cancelable) e.preventDefault();
  }, { passive: false });
  // anything that shifts the page or a fixed box by itself gets put back
  const pin = e => {
    if (scrollX || scrollY) scrollTo(0, 0);
    const t = e && e.target;
    if (t && t.nodeType === 1 && !(t.closest && t.closest(LISTS)) && (t.scrollTop || t.scrollLeft)) { t.scrollTop = 0; t.scrollLeft = 0; }
  };
  addEventListener("scroll", pin, { passive: true });
  document.addEventListener("scroll", pin, { capture: true, passive: true });
})();
</script>
</body>"""
j = src.rfind("</body>")
if j < 0: raise RuntimeError("patch-no-scroll: no </body>")
src = src[:j] + js + src[j + len("</body>"):]
path.write_text(src); print("the app never scrolls; only long lists do")
