#!/usr/bin/env python3
"""Fills in the 7 Flower Fever in-app purchases in App Store Connect (same prices as Google Play):
price (USD base, Apple converts the other countries), all countries, English name + description,
and the review screenshot (resources/iap-review.png). Safe to run again: skips what is already set.
Env: ASC_KEY_ID, ASC_ISSUER_ID, ASC_KEY_PATH."""
import hashlib, os, time
import jwt, requests

API = "https://api.appstoreconnect.apple.com"
APP_ID = "6835387214"   # Flower Fever: Match 3
PRE = "com.alxmobileapps.flowerfever."
SHOT = "resources/iap-review.png"
PRODUCTS = {   # id: (USD price, name <= 30 chars, description <= 45 chars)
    "starter30": ("0.99", "Starter Pack", "30 diamonds + 3 free lifelines. Once only."),
    "gems10": ("0.99", "10 Diamonds", "10 diamonds for lifelines and the garden."),
    "gems25": ("1.99", "25 Diamonds", "25 diamonds for lifelines and the garden."),
    "gems60": ("3.99", "60 Diamonds", "60 diamonds for lifelines and the garden."),
    "gems170": ("9.99", "170 Diamonds", "170 diamonds for lifelines and the garden."),
    "gems400": ("19.99", "400 Diamonds", "400 diamonds for lifelines and the garden."),
    "noads100": ("5.99", "No Ads + 100 Diamonds", "No forced ads, plus 100 diamonds."),
}

def token():
    now = int(time.time())
    return jwt.encode({"iss": os.environ["ASC_ISSUER_ID"], "iat": now, "exp": now + 1100, "aud": "appstoreconnect-v1"},
                      open(os.environ["ASC_KEY_PATH"]).read(), algorithm="ES256", headers={"kid": os.environ["ASC_KEY_ID"], "typ": "JWT"})

def call(method, path, body=None, params=None, ok=(200, 201, 204)):
    r = requests.request(method, path if path.startswith("http") else API + path, params=params, json=body, timeout=90,
                         headers={"Authorization": f"Bearer {token()}", "Content-Type": "application/json"})
    if r.status_code not in ok:
        raise RuntimeError(f"{method} {path} -> {r.status_code}: {r.text[:600]}")
    return r.json() if r.content else {}

def all_pages(path, params=None):
    out, url, p = [], path, dict(params or {})
    while url:
        d = call("GET", url, params=p); out += d.get("data", []); url = (d.get("links") or {}).get("next"); p = None
    return out

iaps = {i["attributes"]["productId"]: i for i in all_pages(f"/v1/apps/{APP_ID}/inAppPurchasesV2", {"limit": 200})}
territories = [t["id"] for t in all_pages("/v1/territories", {"limit": 200})]
print(f"{len(iaps)} in-app purchases, {len(territories)} territories")
shot = open(SHOT, "rb").read()

for short, (usd, name, desc) in PRODUCTS.items():
    pid = PRE + short
    iap = iaps.get(pid)
    if not iap:
        print("MISSING in App Store Connect:", pid); continue
    iid = iap["id"]
    print(f"== {pid} ({iap['attributes'].get('state')})")

    # English name + description
    locs = call("GET", f"/v2/inAppPurchases/{iid}/inAppPurchaseLocalizations")["data"]
    if not any(l["attributes"]["locale"] == "en-US" for l in locs):
        call("POST", "/v1/inAppPurchaseLocalizations", {"data": {"type": "inAppPurchaseLocalizations",
             "attributes": {"locale": "en-US", "name": name, "description": desc},
             "relationships": {"inAppPurchaseV2": {"data": {"type": "inAppPurchases", "id": iid}}}}})
        print("  name + description set")

    # all countries (and new ones later)
    try:
        call("GET", f"/v2/inAppPurchases/{iid}/inAppPurchaseAvailability")
        print("  availability already set")
    except RuntimeError:
        call("POST", "/v1/inAppPurchaseAvailabilities", {"data": {"type": "inAppPurchaseAvailabilities",
             "attributes": {"availableInNewTerritories": True},
             "relationships": {"inAppPurchase": {"data": {"type": "inAppPurchases", "id": iid}},
                               "availableTerritories": {"data": [{"type": "territories", "id": t} for t in territories]}}}})
        print("  available in all countries")

    # price (USD base; Apple sets the other countries from it)
    has_price = False
    try:
        has_price = bool(call("GET", f"/v1/inAppPurchasePriceSchedules/{iid}/manualPrices")["data"])
    except RuntimeError:
        pass
    if not has_price:
        pts = all_pages(f"/v2/inAppPurchases/{iid}/pricePoints", {"filter[territory]": "USA", "limit": 200})
        pp = next((p for p in pts if p["attributes"]["customerPrice"] in (usd, usd + "0")), None)
        if not pp: raise SystemExit(f"no USD price point {usd} for {pid}")
        call("POST", "/v1/inAppPurchasePriceSchedules", {
            "data": {"type": "inAppPurchasePriceSchedules", "relationships": {
                "inAppPurchase": {"data": {"type": "inAppPurchases", "id": iid}},
                "baseTerritory": {"data": {"type": "territories", "id": "USA"}},
                "manualPrices": {"data": [{"type": "inAppPurchasePrices", "id": "${p0}"}]}}},
            "included": [{"type": "inAppPurchasePrices", "id": "${p0}", "attributes": {"startDate": None},
                          "relationships": {"inAppPurchasePricePoint": {"data": {"type": "inAppPurchasePricePoints", "id": pp["id"]}}}}]})
        print(f"  price ${usd}")
    else:
        print("  price already set")

    # review screenshot
    try:
        cur = call("GET", f"/v2/inAppPurchases/{iid}/appStoreReviewScreenshot").get("data")
    except RuntimeError:
        cur = None
    if not cur:
        r = call("POST", "/v1/inAppPurchaseAppStoreReviewScreenshots", {"data": {"type": "inAppPurchaseAppStoreReviewScreenshots",
             "attributes": {"fileName": "iap-review.png", "fileSize": len(shot)},
             "relationships": {"inAppPurchaseV2": {"data": {"type": "inAppPurchases", "id": iid}}}}})["data"]
        for op in r["attributes"]["uploadOperations"]:
            part = shot[op["offset"]: op["offset"] + op["length"]]
            requests.request(op["method"], op["url"], data=part, headers={h["name"]: h["value"] for h in op["requestHeaders"]}, timeout=120).raise_for_status()
        call("PATCH", f"/v1/inAppPurchaseAppStoreReviewScreenshots/{r['id']}", {"data": {"type": "inAppPurchaseAppStoreReviewScreenshots",
             "id": r["id"], "attributes": {"uploaded": True, "sourceFileChecksum": hashlib.md5(shot).hexdigest()}}})
        print("  review screenshot uploaded")
    else:
        print("  review screenshot already there")

time.sleep(5)
for i in all_pages(f"/v1/apps/{APP_ID}/inAppPurchasesV2", {"limit": 200}):
    print(f"{i['attributes']['productId']}: {i['attributes'].get('state')}")
