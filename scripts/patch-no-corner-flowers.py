"""Windows (level complete, profile, settings, friends...) no longer show the four flowers in their corners."""
from pathlib import Path

path = Path("www/index.html")
src = path.read_text()
before = "card.innerHTML = cardCorners + html;"
if before not in src:
    if "card.innerHTML = html; overlay.hidden = false;" in src:
        print("corner flowers already removed"); raise SystemExit(0)
    raise RuntimeError("patch-no-corner-flowers: window code changed; review before building")
src = src.replace(before, "card.innerHTML = html;", 1)
path.write_text(src)
print("Corner flowers removed from windows")
