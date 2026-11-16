# Flower Fever — iPhone (iOS) setup

This repo is the iPhone version of Flower Fever, made from **Android build 100**
(commit `802777c`, "Gifts from friends arrive live while the game is open").
Same game code and patches, plus what Apple needs:

| Feature | On iPhone |
|---|---|
| Puzzle, garden, bouquets, friends & gifts, switch lifeline… | Same as Android build 100 |
| Ads (AdMob) | iOS ad ids in `www/ads-config.js` (`FLOWER_ADS_IOS`). Google **test** ads until you add yours |
| Apple's "Allow tracking?" question (ATT) | Asked once, before the first ad |
| In-app purchases | App Store (StoreKit), same packs. **Restore purchases** is in Settings |
| Sign in | **Sign in with Apple** + Sign in with Google (needs Firebase, step 4) |
| Delete account | Settings → "Delete my account and cloud save" (also revokes the Apple sign-in) |
| Rating | Apple's own review window (no custom "rate us" window, no Play Store link) |
| Notifications, vibration, save/share pictures | Yes (iPhone asks once for each permission) |
| Privacy manifest (`PrivacyInfo.xcprivacy`) | Added by the build |
| Back button | Not on iPhone (the game's own buttons are used) |

The build runs on a GitHub cloud Mac (`.github/workflows/ios.yml`). No Mac needed.
Every push builds a Simulator test. With the Apple secrets, it also uploads to **TestFlight**.

## 1. GitHub secrets (same values as AlphaBlast-iOS)
This repo → Settings → Secrets and variables → Actions → **New repository secret**:

| Secret | Value |
|---|---|
| `APPLE_TEAM_ID` | Your 10-character Team ID |
| `ASC_KEY_ID` | App Store Connect API key id |
| `ASC_ISSUER_ID` | App Store Connect API issuer id |
| `ASC_KEY_P8` | The full text of the `AuthKey_XXXX.p8` file |

(If you don't have the .p8 file anymore, make a new key: App Store Connect → Users and Access →
Integrations → App Store Connect API → **+**, access **Admin**.)

The build registers the App ID `com.alxmobileapps.flowerfever` by itself.

## 2. Create the app in App Store Connect
https://appstoreconnect.apple.com → Apps → **+ New App**
- Platform: iOS · Name: **Flower Fever** · Language: English
- Bundle ID: `com.alxmobileapps.flowerfever` (it appears after the first build with secrets)
- SKU: `flowerfever-ios`

Then put the app's **Apple ID** number (App Information page) in `www/ads-config.js` →
`FLOWER_APPSTORE_ID`, so share messages link to the App Store.

## 3. In-app purchases (App Store Connect → your app → Monetization → In-App Purchases)

| Product ID | Type | Same as Android |
|---|---|---|
| `com.alxmobileapps.flowerfever.starter30` | Consumable | starter30 |
| `com.alxmobileapps.flowerfever.gems10` | Consumable | gems10 |
| `com.alxmobileapps.flowerfever.gems25` | Consumable | gems25 |
| `com.alxmobileapps.flowerfever.gems60` | Consumable | gems60 |
| `com.alxmobileapps.flowerfever.gems170` | Consumable | gems170 |
| `com.alxmobileapps.flowerfever.gems400` | Consumable | gems400 |
| `com.alxmobileapps.flowerfever.noads100` | **Non-Consumable** | noads100 |

The **Paid Apps agreement** (Business) must be signed, or purchases won't load.

## 4. Firebase (sign-in, cloud save, friends, analytics)
Firebase console → the Flower Fever project:
1. Project settings → **Add app → iOS**, bundle id `com.alxmobileapps.flowerfever`.
2. Download **GoogleService-Info.plist** and add it to the root of this repo.
3. Authentication → Sign-in method → turn on **Apple** (Google and Anonymous are already on).

Without the file the app still builds and plays, just without sign-in, cloud save and friends.

## 5. AdMob
AdMob → Apps → **Add app → iOS** (Flower Fever), then make 3 ad units: Banner, Interstitial, Rewarded.
Put the app id and the 3 unit ids in `www/ads-config.js` → `FLOWER_ADS_IOS`, and set `testing: false`.

## 6. Before sending for review
Apple asks for: iPhone screenshots (6.9" and 6.5"), privacy policy URL, the App Privacy questionnaire
(AdMob: device id / advertising data, used for tracking; Firebase: user id + gameplay data, linked
to the user), age rating, and a review note (where Restore purchases and Delete account are).
