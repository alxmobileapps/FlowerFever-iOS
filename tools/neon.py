"""Renders the home logo words and the praise words exactly as Chrome (Android) draws them,
# Dev tool (needs Playwright + Chrome, and the test mock init.js next to it). Serve a built www/ and run:
#   python3 tools/neon.py http://localhost:PORT/index.html OUTDIR   then convert the PNGs to .webp into www/neon/
as transparent PNGs, plus a JSON with their sizes in em. Usage: neon.py URL OUTDIR"""
import sys, asyncio, json, re, os
from playwright.async_api import async_playwright

WORDS = ["Lovely!", "Blooming!", "Gorgeous!", "Dazzling!", "Wow!", "Buzzing!", "Flower Shower!", "Hurry!",
         "Petal Storm!", "Shuffle!", "Tap two flowers", "Amazing!", "Magnificent!", "Phenomenal!"]
LOGO_PAD = 0.6  # em of glow room around each logo word

def slug(w): return re.sub(r'[^a-z0-9]+', '-', w.lower()).strip('-')

FREEZE = """
html,body,#homeView,#app,#game,#frame,#board,.h3,.h3top{background:transparent!important}
*{visibility:hidden!important;animation:none!important;transition:none!important}
"""

async def main():
    url, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    meta = {"logo": {}, "praise": {}}
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/usr/bin/google-chrome")
        # ---- logo words ----
        pg = await b.new_page(viewport={"width": 1000, "height": 1100}, device_scale_factor=3)
        await pg.add_init_script(open('/home/claude/tools/init.js').read())
        await pg.goto(url); await pg.wait_for_timeout(3500)
        await pg.evaluate("document.fonts.ready")
        await pg.add_style_tag(content=FREEZE + ".h3name span.nw{visibility:visible!important}.h3name{top:300px!important}")
        await pg.wait_for_timeout(300)
        info = await pg.evaluate("""(pad)=>{
          const h=document.querySelector('.h3name'); if(!h) return null;
          const F=parseFloat(getComputedStyle(h).fontSize); const res={F,words:[]};
          [...h.childNodes].filter(n=>n.nodeType===3&&n.textContent.trim()).forEach(n=>{
            const s=document.createElement('span'); s.className='nw'; s.textContent=n.textContent; n.replaceWith(s);
            const mk=document.createElement('i'); mk.style.cssText='display:inline-block;width:0;height:0;vertical-align:baseline'; s.after(mk);
          });
          h.querySelectorAll('span.nw').forEach(s=>{
            const r=s.getBoundingClientRect(), base=s.nextSibling.getBoundingClientRect().top;
            res.words.push({t:s.textContent,x:r.left,y:r.top,w:r.width,h:r.height,base});
          });
          return res;}""", LOGO_PAD)
        F = info["F"]; pad = LOGO_PAD * F
        for i, wd in enumerate(info["words"]):
            await pg.evaluate("(i)=>document.querySelectorAll('.h3name span.nw').forEach((s,k)=>s.style.setProperty('visibility',k===i?'visible':'hidden','important'))", i)
            await pg.wait_for_timeout(150)
            clip = {"x": wd["x"] - pad, "y": wd["y"] - pad, "width": wd["w"] + 2 * pad, "height": wd["h"] + 2 * pad}
            fn = "logo-" + slug(wd["t"]) + ".png"
            await pg.screenshot(path=os.path.join(out, fn), clip=clip, omit_background=True)
            meta["logo"][wd["t"]] = {"src": fn, "w": round(clip["width"] / F, 4), "h": round(clip["height"] / F, 4),
                                     "m": LOGO_PAD, "va": round(-(wd["y"] + wd["h"] - wd["base"]) / F, 4)}
        await pg.close()
        # ---- praise words ----
        pg = await b.new_page(viewport={"width": 1400, "height": 932}, device_scale_factor=3)
        await pg.add_init_script(open('/home/claude/tools/init.js').read())
        await pg.goto(url); await pg.wait_for_timeout(3500)
        await pg.evaluate("document.fonts.ready")
        await pg.add_style_tag(content=FREEZE + """
          #praise{position:fixed!important;left:50%!important;top:50%!important;transform:translate(-50%,-50%)!important;opacity:1!important;filter:none!important;z-index:99999!important}
          #praise .pw{font-size:51.5px!important;visibility:visible!important;clip-path:none!important;-webkit-clip-path:none!important;filter:none!important}
          #praise .ps,#praise .rail{display:none!important}""")
        for w in WORDS:
            r = await pg.evaluate("""(w)=>{let el=document.getElementById('praise');
              if(!el){el=document.createElement('div');el.id='praise';document.body.appendChild(el);}
              if(el.parentElement!==document.body) document.body.appendChild(el);
              el.className=''; el.innerHTML='<span class="pw"></span>'; el.firstChild.textContent=w;
              const pw=el.firstChild, cs=getComputedStyle(pw), r=pw.getBoundingClientRect();
              return {x:r.left,y:r.top,w:r.width,h:r.height,F:parseFloat(cs.fontSize),
                pt:parseFloat(cs.paddingTop),pl:parseFloat(cs.paddingLeft),pr:parseFloat(cs.paddingRight),pb:parseFloat(cs.paddingBottom)};}""", w)
            await pg.wait_for_timeout(150)
            fn = "praise-" + slug(w) + ".png"
            await pg.screenshot(path=os.path.join(out, fn), clip={"x": r["x"], "y": r["y"], "width": r["w"], "height": r["h"]}, omit_background=True)
            Fp = r["F"]
            meta["praise"][w] = {"src": fn, "w": round(r["w"] / Fp, 4), "h": round(r["h"] / Fp, 4),
                                 "pt": round(r["pt"] / Fp, 4), "pl": round(r["pl"] / Fp, 4), "pr": round(r["pr"] / Fp, 4), "pb": round(r["pb"] / Fp, 4)}
        await b.close()
    json.dump(meta, open(os.path.join(out, "neon.json"), "w"), indent=1)
    print(json.dumps(meta)[:1500])

asyncio.run(main())
