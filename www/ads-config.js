/* =====================================================================
 * FLOWER FEVER — AdMob + Google Play settings
 * =====================================================================
 * appId          AdMob App ID (copied into the Android manifest by the build)
 * bannerId       Banner under the board (during levels only)
 * interstitialId Full-screen ad between levels (after every 5 wins, from level 20)
 * rewardedId     "Watch an ad" rewards (diamonds, lives, lifelines, x2 coins, +5 moves)
 * testing        false = real ads. The DEBUG test APK always switches to Google
 *                test ads, so you can play it on your own phone safely.
 *
 * Real Flower Fever AdMob ids (account ca-app-pub-2452250229562082).
 * ===================================================================== */
window.FLOWER_ADS = {
  appId: 'ca-app-pub-2452250229562082~6470928510',
  bannerId: 'ca-app-pub-2452250229562082/2148540129',
  interstitialId: 'ca-app-pub-2452250229562082/7867770663',
  rewardedId: 'ca-app-pub-2452250229562082/9807538292',
  testing: false
};

/* Google Play in-app products (create these exact ids in Play Console → Monetize → In-app products) */
window.FLOWER_PRODUCTS = {
  consumable: ['starter30', 'gems10', 'gems25', 'gems60', 'gems170', 'gems400'],
  nonConsumable: ['noads100']
};

/* ===== iPhone (iOS) =====
 * Create an iOS app in AdMob (Apps → Add app → iOS) and 3 ad units (Banner, Interstitial, Rewarded),
 * Real Flower Fever iOS AdMob ids (account ca-app-pub-2452250229562082).
 * appId is copied into the iPhone app's Info.plist by the build (GADApplicationIdentifier).
 */
window.FLOWER_ADS_IOS = {
  appId: 'ca-app-pub-2452250229562082~9957554443',
  bannerId: 'ca-app-pub-2452250229562082/5826737743',
  interstitialId: 'ca-app-pub-2452250229562082/3200574400',
  rewardedId: 'ca-app-pub-2452250229562082/1887492733',
  testing: false
};
/* App Store in-app purchase ids = this prefix + the ids above, e.g. com.alxmobileapps.flowerfever.gems10 */
window.FLOWER_IOS_SKU_PREFIX = 'com.alxmobileapps.flowerfever.';
/* App Store app id (the number in the App Store link, App Store Connect → App Information → Apple ID).
   Used in "share" messages. Leave empty until the app exists. */
window.FLOWER_APPSTORE_ID = '';
