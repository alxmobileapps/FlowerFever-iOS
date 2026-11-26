"""iPhone: the keyboard covered the message box on "✏️ Your message", so the player could not see what they typed.

While the keyboard is up, the window sits just above it and the bouquet preview gets smaller, so the picture,
the message box and "Use message" all stay in view. When the keyboard closes, everything goes back.
(Android already moves the window above the keyboard by itself, so this is only in the iPhone build.)
Runs after patch-bouquet-message.py (it edits the final www/index.html).
"""
from pathlib import Path

path = Path("www/index.html")
src = path.read_text()
if "IOS_MSG_KEYBOARD_PATCH" in src:
    print("iPhone message keyboard patch already applied"); raise SystemExit(0)

def rep(before, after):
    global src
    n = src.count(before)
    if n != 1:
        raise RuntimeError(f"patch-ios-msg-keyboard: expected 1 of: {before[:80]!r}, found {n}")
    src = src.replace(before, after)

rep(""".fmsgin:focus{""",
    """.fcard.kbd .fmsgprev{width:84px;height:84px;margin:2px auto} .fcard.kbd h3{margin:0 0 2px} .fcard.kbd .fmsgn{margin:2px 0}
.fmsgin:focus{""")

rep("""        setTimeout(() => { try { ta.focus(); } catch (e) {} }, 300);""",
    """        { // IOS_MSG_KEYBOARD_PATCH: keep the message box above the iPhone keyboard
          const sh = c.closest(".fsheet"), vv = window.visualViewport, later = () => setTimeout(kb, 0);
          const kb = () => {
            if (!c.contains(ta)) { if (sh) sh.style.removeProperty("padding-bottom"); c.classList.remove("kbd"); if (vv) { vv.removeEventListener("resize", kb); vv.removeEventListener("scroll", kb); } c.removeEventListener("click", later); return; }
            const h = vv ? Math.max(0, innerHeight - vv.height - vv.offsetTop) : 0, on = h > 80 && document.activeElement === ta;
            c.classList.toggle("kbd", on);
            if (sh) { if (on) sh.style.setProperty("padding-bottom", (h + 10) + "px", "important"); else sh.style.removeProperty("padding-bottom"); }
          };
          if (vv) { vv.addEventListener("resize", kb); vv.addEventListener("scroll", kb); }
          ta.addEventListener("focus", () => { kb(); setTimeout(kb, 350); });
          ta.addEventListener("blur", () => setTimeout(kb, 120));
          c.addEventListener("click", later);   // Back / Use message replace the window: tidy up after it
        }
        setTimeout(() => { try { ta.focus(); } catch (e) {} }, 300);""")

path.write_text(src)
print("iPhone: message box stays above the keyboard")
