"""Home "Collect" (daily diamond gift) always answers a tap.

Before: if the gift could not be given at that moment, the tap did nothing. That happens right after a new
install when the Google save arrives a few seconds after the home screen opened and says today's gift was
already collected (on this phone before reinstalling, or on another phone), or when the phone's clock is
behind the time the game last saw.
Now: the home screen refreshes when the Google save arrives, and a tap that can't give the gift says why.
Runs after the .patch files (it edits the final www/index.html).
"""
from pathlib import Path
path = Path("www/index.html"); src = path.read_text()
if "COLLECT_FIX_PATCH" in src:
    print("collect fix patch already applied"); raise SystemExit(0)
def rep(a, b):
    global src
    if src.count(a) != 1: raise RuntimeError("patch-collect-fix: code changed: " + a[:60])
    src = src.replace(a, b)
rep("""  const col = el.querySelector("#hCollect"); if (col) col.onclick = () => { if (!dailyGift()) return; flyGem(col); setTimeout(back, 700); };""",
    """  const col = el.querySelector("#hCollect"); if (col) col.onclick = () => {   // COLLECT_FIX_PATCH
    if (dailyGift()) { flyGem(col); setTimeout(back, 700); return; }
    const already = save.daily === todayKey();
    col.disabled = true; col.textContent = already ? "Got it ✓" : "Check clock";
    praise(already ? "Today's gift is already collected" : "Check your phone's date and time");
    setTimeout(back, 1600);
  };""")
rep("""    if (cloud) { const merged = mergeSaves(save, cloud); Object.keys(save).forEach(k => delete save[k]); Object.assign(save, merged); try { localStorage.setItem("petalpop.v1", JSON.stringify(save)); } catch (e) {} }
    await acctSave();""", """    if (cloud) { const merged = mergeSaves(save, cloud); Object.keys(save).forEach(k => delete save[k]); Object.assign(save, merged); try { localStorage.setItem("petalpop.v1", JSON.stringify(save)); } catch (e) {} }
    if (cloud && typeof homeOpen !== "undefined" && homeOpen && typeof showHome === "function" && overlay.hidden) { try { showHome(); } catch (e) {} }   // show the restored diamonds / gift state
    await acctSave();""")
path.write_text(src); print("collect fix patch applied")
