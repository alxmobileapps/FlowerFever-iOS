"""Google save can no longer be overwritten by a fresh or half-loaded phone save.

1) Nothing is written to Google until this phone has read the Google copy and combined it with its own
   (before, a save 5 seconds after any change, or when the app went to the background, could go out first
   and replace the Google copy with the new phone's empty progress).
2) If reading the Google copy fails (no internet, slow network), the game does not write either; it tries
   again every 30 seconds. Before, a failed read counted as "no save yet" and the phone's copy was written over it.
3) Saves never run two at a time; a change made while a save is in flight is saved right after it.
Runs after the .patch files (it edits the final www/index.html). www/native.js reports failed reads.
"""
from pathlib import Path
path = Path("www/index.html"); src = path.read_text()
if "SAVE_SAFETY_PATCH" in src:
    print("save safety patch already applied"); raise SystemExit(0)
def rep(a, b):
    global src
    if src.count(a) != 1: raise RuntimeError("patch-save-safety: code changed: " + a[:60])
    src = src.replace(a, b)
rep("""async function acctSave() { const A = ACCT(); if (!A || !A.user) return false; const ok = await A.save(cloudCopy());""",
    """// SAVE_SAFETY_PATCH: write only after this phone has read and combined the Google copy; one write at a time
let acctReady = false, acctWriting = null, acctAgain = false, acctRetry = 0;
async function acctSave() {
  const A = ACCT(); if (!A || !A.user || !acctReady) return false;
  if (acctWriting) { acctAgain = true; return acctWriting; }
  acctWriting = acctSaveNow(A);
  try { return await acctWriting; } finally { acctWriting = null; if (acctAgain) { acctAgain = false; acctSave(); } }
}
async function acctSaveNow(A) { const ok = await A.save(cloudCopy());""")
rep("""  const A = ACCT(); if (!A || !A.user || acctBusy) return false; acctBusy = true;
  try {
    const cloud = await A.load();""", """  const A = ACCT(); if (!A || !A.user || acctBusy) return false; acctBusy = true;
  try {
    let cloud;
    try { cloud = await A.load(); }
    catch (e) { acctReady = false; clearTimeout(acctRetry); acctRetry = setTimeout(acctSync, 30000); track("account_sync_failed", {}); return false; }   // couldn't read: don't write over it
    acctReady = true;""")
rep("""e2.querySelector("#oYes").onclick = async () => { await acctSave(); await ACCT().signOut();""",
    """e2.querySelector("#oYes").onclick = async () => { await acctSave(); acctReady = false; await ACCT().signOut();""")
path.write_text(src); print("save safety patch applied")
