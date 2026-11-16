"""Basket: a flower kept for a bouquet can still be sold, after a short question
("This flower is for a bouquet. Sell it anyway?"). "Sell extras" still sells only the extras.
Runs after patch-bouquets.py (it edits the final www/index.html).
"""
from pathlib import Path

path = Path("www/index.html")
src = path.read_text()
if "SELL_KEPT_PATCH" in src:
    print("sell kept patch already applied"); raise SystemExit(0)

def rep(before, after):
    global src
    if src.count(before) != 1:
        raise RuntimeError("patch-sell-kept: code changed: " + before[:70])
    src = src.replace(before, after)

rep("""  function sellOne(k, b) {
    if ((f.inv[k] || 0) <= (needFor()[k] || 0)) { b.classList.remove("nope"); void b.offsetWidth; b.classList.add("nope"); return; }   // kept for a bouquet
    const g = sellPrice(k);""",
    """  function sellOne(k, b, sure) {
    // SELL_KEPT_PATCH: a flower kept for a bouquet can still be sold, after asking once
    if (!sure && (f.inv[k] || 0) <= (needFor()[k] || 0)) {
      sheetShow(`<h3>💐 For a bouquet</h3><img class="fskimg" alt="" src="${brImg(k)}"><p><b>${SEEDS[k].n}</b> is for a bouquet.<br>Sell it anyway?</p>
        <div class="btns col"><button class="btn" id="skSell">${FC_SVG} Sell · +${sellPrice(k)}</button><button class="btn alt" id="skKeep">Keep</button></div>`,
        c => { c.querySelector("#skKeep").onclick = () => basketSheet(); c.querySelector("#skSell").onclick = () => { basketSheet(); sellOne(k, null, true); }; });
      return;
    }
    if (!(f.inv[k] > 0)) return;
    if (!b) b = sheet.querySelector(`.fbi[data-k="${k}"]`) || el.querySelector(".fcbuy");
    const g = sellPrice(k);""")
rep(""".fbask{""", """.fskimg{display:block;width:96px;height:96px;object-fit:contain;margin:4px auto}
.fbask{""")
path.write_text(src)
print("sell kept patch applied")
