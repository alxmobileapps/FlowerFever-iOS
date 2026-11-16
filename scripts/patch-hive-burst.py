"""Beehive: all of its bees always fly out together, also during the Flower Shower
(the shower used to send them one at a time, one per shower beat).
Runs after the .patch files (it edits the final www/index.html).
"""
from pathlib import Path

path = Path("www/index.html")
src = path.read_text()
if "HIVE_BURST_PATCH" in src:
    print("hive burst patch already applied"); raise SystemExit(0)

def rep(before, after):
    global src
    if src.count(before) != 1:
        raise RuntimeError("patch-hive-burst: code changed: " + before[:70])
    src = src.replace(before, after)

rep("""  if (inShower) {
    for (const { cells, per } of list) {
      for (const [r, c] of cells) {
        for (let i = 0; i < per; i++) {
          await waitForShowerBeat();
          beginShowerEffect();
          await flyBee(r, c, palette[rnd(palette.length)]);
        }
      }
      for (const [r, c] of cells) {
        ground[r][c] = 0;
        groundType[r][c] = 0;
        delete hiveAt[r * COLS + c];
      }
    }
    sfx("crack");
    return true;
  }
  const all = []; let k = 0;
  list.forEach(({ cells, per }) => cells.forEach(([r, c]) => { for (let i = 0; i < per; i++) { const d = k++ * 110;""",
    """  // HIVE_BURST_PATCH: the whole swarm leaves at once, in the Flower Shower too (it takes one shower beat)
  if (inShower) { await waitForShowerBeat(); beginShowerEffect(); }
  const all = []; let k = 0;
  list.forEach(({ cells, per }) => cells.forEach(([r, c]) => { for (let i = 0; i < per; i++) { const d = k++ * 40;""")
rep("""  await sleep((k - 1) * 110 + 260);   // every bee is out of the hive""", """  await sleep((k - 1) * 40 + 260);   // every bee is out of the hive""")
path.write_text(src)
print("hive burst patch applied")
