"""Google save: keep the garden (and the diamond balance) when the game is opened on a new or reinstalled phone.

Before: when the phone's save and the Google save were combined, the garden and the diamonds were taken from
whichever save was changed last. A new install changes its fresh save first, so its empty garden "won" and
was then written over the Google copy.
Now: a save with no progress (no stars and no garden XP) never wins over one with progress, and the garden
with more garden XP is kept (garden XP only goes up), the most recent one when they are equal.
Runs after the .patch files (it edits the final www/index.html).
"""
from pathlib import Path

path = Path("www/index.html")
src = path.read_text()
before = """  const newer = (a.savedAt || 0) >= (b.savedAt || 0) ? a : b;   // balances come from the most recent save, so spent diamonds can't come back
  m.gems = newer.gems || 0; if (newer.farm) m.farm = newer.farm; m.savedAt = Math.max(a.savedAt || 0, b.savedAt || 0);"""
after = """  // balances come from the most recent save that has progress, so spent diamonds can't come back and a new install can't wipe them
  const prog = s => Object.keys(s.stars || {}).length + ((s.farm && s.farm.xp) || 0) + ((s.farm && s.farm.coins != null && s.farm.coins !== 100) ? 1 : 0);
  const newer = !prog(a) && prog(b) ? b : !prog(b) && prog(a) ? a : (a.savedAt || 0) >= (b.savedAt || 0) ? a : b;
  m.gems = newer.gems || 0; m.savedAt = Math.max(a.savedAt || 0, b.savedAt || 0);
  const fa = a.farm, fb = b.farm, xa = (fa && fa.xp) || 0, xb = (fb && fb.xp) || 0;   // the garden with more garden XP is the one played most recently
  const farm = !fa ? fb : !fb ? fa : xa !== xb ? (xa > xb ? fa : fb) : newer === a ? fa : fb; if (farm) m.farm = farm;"""
if src.count(after) == 1:
    print("save merge patch already applied")
elif src.count(before) == 1:
    path.write_text(src.replace(before, after)); print("save merge patch applied")
else:
    raise RuntimeError("mergeSaves changed; check patch-save-merge.py")
