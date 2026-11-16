"""Bouquet pictures to save and share, and a Garden button on the level-complete window.

- Tap a bouquet you made: a big picture with "⬇ Save" (to the phone's photos) and "📤 Share"
  (Messenger, Facebook, Viber...). The picture is 1080 x 1080: the bouquet on a soft background,
  its name and occasion, and a small "Flower Fever" mark.
- Sharing gives +1 diamond, once a day.
- Level complete: a "Garden" button next to Replay / Map / Home.
Runs after patch-bouquets.py (it edits the final www/index.html). The phone side is in www/native.js (FlowerFeverShare).
"""
from pathlib import Path

path = Path("www/index.html")
src = path.read_text()
if "SHARE_GARDEN_PATCH" in src:
    print("share / garden patch already applied"); raise SystemExit(0)

def rep(before, after, count=1):
    global src
    n = src.count(before)
    if n != count:
        raise RuntimeError(f"patch-share-garden: expected {count} of: {before[:80]!r}, found {n}")
    src = src.replace(before, after)

# --- Garden button on the level-complete window ------------------------------------------------
rep("""V20H18V9.5"/></svg>Home</button></div>""", """V20H18V9.5"/></svg>Home</button><button class="wpill" id="wGarden" aria-label="My garden"><span aria-hidden="true">🌷</span>Garden</button></div>""")
rep("""      el.querySelector("#wHome").onclick = () => leaveWin(showHome);""",
    """      el.querySelector("#wHome").onclick = () => leaveWin(showHome);
      el.querySelector("#wGarden").onclick = () => leaveWin(() => showMyGarden(() => startLevel(Math.min(LEVELS.length - 1, levelIdx + 1))));""")
rep(".wpill{flex:1;max-width:118px;", ".wsec .wpill{padding:0 5px!important;gap:3px!important;font-size:14px!important;overflow:hidden;white-space:nowrap}.wsec .wpill svg,.wsec .wpill img{flex:none}\n.wpill{flex:1;max-width:118px;min-width:0;")

# --- the made bouquet: big picture, Save and Share ---------------------------------------------
rep("""    const made = !!f.stk[no];
    sheetShow(""", """    const made = !!f.stk[no];
    if (made) { bouquetCard(b); return; }
    sheetShow(""")

code = r'''
  // SHARE_GARDEN_PATCH: a 1080 x 1080 picture of a made bouquet, to save or share
  function bouquetPng(b) {
    return new Promise(res => {
      const im = new Image();
      im.onload = () => {
        const S = 1080, c = document.createElement("canvas"); c.width = c.height = S; const g = c.getContext("2d");
        const bg = g.createLinearGradient(0, 0, 0, S); bg.addColorStop(0, "#fff6fa"); bg.addColorStop(1, "#fde3ee"); g.fillStyle = bg; g.fillRect(0, 0, S, S);
        g.fillStyle = "rgba(255,255,255,.75)"; g.beginPath(); g.arc(S / 2, 430, 380, 0, Math.PI * 2); g.fill();
        g.shadowColor = "rgba(90,30,60,.22)"; g.shadowBlur = 30; g.shadowOffsetY = 12; g.drawImage(im, S / 2 - 360, 70, 720, 720); g.shadowColor = "transparent";
        g.textAlign = "center"; g.fillStyle = "#5a2e44"; g.font = '800 76px "Baloo 2","Trebuchet MS",sans-serif'; g.fillText(b.n, S / 2, 880);
        g.fillStyle = "#a0607e"; g.font = '700 44px "Nunito","Trebuchet MS",sans-serif'; g.fillText(b.occ, S / 2, 950);
        g.textAlign = "right"; g.fillStyle = "rgba(232,70,126,.85)"; g.font = '800 34px "Baloo 2","Trebuchet MS",sans-serif'; g.fillText("🌷 Flower Fever", S - 36, S - 34);
        res(c.toDataURL("image/png"));
      };
      im.onerror = () => res(null); im.src = b.img;
    });
  }
  const shareFile = b => "flower-fever-" + b.n.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") + ".png";
  function bouquetCard(b) {
    const today = new Date().toDateString(), bonus = f.shareDay !== today;
    sheetShow(`<img class="fpic fstkpic big" alt="" src="${b.img}"><h3>${b.n}</h3><p class="fsub">${b.occ}</p>
      <div class="btns col"><button class="btn" id="sShare">📤 Share${bonus ? ` <small>· <span class="fgem">${GEM_SVG}</span>+1</small>` : ""}</button><button class="btn alt" id="sSave">⬇ Save</button><button class="btn alt" id="sBack">Back</button></div>`,
      c => {
        c.querySelector("#sBack").onclick = () => albumSheet();
        c.querySelector("#sSave").onclick = async e => { const btn = e.currentTarget; btn.disabled = true; const png = await bouquetPng(b); const ok = png && await saveBouquet(png, b); btn.disabled = false; floatAt(btn, ok ? "✓ Saved" : "Try again"); if (ok) track("bouquet_save", { no: b.no }); };
        c.querySelector("#sShare").onclick = async e => { const btn = e.currentTarget; btn.disabled = true; const png = await bouquetPng(b); const ok = png && await shareBouquet(png, b); btn.disabled = false;
          if (ok) { track("bouquet_share", { no: b.no }); if (f.shareDay !== new Date().toDateString()) { f.shareDay = new Date().toDateString(); persist(); addGems(1); sfx("create"); floatAt(btn, `+1 <span class="fgem">${GEM_SVG}</span>`); bouquetCard(b); } } };
      });
  }
  async function saveBouquet(png, b) {
    const N = window.FlowerFeverShare;
    if (N) { try { return await N.save(png, shareFile(b)); } catch (e) { return false; } }
    try { const a = document.createElement("a"); a.href = png; a.download = shareFile(b); document.body.appendChild(a); a.click(); a.remove(); return true; } catch (e) { return false; }
  }
  async function shareBouquet(png, b) {
    const N = window.FlowerFeverShare, text = `${b.n} 💐 ${b.occ} — made in Flower Fever`;
    if (N) { try { return await N.share(png, shareFile(b), text); } catch (e) { return false; } }
    try { const blob = await (await fetch(png)).blob(), file = new File([blob], shareFile(b), { type: "image/png" });
      if (navigator.canShare && navigator.canShare({ files: [file] })) { await navigator.share({ files: [file], text }); return true; } } catch (e) { return false; }
    return saveBouquet(png, b);
  }
'''
rep("  function makeBouquet(b) {", code + "  function makeBouquet(b) {")
rep(".farm .fsub{margin:0;", ".farm .fstkpic.big{width:210px;height:210px}.farm .btn small{font-size:.8em;opacity:.9}\n.farm .fsub{margin:0;")

path.write_text(src)
print("share / garden patch applied")
