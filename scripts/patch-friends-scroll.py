"""Friends window with many friends: the list scrolls inside the window, so "Back" and the help line
always stay on screen (before, the window grew past the screen and could not scroll)."""
from pathlib import Path
path = Path("www/index.html"); src = path.read_text()
if "FRIENDS_SCROLL_PATCH" in src: print("friends scroll already applied"); raise SystemExit(0)
css = """
/* FRIENDS_SCROLL_PATCH: the friends list scrolls; the window never grows past the screen */
#card.frcard{max-height:none}
#card.frcard .frlist{max-height:max(160px,calc(100vh - 520px));max-height:max(160px,calc(100dvh - 520px));overflow-y:auto;overscroll-behavior:contain;
  -webkit-overflow-scrolling:touch;padding:2px 6px 10px 2px;margin-right:-6px;scrollbar-width:thin;scrollbar-color:#f3a9c6 transparent;
  -webkit-mask:linear-gradient(#000 calc(100% - 18px),transparent);mask:linear-gradient(#000 calc(100% - 18px),transparent)}
</style>"""
i = src.rfind("</style>", 0, src.find("<body"))
if i < 0: raise RuntimeError("patch-friends-scroll: no </style> in <head>")
src = src[:i] + css + src[i + len("</style>"):]
path.write_text(src); print("friends list scrolls")
