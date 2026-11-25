#!/usr/bin/env bash
# Builds the final game page (www/index.html) from the base page + the game patches, then the iPhone changes.
# Same patches, same order as the Android build 100 (minus the Android-only ones).
set -euo pipefail
git apply scripts/board-webgl.patch
git apply scripts/celebration-polish.patch
git apply scripts/webgl-effects.patch
git apply --unidiff-zero scripts/home-and-offers.patch
python3 scripts/patch-portal-refill.py
python3 scripts/patch-board-layout.py
python3 scripts/patch-garden-plants.py
python3 scripts/patch-bouquets.py
python3 scripts/patch-share-garden.py
python3 scripts/patch-save-merge.py
python3 scripts/patch-shower-combos.py
python3 scripts/patch-bouquet-message.py
python3 scripts/patch-fit-overlay.py
python3 scripts/patch-garden-tutorial.py
python3 scripts/patch-bee-help.py
python3 scripts/patch-shuffle-goal.py
python3 scripts/patch-switch-lifeline.py
python3 scripts/patch-quiet-ads.py
python3 scripts/patch-continue-7.py
python3 scripts/patch-flower-size.py
python3 scripts/patch-sharp-board.py
python3 scripts/patch-collect-fix.py
python3 scripts/patch-save-safety.py
python3 scripts/patch-diagonal-fill.py
python3 scripts/patch-coin-reward.py
python3 scripts/patch-sell-kept.py
python3 scripts/patch-voice-wait.py
python3 scripts/patch-rate-again.py
python3 scripts/patch-hive-burst.py
python3 scripts/patch-open-quiet.py
python3 scripts/patch-social.py
python3 scripts/patch-no-corner-flowers.py
python3 scripts/patch-home-rows.py
python3 scripts/patch-portal-ends.py
python3 scripts/patch-tutorial-coins.py
python3 scripts/patch-bgm-webaudio.py
python3 scripts/patch-ugc-safety.py
python3 scripts/patch-ad-levels.py
python3 scripts/patch-level16-heart.py
python3 scripts/patch-showcase-levels.py
python3 scripts/patch-new-shapes.py
python3 scripts/patch-hive-edges.py
python3 scripts/patch-goals-swamp.py
python3 scripts/patch-combo-shower-fx.py
python3 scripts/patch-lift-overlay.py
python3 scripts/patch-layer-order.py
python3 scripts/patch-garden-bg.py
python3 scripts/patch-neon-images.py
python3 scripts/patch-flower-ask.py
python3 scripts/patch-slow-fall.py
python3 scripts/patch-voices4.py
python3 scripts/patch-unbelievable.py
python3 scripts/patch-tablet-board.py
python3 scripts/patch-friends-scroll.py
python3 scripts/patch-audio-resume.py
python3 scripts/patch-diag-regions.py
python3 scripts/patch-plant-all.py
python3 scripts/patch-no-scroll.py
python3 scripts/patch-switch-tip.py
python3 scripts/patch-bee-swamp.py
python3 scripts/patch-shower-convert.py
python3 scripts/patch-continue-gems.py
python3 scripts/patch-pano-resume.py
python3 scripts/patch-boot-cover.py
python3 scripts/patch-idle-draw.py
python3 scripts/patch-win-revamp.py
python3 scripts/patch-water-third.py
python3 scripts/patch-ios.py
python3 scripts/ios/scrub_platform.py
