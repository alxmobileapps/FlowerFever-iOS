"""Player safety for the friends feature (App Store Guideline 1.2, user-generated content):
- Block & report a player from the friends list (the Remove window): they disappear from the list,
  their water and coin gifts are ignored, their garden can't be opened, and a report is sent
  (Firestore reports/, read by the developer, answered within 24 hours).
- Contact line in the Friends window.
Nicknames were already filtered for rude words (nickProblem). Runs after the social patches.
"""
from pathlib import Path

path = Path("www/index.html")
src = path.read_text()
if "UGC_SAFETY_PATCH" in src:
    print("ugc safety patch already applied"); raise SystemExit(0)

def rep(before, after):
    global src
    if src.count(before) != 1:
        raise RuntimeError("patch-ugc-safety: code changed: " + before[:80])
    src = src.replace(before, after)

rep("""/* --- friends list (gardens you visited, and friends who watered yours) --- */""",
    """/* UGC_SAFETY_PATCH: blocked players (their gifts are ignored, their garden can't be opened) and reports */
const SUPPORT_EMAIL = "alx.mobileapps@gmail.com";
const isBlocked = pid => (save.blocked || []).includes(pid);
async function blockPlayer(pid, name) {
  save.blocked = [...new Set([...(save.blocked || []), pid])].slice(-200);
  save.friends = (save.friends || []).filter(y => y.p !== pid); persist();
  track("player_block", {});
  const S = SOC(); if (!S || !save.pid) return;
  try { await S.set(`reports/${save.pid}_${pid}`, { pid, name: String(name || "").slice(0, 16), by: save.pid, why: "blocked", at: Date.now() }); } catch (e) {}
}
/* --- friends list (gardens you visited, and friends who watered yours) --- */""")

# gifts from blocked players are thrown away
rep("""    try { await S.del(`profiles/${save.pid}/coins/${w.id}`); } catch (e) { continue; }   // each gift counts once
    const d = w.data || {};""",
    """    try { await S.del(`profiles/${save.pid}/coins/${w.id}`); } catch (e) { continue; }   // each gift counts once
    const d = w.data || {}; if (d.from && isBlocked(d.from)) continue;""")
rep("""    try { await S.del(`profiles/${save.pid}/water/${w.id}`); } catch (e) { continue; }   // each gift counts once
    const d = w.data || {};""",
    """    try { await S.del(`profiles/${save.pid}/water/${w.id}`); } catch (e) { continue; }   // each gift counts once
    const d = w.data || {}; if (d.from && isBlocked(d.from)) continue;""")

# a blocked player's garden can't be opened
rep("""async function visitFriend(pid, back, msgEl) {
  const S = SOC(); if (!S) return;""",
    """async function visitFriend(pid, back, msgEl) {
  const S = SOC(); if (!S) return;
  if (isBlocked(pid)) {
    show(`<div class="ribbon">Friends</div><h2>You blocked this player</h2><p>Unblock ${pidShow(pid)} to visit their garden again?</p><div class="btns"><button class="btn" id="ubYes">Unblock</button><button class="btn alt" id="ubNo">Cancel</button></div>`,
      e2 => { e2.querySelector("#ubNo").onclick = back; e2.querySelector("#ubYes").onclick = () => { save.blocked = (save.blocked || []).filter(x => x !== pid); persist(); visitFriend(pid, back); }; });
    return;
  }""")

# Remove window: Remove / Block & report / Cancel
rep("""<p>You can add them again any time with their Player ID: <b>${pidShow(x.p)}</b></p><div class="btns"><button class="btn" id="rmYes">Remove</button><button class="btn alt" id="rmNo">Cancel</button></div>`,
        e2 => { e2.querySelector("#rmNo").onclick = again;""",
    """<p>You can add them again any time with their Player ID: <b>${pidShow(x.p)}</b></p><div class="btns"><button class="btn" id="rmYes">Remove</button><button class="btn alt" id="rmBlock">🚫 Block &amp; report</button><button class="btn alt" id="rmNo">Cancel</button></div>`,
        e2 => { e2.querySelector("#rmNo").onclick = again;
          e2.querySelector("#rmBlock").onclick = async () => { await blockPlayer(x.p, x.n);
            show(`<div class="ribbon">Blocked</div><h2>${socEsc(x.n || pidShow(x.p))} is blocked</h2><p>You won't see their name or gifts again. Thank you for telling us: we check every report within 24 hours.</p><p class="llnote">Questions? ${SUPPORT_EMAIL}</p><div class="btns"><button class="btn" id="bkOk">OK</button></div>`, e3 => { e3.querySelector("#bkOk").onclick = again; }); };""")

# contact line under the list
rep("""    <div class="btns"><button class="btn alt" id="frBack">Back</button></div>`, el => {
    el.closest(".card").classList.add("frcard");""",
    """    <p class="llnote frhelp">Someone bothering you? Tap ✕ next to their name to block &amp; report them. Help: ${SUPPORT_EMAIL}</p>
    <div class="btns"><button class="btn alt" id="frBack">Back</button></div>`, el => {
    el.closest(".card").classList.add("frcard");""")
path.write_text(src)
print("ugc safety patch applied")
