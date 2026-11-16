/* Flower Fever — iPhone (iOS) bridges. (Same game code as the Android app, adapted for Apple.)
 * The game calls these when they exist (in the web preview they don't, and the game uses its own stand-ins):
 *   window.FlowerFeverAds        showBanner / hideBanner / showInterstitial() / showRewarded(kind) → true when the reward is earned
 *   window.FlowerFeverStore      buy(id) → true when paid · restore() → owned ids · prices { id: "₱49.00" }
 *   window.FlowerFeverNotify     schedule([{ id, title, body, at }]) · cancel(ids)
 *   window.FlowerFeverAnalytics  logEvent(name, params)   (Firebase, only when google-services.json was added)
 */
(function () {
  const C = window.Capacitor;
  if (!C || !C.isNativePlatform || !C.isNativePlatform()) return;
  const P = n => (C.Plugins && C.Plugins[n]) || (C.registerPlugin && C.registerPlugin(n));
  const IOS = C.getPlatform && C.getPlatform() === 'ios';
  const cfg = (IOS && window.FLOWER_ADS_IOS) || window.FLOWER_ADS || {};
  const log = (...a) => { try { console.log('[FF]', ...a); } catch (e) {} };

  /* ---------- Ads (AdMob) ---------- */
  const AdMob = P('AdMob');
  if (AdMob) {
    const test = !!cfg.testing;
    let ready = (async () => {
      try {
        await AdMob.initialize({ initializeForTesting: test });
        try {
          const info = await AdMob.requestConsentInfo();
          if (info && info.isConsentFormAvailable && info.status === 'REQUIRED') await AdMob.showConsentForm();
        } catch (e) { log('consent', e); }
        if (IOS) {   // Apple's "Allow tracking?" question (App Tracking Transparency), asked once, before the first ad
          try {
            await new Promise(r => setTimeout(r, 1200));   // iOS only shows it once the app is fully on screen
            const t = await AdMob.trackingAuthorizationStatus();
            if (t && t.status === 'notDetermined') await AdMob.requestTrackingAuthorization();
          } catch (e) { log('tracking', e); }
        }
      } catch (e) { log('admob init', e); }
    })();

    // the web page keeps a 50px strip under the board for the banner; in the app the real banner sits there
    const st = document.createElement('style');
    st.textContent = '#adBanner{background:none!important;color:transparent!important;border:0!important;box-shadow:none!important}#adBanner *{visibility:hidden!important}';
    document.head.appendChild(st);

    // One banner call at a time, and after each one the banner is brought in line with what the game wants now.
    // (Before, leaving a level while the first banner was still loading let it appear later on Home or in the garden.)
    let bannerShown = false, bannerOnScreen = false, bannerWanted = false, bannerRun = null;
    const bannerApply = () => {
      if (bannerRun) return bannerRun;
      bannerRun = (async () => {
        await ready;
        for (let tries = 0; tries < 4 && bannerWanted !== bannerOnScreen; tries++) {
          const want = bannerWanted;
          try {
            if (want) {
              if (bannerShown) await AdMob.resumeBanner();
              else { await AdMob.showBanner({ adId: cfg.bannerId, adSize: 'BANNER', position: 'BOTTOM_CENTER', margin: 0, isTesting: test }); bannerShown = true; }
            } else if (bannerShown) await AdMob.hideBanner();
            bannerOnScreen = want;
          } catch (e) { log('banner', e); if (want) break; }   // a banner that failed to load: try again next time it is wanted
        }
      })().finally(() => { bannerRun = null; if (bannerWanted !== bannerOnScreen && !bannerWanted) bannerApply(); });
      return bannerRun;
    };
    const banner = {
      show() { bannerWanted = true; return bannerApply(); },
      hide() { bannerWanted = false; return bannerApply(); }
    };

    // full-screen ads are loaded ahead of time so they open instantly
    let interReady = false, rewardReady = false, rewardBusy = false;
    const loadInter = async () => { await ready; try { await AdMob.prepareInterstitial({ adId: cfg.interstitialId, isTesting: test }); interReady = true; } catch (e) { interReady = false; setTimeout(loadInter, 60000); } };
    const loadReward = async () => { await ready; try { await AdMob.prepareRewardVideoAd({ adId: cfg.rewardedId, isTesting: test }); rewardReady = true; } catch (e) { rewardReady = false; setTimeout(loadReward, 60000); } };
    loadInter(); loadReward();

    const once = (events, ms) => new Promise(res => {
      const hs = []; let done = false;
      const fin = v => { if (done) return; done = true; hs.forEach(h => { try { h.remove(); } catch (e) {} }); res(v); };
      events.forEach(([ev, v]) => { Promise.resolve(AdMob.addListener(ev, () => fin(v))).then(h => hs.push(h)); });
      if (ms) setTimeout(() => fin('timeout'), ms);
    });

    window.FlowerFeverAds = {
      showBanner: () => banner.show(),
      hideBanner: () => banner.hide(),
      async showInterstitial() {
        if (!interReady) { loadInter(); return false; }
        interReady = false;
        const listeners = [];
        let timer;
        try {
          let settle;
          const closed = new Promise(resolve => { settle = resolve; });
          listeners.push(await AdMob.addListener('interstitialAdDismissed', () => settle(true)));
          listeners.push(await AdMob.addListener('interstitialAdFailedToShow', () => settle(false)));
          timer = setTimeout(() => settle(false), 120000);
          quiet(true);
          await AdMob.showInterstitial();
          return await closed;
        } catch (e) {
          log('inter', e);
          return false;
        } finally {
          clearTimeout(timer);
          for (const listener of listeners) Promise.resolve(listener.remove()).catch(() => {});
          quiet(false);
          loadInter();
        }
      },
      async showRewarded(kind) {
        if (rewardBusy) return false;   // a second tap while the ad is loading
        rewardBusy = true; loading(true);   // "Ads loading... Please wait." from the moment of the tap
        try {
          if (!rewardReady) {
            await loadReward();
            if (!rewardReady) { loading(false); alertNoAd(); return false; }
          }
          rewardReady = false;
          let earned = false;
          const rew = once([['onRewardedVideoAdReward', 1]]); rew.then(v => { if (v === 1) earned = true; });
          const closed = once([['onRewardedVideoAdDismissed', 1], ['onRewardedVideoAdFailedToShow', 0]], 180000);
          once([['onRewardedVideoAdShowed', 1], ['onRewardedVideoAdFailedToShow', 0]], 30000).then(() => loading(false));
          quiet(true); try { const r = await AdMob.showRewardVideoAd(); if (r) earned = true; await closed; } catch (e) { log('reward', e); } quiet(false);
          loadReward();
          return earned;
        } finally { loading(false); rewardBusy = false; }
      }
    };
  }
  // "Ads loading... Please wait." window while a rewarded ad is being fetched (it can take a few seconds)
  let loadTimer = 0;
  function loading(on) {
    try {
      let d = document.getElementById('ffAdLoading');
      clearTimeout(loadTimer);
      if (!on) { if (d) d.remove(); return; }
      if (!d) {
        d = document.createElement('div'); d.id = 'ffAdLoading'; d.setAttribute('role', 'alert');
        d.style.cssText = 'position:fixed;inset:0;z-index:2147483647;display:flex;align-items:center;justify-content:center;background:rgba(60,20,40,.6);padding:16px;touch-action:none';
        d.innerHTML = '<style>@keyframes ffAdSpin{to{transform:rotate(360deg)}}</style>'
          + '<div style="background:#fff;border-radius:24px;padding:24px 28px;max-width:300px;width:100%;text-align:center;box-shadow:0 18px 40px rgba(0,0,0,.35);font-family:Nunito,sans-serif">'
          + '<div style="width:46px;height:46px;margin:0 auto 14px;border-radius:50%;border:5px solid #fcd3e3;border-top-color:#e8467e;animation:ffAdSpin .8s linear infinite"></div>'
          + '<div style="font-size:21px;font-weight:900;color:#5a2e44">Ads loading...</div>'
          + '<div style="font-size:16px;font-weight:700;color:#8a6a7a;margin-top:4px">Please wait.</div></div>';
        ['click', 'pointerdown', 'touchstart'].forEach(ev => d.addEventListener(ev, e => { e.stopPropagation(); e.preventDefault(); }, { passive: false }));
        document.body.appendChild(d);
      }
      loadTimer = setTimeout(() => loading(false), 30000);   // never leave it up forever
    } catch (e) {}
  }
  function quiet(on) { try { const A = window.FlowerFeverAudio; if (A) on ? A.pause() : A.resume(); } catch (e) {} }
  function alertNoAd() {
    try {
      const d = document.createElement('div');
      d.textContent = 'No ad is ready right now. Please try again in a minute.';
      d.style.cssText = 'position:fixed;left:50%;bottom:90px;transform:translateX(-50%);z-index:99;background:#5a2e44;color:#fff;padding:12px 16px;border-radius:14px;font:700 15px/1.3 Nunito,sans-serif;max-width:80%;text-align:center';
      document.body.appendChild(d); setTimeout(() => d.remove(), 3500);
    } catch (e) {}
  }

  /* ---------- In-app purchases (cordova-plugin-purchase): App Store on iPhone ---------- */
  const prods = window.FLOWER_PRODUCTS || { consumable: [], nonConsumable: [] };
  // App Store product ids carry the app's prefix (com.alxmobileapps.flowerfever.gems10); the game keeps using the short ids
  const SKU_PRE = IOS ? (window.FLOWER_IOS_SKU_PREFIX || 'com.alxmobileapps.flowerfever.') : '';
  const sku = id => SKU_PRE + id, gameId = id => (SKU_PRE && String(id).startsWith(SKU_PRE)) ? String(id).slice(SKU_PRE.length) : id;
  const storeApi = { prices: {} };
  window.FlowerFeverStore = storeApi;
  document.addEventListener('deviceready', () => {
    const Cdv = window.CdvPurchase; if (!Cdv) { log('no billing plugin'); return; }
    const { store, ProductType } = Cdv, Platform = { GOOGLE_PLAY: IOS ? Cdv.Platform.APPLE_APPSTORE : Cdv.Platform.GOOGLE_PLAY };
    const waiting = {};   // product id → resolve() of a buy() the game is waiting on
    store.register([
      ...prods.consumable.map(id => ({ id: sku(id), type: ProductType.CONSUMABLE, platform: Platform.GOOGLE_PLAY })),
      ...prods.nonConsumable.map(id => ({ id: sku(id), type: ProductType.NON_CONSUMABLE, platform: Platform.GOOGLE_PLAY }))
    ]);
    store.when()
      .productUpdated(p => { try { const pr = p.pricing && p.pricing.price; if (pr) storeApi.prices[gameId(p.id)] = pr; } catch (e) {} })
      .approved(t => t.verify())
      .verified(r => r.finish())
      .finished(t => {
        (t.products || []).forEach(tp => {
          const p = { id: gameId(tp.id) };
          if (waiting[p.id]) { const res = waiting[p.id]; delete waiting[p.id]; markSeen(t.transactionId); res(true); }
          else if ((prods.consumable.includes(p.id) || p.id === 'noads100') && !seen(t.transactionId)) {
            // paid earlier but never delivered (app closed during the purchase): give it now
            try { if (window.FlowerFeverGrant && window.FlowerFeverGrant(p.id)) markSeen(t.transactionId); } catch (e) {}
          }
        });
      });
    store.error(e => log('billing error', e && e.message));
    store.initialize([Platform.GOOGLE_PLAY]).catch(e => log('billing init', e));

    const seen = id => { try { return (JSON.parse(localStorage.getItem('ff.tx') || '[]')).includes(id); } catch (e) { return false; } };
    const markSeen = id => { try { const a = JSON.parse(localStorage.getItem('ff.tx') || '[]'); a.push(id); localStorage.setItem('ff.tx', JSON.stringify(a.slice(-200))); } catch (e) {} };

    storeApi.buy = id => new Promise(async res => {
      const p = store.get(sku(id), Platform.GOOGLE_PLAY), offer = p && p.getOffer();
      if (!offer || waiting[id]) { res(false); return; }
      waiting[id] = res;
      const err = await Promise.resolve().then(() => offer.order()).catch(() => true);
      if (err) { delete waiting[id]; res(false); }   // cancelled or failed
      setTimeout(() => { if (waiting[id] === res) { delete waiting[id]; res(false); } }, 10 * 60 * 1000);
    });
    storeApi.restore = async () => {
      try { await store.restorePurchases(); } catch (e) {}
      return store.products.filter(p => p.owned).map(p => gameId(p.id));
    };
  }, false);

  /* ---------- Local notifications ---------- */
  const LN = P('LocalNotifications');
  if (LN) {
    let asked = false;
    window.FlowerFeverNotify = {
      async schedule(list) {
        try {
          if (!asked) { asked = true; const p = await LN.checkPermissions(); if (p.display !== 'granted') await LN.requestPermissions(); }
          await LN.cancel({ notifications: list.map(n => ({ id: n.id })) }).catch(() => {});
          await LN.schedule({ notifications: list.map(n => ({ id: n.id, title: n.title, body: n.body, schedule: { at: new Date(n.at) } })) });
        } catch (e) { log('notify', e); }
      },
      cancel(ids) { try { LN.cancel({ notifications: ids.map(id => ({ id })) }); } catch (e) {} }
    };
  }

  /* ---------- Analytics (Firebase) ---------- */
  const FA = P('FirebaseAnalytics');
  if (FA && window.FLOWER_FIREBASE) {
    window.FlowerFeverAnalytics = {
      logEvent(name, params) {
        const clean = {}; Object.entries(params || {}).forEach(([k, v]) => { if (v !== undefined && v !== null) clean[k] = typeof v === 'boolean' ? (v ? 1 : 0) : v; });
        try { FA.logEvent({ name: String(name).slice(0, 40), params: clean }); } catch (e) {}
      }
    };
  }

  /* ---------- Google sign-in + cloud save (Firebase Auth + Firestore, only when google-services.json was added) ---------- */
  const FAuth = P('FirebaseAuthentication'), FS = P('FirebaseFirestore');
  if (FAuth && FS && window.FLOWER_FIREBASE) {
    const path = uid => `players/${uid}`;
    // `user` is the Google account only. Players who never signed in get an anonymous Firebase user (`fbUser`),
    // used just for the Player ID and friends' gardens (window.FlowerFeverSocial below).
    let user = null, fbUser = null;
    const listeners = [];
    const setUser = u => {
      fbUser = u || null;
      const prov = u && (u.providerData || []).map(x => x && x.providerId);
      user = u && !u.isAnonymous ? { uid: u.uid, name: u.displayName || '', email: u.email || '', photo: u.photoUrl || '',
        provider: prov && prov.includes('apple.com') && !prov.includes('google.com') ? 'apple' : prov && prov.includes('google.com') ? 'google' : (localStorage.getItem('ff.acctProvider') || 'google') } : null;
      listeners.forEach(f => { try { f(user); } catch (e) {} });
    };
    const firstUser = FAuth.getCurrentUser().then(r => setUser(r && r.user)).catch(() => {});
    try { FAuth.addListener('authStateChange', r => setUser(r && r.user)); } catch (e) {}
    window.FlowerFeverAccount = {
      get user() { return user; },
      onChange(f) { listeners.push(f); },
      providers: IOS ? ['apple', 'google'] : ['google'],
      async signIn(provider) {
        if (provider === 'apple') {
          // Sign in with Apple (required by Apple next to Google). Keeps the same Player ID for anonymous players.
          let r;
          if (fbUser && fbUser.isAnonymous) {
            try { r = await FAuth.linkWithApple(); }
            catch (e) {
              const why = String((e && e.code) || '') + ' ' + String((e && e.message) || '');
              if (!/credential-already-in-use|already (been )?(linked|associated|in use)/i.test(why)) throw e;
              r = await FAuth.signInWithApple();
            }
          } else r = await FAuth.signInWithApple();
          if (!r || !r.user || !r.user.uid) throw new Error('Apple sign-in returned no user. Please try again.');
          try { localStorage.setItem('ff.acctProvider', 'apple'); } catch (e) {}
          setUser(r.user); return user;
        }
        try { localStorage.setItem('ff.acctProvider', 'google'); } catch (e) {}
        // Patched at build time to GetSignInWithGoogleOption: explicit button flow,
        // including add-account and reauthentication, rather than the bottom sheet.
        // Preserve errors/cancellation; do not hide them behind a second sign-in attempt.
        let r;
        if (fbUser && fbUser.isAnonymous) {
          // keep the same Firebase user (and so the same Player ID) by adding Google to it
          try { r = await FAuth.linkWithGoogle({ useCredentialManager: true }); }
          catch (e) {
            const why = String((e && e.code) || '') + ' ' + String((e && e.message) || '');
            if (!/credential-already-in-use|already (been )?(linked|associated|in use)/i.test(why)) throw e;   // cancelled or failed: report it
            // this Google account already plays on another phone: sign in to it instead (its saved Player ID comes back with the save)
            r = await FAuth.signInWithGoogle({ useCredentialManager: true });
          }
        } else r = await FAuth.signInWithGoogle({ useCredentialManager: true });
        if (!r || !r.user || !r.user.uid) throw new Error('Google sign-in returned no user. Please try again.');
        setUser(r.user); return user;
      },
      async signOut() { try { await FAuth.signOut(); } catch (e) {} setUser(null); },
      async save(data) {
        if (!user) return false;
        try { await FS.setDocument({ reference: path(user.uid), data: { save: JSON.stringify(data), updatedAt: Date.now(), v: 1 } }); return true; }
        catch (e) { log('cloud save', e); return false; }
      },
      async load() {
        if (!user) return null;
        try { const r = await FS.getDocument({ reference: path(user.uid) }); const d = r && r.snapshot && r.snapshot.data; return d && d.save ? JSON.parse(d.save) : null; }
        catch (e) { log('cloud load', e); throw e; }   // a failed read is not "no save": the game must not overwrite the cloud copy
      },
      async deleteData() {
        if (!user) return;
        try { await FS.deleteDocument({ reference: path(user.uid) }); } catch (e) {}
        if (user.provider === 'apple') {
          // Apple asks apps to revoke the Sign in with Apple token when an account is deleted (needs a fresh Apple sign-in)
          try { const r = await FAuth.signInWithApple(); const code = r && r.credential && r.credential.authorizationCode; if (code) await FAuth.revokeAccessToken({ token: code }); } catch (e) { log('apple revoke', e); }
        }
        try { await FAuth.deleteUser(); } catch (e) {}
        try { localStorage.removeItem('ff.acctProvider'); } catch (e) {}
        setUser(null);
      }
    };

    /* Player ID + friends' gardens: public profiles in profiles/{PLAYER_ID} (see firestore.rules).
       Works for everyone: players who aren't signed in with Google get an anonymous Firebase user.
       (Turn on Authentication → Sign-in method → Anonymous in the Firebase console.) */
    let anonWait = null;
    const authUid = async () => {
      await firstUser;
      if (fbUser) return fbUser.uid;
      if (!anonWait) anonWait = FAuth.signInAnonymously()
        .then(r => { anonWait = null; if (r && r.user) { setUser(r.user); return r.user.uid; } return null; })
        .catch(e => { anonWait = null; log('anonymous sign-in', e); return null; });
      return anonWait;
    };
    const needUid = async () => { const u = await authUid(); if (!u) throw new Error('offline: not signed in'); return u; };
    window.FlowerFeverSocial = {
      uid: authUid,
      async get(ref) { await needUid(); const r = await FS.getDocument({ reference: ref }); return (r && r.snapshot && r.snapshot.data) || null; },
      async set(ref, data) { await needUid(); await FS.setDocument({ reference: ref, data }); },
      async del(ref) { await needUid(); await FS.deleteDocument({ reference: ref }); },
      async list(ref) { await needUid(); const r = await FS.getCollection({ reference: ref }); return ((r && r.snapshots) || []).filter(s => s.data).map(s => ({ id: s.id, data: s.data })); },
      // live updates: calls cb(count) whenever the collection changes (first call right away); returns a function that stops it
      async watch(ref, cb) {
        await needUid();
        const id = await FS.addCollectionSnapshotListener({ reference: ref }, (ev, err) => {
          if (err) { log('watch ' + ref, err); return; }
          try { cb(((ev && ev.snapshots) || []).filter(x => x.data).length); } catch (e) {}
        });
        return () => { FS.removeSnapshotListener({ callbackId: id }).catch(() => {}); };
      }
    };
  }

  /* ---------- Vibration (Capacitor Haptics; the WebView's own vibrate does not work in the app) ---------- */
  const H = P('Haptics');
  if (H) {
    // phones barely feel pulses under ~20 ms, so short ones are lengthened a little
    const buzz = d => { try { H.vibrate({ duration: Math.max(20, d) }); } catch (e) {} };
    window.FlowerFeverHaptics = (kind, ms) => {
      if (Array.isArray(ms)) { let t = 0; ms.forEach((d, i) => { if (i % 2 === 0) setTimeout(() => buzz(d), t); t += d; }); }
      else buzz(ms || 15);
    };
  }

  /* ---------- Bouquet pictures: save to the phone's photos, or share (Messenger, Facebook…) ---------- */
  const FSys = P('Filesystem'), Shr = P('Share'), Med = P('Media');
  if (FSys && Shr) {
    const toCache = async (dataUrl, name) => {
      const r = await FSys.writeFile({ path: name, data: dataUrl.split(',')[1], directory: 'CACHE' });
      return r.uri;
    };
    window.FlowerFeverShare = {
      async save(dataUrl, name) {
        const uri = await toCache(dataUrl, name);
        if (Med && IOS) {
          try { await Med.savePhoto({ path: uri }); return true; } catch (e) { log('save photo', e); }
        } else if (Med) {
          try {
            let albums = (await Med.getAlbums()).albums || [], al = albums.find(a => a.name === 'Flower Fever');
            if (!al) { await Med.createAlbum({ name: 'Flower Fever' }); albums = (await Med.getAlbums()).albums || []; al = albums.find(a => a.name === 'Flower Fever'); }
            await Med.savePhoto({ path: uri, albumIdentifier: al && al.identifier, fileName: name.replace(/\.png$/, '') });
            return true;
          } catch (e) { log('save photo', e); }
        }
        // no photo library access: let the person pick "Save" from the share menu
        try { await Shr.share({ title: 'Save picture', files: [uri] }); return true; } catch (e) { return false; }
      },
      async share(dataUrl, name, text) {
        const uri = await toCache(dataUrl, name);
        try { await Shr.share({ title: 'Flower Fever', text, files: [uri], dialogTitle: 'Send your bouquet' }); return true; }
        catch (e) { log('share', e); return false; }   // closed without sharing
      }
    };
  }

  /* ---------- App Store rating: Apple's own review window (Apple doesn't allow a custom "rate us" window) ---------- */
  const Rev = P('InAppReview');
  if (Rev) window.FlowerFeverReview = () => { try { Rev.requestReview(); } catch (e) { log('review', e); } };

  /* ---------- Android back button: close the open window, or ask before leaving ---------- */
  const App = P('App');
  if (App) App.addListener('backButton', () => {
    // the game knows where "back" leads (close a window, leave a bed, open the menu during a level…); on the home screen the app goes to the background
    if (document.getElementById('ffAdLoading')) return;   // an ad is loading: wait for it
    let handled = false;
    try { handled = !!(window.FlowerFeverBack && window.FlowerFeverBack()); } catch (e) { log('back', e); }
    if (!handled) App.minimizeApp();
  });
})();
