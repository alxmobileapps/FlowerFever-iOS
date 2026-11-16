# App Review notes (paste into App Store Connect → App Review Information → Notes)

Lessons from AlphaBlast's App Review rejections are already built into this app.

```
GUIDELINE 2.3.10 - ACCURATE METADATA
The app contains no Google Play / Android references, links or purchase options; the build fails if any such word is found. All purchases use Apple In-App Purchase only. "Sign in with Google" in Settings > Your account is only an optional login (offered next to Sign in with Apple) for saving progress; it is not a store or a payment method.

GUIDELINE 2.1 - APP TRACKING TRANSPARENCY
The ATT request appears automatically about 1 second after launch, before the Google AdMob SDK is started and before any ad is requested. The notification permission is asked only after the ATT request has been answered. If the user selects "Ask App Not to Track", ads are non-personalized.

GUIDELINE 3.1.1 - RESTORING PURCHASES
"Restore purchases" is in the Diamond shop (under the packs) and in Settings. Diamonds (consumable) are saved with the game; with the optional account (Settings > Your account > Sign in with Apple / Google) they are kept on all the user's devices. "No Ads + 100 Diamonds" (non-consumable) is restored with Restore purchases.

ACCOUNT
No login is required to play. Optional account: Settings > Your account > Sign in with Apple or Sign in with Google. Account deletion: Settings > Your account > "Delete my account and cloud save" (also revokes Sign in with Apple).

APP OVERVIEW
Flower Fever is a match-3 flower puzzle game with a garden: players match flowers to finish levels, then plant, grow and pick flowers in their garden and make bouquets. In-app purchases: diamond packs (consumable) and No Ads + 100 Diamonds (non-consumable). External services: Google AdMob (ads), Google Firebase (optional account, cloud save, friends, analytics), Apple In-App Purchase. All content is original.
```
