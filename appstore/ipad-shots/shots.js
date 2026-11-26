/* iPad App Store screenshots: a guided tour of the game, only in the screenshot build (ipad-shots.yml).
   On the first launch it loads a sample save (Level 38, a full garden), then every SHOT_EVERY seconds it moves to
   the next screen. The workflow takes a simulator screenshot in the middle of each step.
   Steps: 0 Home, 1 Level 38, 2 a level with soil and ice, 3 Garden, 4 Level map. */
(function () {
  try {
    if (!localStorage.getItem("ffshots.seeded")) {
      localStorage.setItem("petalpop.v1", JSON.stringify(window.FF_SHOT_SEED));
      localStorage.setItem("ffshots.seeded", "1");
    }
  } catch (e) {}
  const $ = s => document.querySelector(s);
  const press = el => { if (el) el.click(); };
  const byText = t => [...document.querySelectorAll("button")].find(b => b.offsetParent && b.textContent.trim().startsWith(t));
  const quiet = () => {   // no ads or pop-ups in the pictures
    try { if (window.FlowerFeverAds) { FlowerFeverAds.showBanner = () => {}; FlowerFeverAds.hideBanner && FlowerFeverAds.hideBanner(); FlowerFeverAds.showInterstitial = async () => false; } } catch (e) {}
  };
  const closeSheets = () => document.querySelectorAll(".fsheet").forEach(s => { s.hidden = true; });
  const G = c => { try { return window.__G(c); } catch (e) { console.log("shot", e); } };   // the game's own functions (hook added by the workflow)
  const play = n => { G(`hide(); startLevel(${n - 1})`); setTimeout(() => { press(byText("Play")); quiet(); }, 1500); };
  const steps = [
    () => { quiet(); },
    () => play(38),
    () => play(54),
    () => { G("hide(); showHome()"); setTimeout(() => { press($("#nGarden")); }, 800); setTimeout(closeSheets, 3500); setTimeout(closeSheets, 6000); },
    () => { closeSheets(); const g = $("#gardenView"); if (g) g.remove(); G("showHome()"); setTimeout(() => press($("#nMap")), 800); },
  ];
  window.__shotStep = i => steps[i] && steps[i]();
  const EVERY = (window.SHOT_EVERY || 20) * 1000;
  if (window.Capacitor && window.Capacitor.isNativePlatform && window.Capacitor.isNativePlatform())
    window.addEventListener("load", () => { setTimeout(quiet, 3000); steps.forEach((f, i) => i && setTimeout(f, 8000 + i * EVERY)); });
})();
