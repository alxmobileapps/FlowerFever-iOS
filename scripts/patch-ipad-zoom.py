"""iPad: the game is drawn about 1.66x bigger, so it fills the iPad screen instead of a phone-sized column.

The page tells the iPad it is about 620 points wide (13-inch iPad; smaller iPads a bit less) and the iPad
zooms it up to the full screen. Everything keeps the same layout as on phones and tablets (the tablet
board layout already kicks in because the screen is not tall and narrow). iPhones are unchanged.
"""
from pathlib import Path

path = Path("www/index.html")
src = path.read_text()
if "IPAD_ZOOM_PATCH" in src:
    print("iPad zoom already applied"); raise SystemExit(0)

meta = '<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no,viewport-fit=cover">'
if src.count(meta) != 1:
    raise RuntimeError("patch-ipad-zoom: viewport tag changed")
js = ("<script>/* IPAD_ZOOM_PATCH */(function(){try{var w=Math.min(screen.width,screen.height);"
      "if(w>=700&&('ontouchend' in document)){var cw=Math.round(w/1.66),s=(w/cw).toFixed(4);"
      "document.querySelector('meta[name=viewport]').setAttribute('content','width='+cw+',initial-scale='+s+',minimum-scale='+s+',maximum-scale='+s+',user-scalable=no,viewport-fit=cover');}"
      "}catch(e){}})();</script>")
path.write_text(src.replace(meta, meta + "\n" + js))
print("iPad: game zoomed to fill the screen")
