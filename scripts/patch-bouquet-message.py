"""A personal message on the bouquet picture, for 10 diamonds.

On a made bouquet: "✏️ Add a message · 💎10". The player types up to 80 letters, sees the picture
update as they type, and pays 10 diamonds with "Use message". Shared and saved pictures then carry the
message on a white card under the bouquet. Changing the message costs 10 diamonds again, except in the
first 5 minutes after paying (to fix a typo). "Remove" is free.
Runs after patch-share-garden.py (it edits the final www/index.html).
"""
from pathlib import Path

path = Path("www/index.html")
src = path.read_text()
if "BOUQUET_MESSAGE_PATCH" in src:
    print("bouquet message patch already applied"); raise SystemExit(0)

def rep(before, after):
    global src
    n = src.count(before)
    if n != 1:
        raise RuntimeError(f"patch-bouquet-message: expected 1 of: {before[:80]!r}, found {n}")
    src = src.replace(before, after)

# --- the picture: message card under the bouquet -------------------------------------------------
rep("""  function bouquetPng(b) {
    return new Promise(res => {""", """  // BOUQUET_MESSAGE_PATCH
  const MSG_COST = 10, MSG_FREE_MS = 5 * 60 * 1000, MSG_MAX = 80;
  f.bmsg = f.bmsg || {};
  function wrapText(g, text, maxW) {
    const words = text.split(/\\s+/), lines = []; let line = "";
    for (const w of words) { const t = line ? line + " " + w : w; if (g.measureText(t).width > maxW && line) { lines.push(line); line = w; } else line = t; }
    if (line) lines.push(line); return lines.slice(0, 3);
  }
  function bouquetPng(b, msgOverride) {
    const msg = (msgOverride != null ? msgOverride : (f.bmsg[b.no] && f.bmsg[b.no].t) || "").trim();
    if (msg) return bouquetPngMsg(b, msg);
    return new Promise(res => {""")
rep("""  const shareFile = b =>""", """  function bouquetPngMsg(b, msg) {
    return new Promise(res => {
      const im = new Image();
      im.onload = () => {
        const S = 1080, c = document.createElement("canvas"); c.width = c.height = S; const g = c.getContext("2d");
        const bg = g.createLinearGradient(0, 0, 0, S); bg.addColorStop(0, "#fff6fa"); bg.addColorStop(1, "#fde3ee"); g.fillStyle = bg; g.fillRect(0, 0, S, S);
        g.fillStyle = "rgba(255,255,255,.75)"; g.beginPath(); g.arc(S / 2, 330, 300, 0, Math.PI * 2); g.fill();
        g.shadowColor = "rgba(90,30,60,.22)"; g.shadowBlur = 30; g.shadowOffsetY = 12; g.drawImage(im, S / 2 - 290, 40, 580, 580); g.shadowColor = "transparent";
        g.textAlign = "center"; g.fillStyle = "#5a2e44"; g.font = '800 58px "Baloo 2","Trebuchet MS",sans-serif'; g.fillText(b.n, S / 2, 680);
        // the message card
        g.font = 'italic 700 50px "Nunito","Trebuchet MS",sans-serif'; const lines = wrapText(g, msg, 820), lh = 64, ch = 70 + lines.length * lh;
        const x = 100, y = 720, w = S - 200; g.save(); g.shadowColor = "rgba(90,30,60,.18)"; g.shadowBlur = 20; g.shadowOffsetY = 6; g.fillStyle = "#fff";
        g.beginPath(); g.roundRect ? g.roundRect(x, y, w, ch, 28) : g.rect(x, y, w, ch); g.fill(); g.restore();
        g.strokeStyle = "#f3bdd2"; g.lineWidth = 4; g.setLineDash([12, 10]); g.beginPath(); g.roundRect ? g.roundRect(x + 14, y + 14, w - 28, ch - 28, 20) : g.rect(x + 14, y + 14, w - 28, ch - 28); g.stroke(); g.setLineDash([]);
        g.fillStyle = "#7a2e52"; lines.forEach((l, i) => g.fillText(l, S / 2, y + 35 + lh * (i + .75)));
        g.textAlign = "right"; g.fillStyle = "rgba(232,70,126,.85)"; g.font = '800 30px "Baloo 2","Trebuchet MS",sans-serif'; g.fillText("🌷 Flower Fever", S - 30, S - 26);
        res(c.toDataURL("image/png"));
      };
      im.onerror = () => res(null); im.src = b.img;
    });
  }
  function messageSheet(b) {
    const cur = f.bmsg[b.no], free = cur && Date.now() - cur.at < MSG_FREE_MS;
    sheetShow(`<h3>✏️ Your message</h3><img class="fmsgprev" id="mPrev" alt="Picture preview" src="${b.img}">
      <textarea id="mText" class="fmsgin" maxlength="${MSG_MAX}" rows="2" placeholder="Happy birthday, Mama! Love, Alex" aria-label="Message">${cur ? cur.t.replace(/[<&]/g, "") : ""}</textarea>
      <p class="fmsgn"><span id="mLeft">${MSG_MAX - (cur ? cur.t.length : 0)}</span> letters left</p>
      <div class="btns col"><button class="btn" id="mUse">${free ? "Use message · free" : `Use message · <span class="fgem">${GEM_SVG}</span>${MSG_COST}`}</button>${cur ? `<button class="btn alt" id="mDel">Remove message</button>` : ""}<button class="btn alt" id="mBack">Back</button></div>`,
      c => {
        const ta = c.querySelector("#mText"), prev = c.querySelector("#mPrev"), left = c.querySelector("#mLeft"); let tick = 0;
        const draw = () => { clearTimeout(tick); tick = setTimeout(async () => { const v = ta.value.trim(); const png = await bouquetPng(b, v); if (png) prev.src = png; }, 250); };
        ta.oninput = () => { left.textContent = MSG_MAX - ta.value.length; draw(); }; draw();
        c.querySelector("#mBack").onclick = () => bouquetCard(b);
        const del = c.querySelector("#mDel"); if (del) del.onclick = () => { delete f.bmsg[b.no]; persist(); bouquetCard(b); };
        c.querySelector("#mUse").onclick = () => {
          const v = ta.value.trim().slice(0, MSG_MAX); if (!v) { ta.focus(); return; }
          if (!free) {
            if ((save.gems || 0) < MSG_COST) { sheet.hidden = true; showGems(() => { el.style.display = ""; }, MSG_COST); el.style.display = "none"; return; }
            addGems(-MSG_COST); track("bouquet_message", { no: b.no }); f.bmsg[b.no] = { t: v, at: Date.now() };
          } else f.bmsg[b.no].t = v;
          persist(); sfx("create"); bouquetCard(b);
        };
        setTimeout(() => { try { ta.focus(); } catch (e) {} }, 300);
      });
  }
  const shareFile = b =>""")

# --- the made-bouquet card: show the message picture, and the new button --------------------------
rep("""    sheetShow(`<img class="fpic fstkpic big" alt="" src="${b.img}"><h3>${b.n}</h3><p class="fsub">${b.occ}</p>""",
    """    const m = f.bmsg[b.no];
    sheetShow(`<img class="fpic fstkpic big${m ? " withmsg" : ""}" id="bPic" alt="" src="${b.img}"><h3>${b.n}</h3><p class="fsub">${m ? `“${m.t.replace(/[<&]/g, "")}”` : b.occ}</p>""")
rep("""<button class="btn alt" id="sSave">⬇ Save</button><button class="btn alt" id="sBack">Back</button></div>`,""",
    """<button class="btn alt" id="sMsg">${m ? "✏️ Change message" : `✏️ Add a message · <span class="fgem">${GEM_SVG}</span>${MSG_COST}`}</button><button class="btn alt" id="sSave">⬇ Save</button><button class="btn alt" id="sBack">Back</button></div>`,""")
rep("""        c.querySelector("#sBack").onclick = () => albumSheet();""",
    """        c.querySelector("#sBack").onclick = () => albumSheet();
        c.querySelector("#sMsg").onclick = () => messageSheet(b);
        if (m) bouquetPng(b).then(png => { const p = c.querySelector("#bPic"); if (png && p) p.src = png; });""")

css = """
.farm .fmsgprev{display:block;width:190px;height:190px;margin:6px auto;border-radius:16px;object-fit:contain;background:#fff6fa;box-shadow:0 2px 8px rgba(90,30,60,.15)}
.farm .fmsgin{width:100%;box-sizing:border-box;border:2px solid #f0c2d4;border-radius:14px;padding:10px 12px;font:700 18px/1.35 var(--body);color:#5a2e44;background:#fff;resize:none}
.farm .fmsgin:focus{outline:none;border-color:#e8467e;box-shadow:0 0 0 3px rgba(232,70,126,.2)}
.farm .fmsgn{margin:4px 0 0;font:700 13px var(--body);color:#8a6a50;text-align:right}
.farm .fstkpic.withmsg{border-radius:16px;background:#fff6fa}
"""
rep(".farm .fbedbtn{z-index:4}", ".farm .fbedbtn{z-index:4}" + css)

path.write_text(src)
print("bouquet message patch applied")
