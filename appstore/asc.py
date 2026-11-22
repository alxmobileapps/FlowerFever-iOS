#!/usr/bin/env python3
"""
App Store Connect setup for Flower Fever (iPhone), via the App Store Connect API.

  python asc.py prepare       version string, content rights, age rating,
                              price (Free), availability, in-app purchases
  python asc.py attach-build  attach the newest processed build to the version

Every step is idempotent (safe to re-run) and failures are reported but don't
stop the other steps. A summary is written to $REPORT (default report.txt).

Env: ASC_KEY_ID, ASC_ISSUER_ID, ASC_KEY_PATH (the .p8), IOS_APP_VERSION,
     IAP_SCREENSHOT (PNG used as the in-app purchase review screenshot).
"""
import hashlib
import json
import os
import sys
import time

import jwt
import requests

API = "https://api.appstoreconnect.apple.com"
BUNDLE_ID = "com.alxmobileapps.flowerfever"
VERSION = os.environ.get("IOS_APP_VERSION", "1.0.0")
REPORT = os.environ.get("REPORT", "report.txt")

# Games need a government license to be sold in mainland China.
EXCLUDED_TERRITORIES = {"CHN"}

IAPS = [
    {"productId": "com.alxmobileapps.flowerfever.starter30", "type": "CONSUMABLE", "refName": "Starter Pack 30 Diamonds", "name": "Starter Pack", "description": "30 diamonds + 3 free lifelines. Once only.", "usd": "0.99", "screenshot": "resources/iap-review.png", "reviewNote": "Diamond shop > Starter deal (top). Adds 30 diamonds and 3 free lifelines; offered once."},
    {"productId": "com.alxmobileapps.flowerfever.gems10", "type": "CONSUMABLE", "refName": "10 Diamonds", "name": "10 Diamonds", "description": "10 diamonds for lifelines and the garden.", "usd": "0.99", "screenshot": "resources/iap-review.png", "reviewNote": "Diamond shop > 10 diamonds. Adds 10 diamonds (in-game currency)."},
    {"productId": "com.alxmobileapps.flowerfever.gems25", "type": "CONSUMABLE", "refName": "25 Diamonds", "name": "25 Diamonds", "description": "25 diamonds for lifelines and the garden.", "usd": "1.99", "screenshot": "resources/iap-review.png", "reviewNote": "Diamond shop > 25 diamonds."},
    {"productId": "com.alxmobileapps.flowerfever.gems60", "type": "CONSUMABLE", "refName": "60 Diamonds", "name": "60 Diamonds", "description": "60 diamonds for lifelines and the garden.", "usd": "3.99", "screenshot": "resources/iap-review.png", "reviewNote": "Diamond shop > 60 diamonds."},
    {"productId": "com.alxmobileapps.flowerfever.gems170", "type": "CONSUMABLE", "refName": "170 Diamonds", "name": "170 Diamonds", "description": "170 diamonds for lifelines and the garden.", "usd": "9.99", "screenshot": "resources/iap-review.png", "reviewNote": "Diamond shop > 170 diamonds."},
    {"productId": "com.alxmobileapps.flowerfever.gems400", "type": "CONSUMABLE", "refName": "400 Diamonds", "name": "400 Diamonds", "description": "400 diamonds for lifelines and the garden.", "usd": "19.99", "screenshot": "resources/iap-review.png", "reviewNote": "Diamond shop > 400 diamonds."},
    {"productId": "com.alxmobileapps.flowerfever.noads100", "type": "NON_CONSUMABLE", "refName": "No Ads + 100 Diamonds", "name": "No Ads + 100 Diamonds", "description": "No forced ads, plus 100 diamonds.", "usd": "5.99", "screenshot": "resources/iap-review.png", "reviewNote": "Diamond shop > No ads (100 diamonds + no forced ads). Restorable with 'Restore purchases' in the Diamond shop and in Settings."},
]

report_lines = []


def log(status, msg):
    line = f"{status:5} {msg}"
    print(line, flush=True)
    report_lines.append(line)


def write_report():
    failed = sum(1 for l in report_lines if l.startswith("FAIL"))
    head = "RESULT: ALL OK" if not failed else f"RESULT: {failed} step(s) FAILED"
    with open(REPORT, "a") as f:
        f.write("\n".join([head, ""] + report_lines) + "\n\n")


_token = {"value": None, "exp": 0}


def token():
    if time.time() < _token["exp"] - 60:
        return _token["value"]
    key = open(os.environ["ASC_KEY_PATH"]).read()
    now = int(time.time())
    _token["value"] = jwt.encode(
        {"iss": os.environ["ASC_ISSUER_ID"], "iat": now, "exp": now + 1100, "aud": "appstoreconnect-v1"},
        key,
        algorithm="ES256",
        headers={"kid": os.environ["ASC_KEY_ID"], "typ": "JWT"},
    )
    _token["exp"] = now + 1100
    return _token["value"]


class ApiError(Exception):
    pass


def call(method, path, body=None, params=None, ok=(200, 201, 204)):
    url = path if path.startswith("http") else API + path
    r = requests.request(
        method, url, params=params, json=body,
        headers={"Authorization": f"Bearer {token()}", "Content-Type": "application/json"},
        timeout=60,
    )
    if r.status_code not in ok:
        try:
            errs = r.json().get("errors", [])
            detail = "; ".join(f"{e.get('title')}: {e.get('detail')}" for e in errs) or r.text[:400]
        except Exception:
            detail = r.text[:400]
        raise ApiError(f"{method} {path} -> {r.status_code}: {detail}")
    return r.json() if r.content else {}


def get_all(path, params=None):
    out, url, p = [], path, dict(params or {})
    p.setdefault("limit", 200)
    while url:
        data = call("GET", url, params=p)
        out += data.get("data", [])
        url, p = data.get("links", {}).get("next"), None
    return out


def step(name):
    def wrap(fn):
        def run(*a, **kw):
            try:
                res = fn(*a, **kw)
                log("OK", f"{name}{(': ' + res) if isinstance(res, str) and res else ''}")
            except Exception as e:  # keep going with the other steps
                log("FAIL", f"{name}: {e}")
        return run
    return wrap


def find_app():
    apps = call("GET", "/v1/apps", params={"filter[bundleId]": BUNDLE_ID})["data"]
    if not apps:
        raise SystemExit(f"No app with bundle id {BUNDLE_ID} in App Store Connect")
    return apps[0]


def editable_version(app_id):
    versions = get_all(f"/v1/apps/{app_id}/appStoreVersions", {"filter[platform]": "IOS"})
    editable = [v for v in versions if v["attributes"]["appStoreState"] in
                ("PREPARE_FOR_SUBMISSION", "DEVELOPER_REJECTED", "REJECTED", "METADATA_REJECTED", "INVALID_BINARY")]
    if not editable:
        # the live version is done: start the next one (an update) with VERSION
        if any(v["attributes"]["versionString"] == VERSION for v in versions):
            raise ApiError(f"version {VERSION} exists and is not editable - raise IOS_APP_VERSION")
        new = call("POST", "/v1/appStoreVersions", {"data": {"type": "appStoreVersions",
                   "attributes": {"platform": "IOS", "versionString": VERSION, "releaseType": "AFTER_APPROVAL"},
                   "relationships": {"app": {"data": {"type": "apps", "id": app_id}}}}})["data"]
        log("OK", f"new App Store version {VERSION} created")
        return new
    return editable[0]


def territories():
    return [t["id"] for t in get_all("/v1/territories") if t["id"] not in EXCLUDED_TERRITORIES]


# ---------------------------------------------------------------- prepare

@step("Version string")
def set_version(app_id):
    v = editable_version(app_id)
    if v["attributes"]["versionString"] == VERSION:
        return f"already {VERSION}"
    call("PATCH", f"/v1/appStoreVersions/{v['id']}", {"data": {
        "type": "appStoreVersions", "id": v["id"], "attributes": {"versionString": VERSION}}})
    return f"{v['attributes']['versionString']} -> {VERSION}"


@step("Content rights (no third-party content)")
def set_content_rights(app_id):
    call("PATCH", f"/v1/apps/{app_id}", {"data": {"type": "apps", "id": app_id, "attributes": {
        "contentRightsDeclaration": "DOES_NOT_USE_THIRD_PARTY_CONTENT"}}})


FREQUENCY_FIELDS = {
    "alcoholTobaccoOrDrugUseOrReferences", "contests", "gamblingSimulated", "gunsOrOtherWeapons",
    "horrorOrFearThemes", "matureOrSuggestiveThemes", "medicalOrTreatmentInformation",
    "profanityOrCrudeHumor", "sexualContentGraphicAndNudity", "sexualContentOrNudity",
    "violenceCartoonOrFantasy", "violenceRealistic", "violenceRealisticProlongedGraphicOrSadistic",
}
BOOL_FIELDS_TRUE = {"userGeneratedContent", "advertising"}  # friends' nicknames; AdMob ads
BOOL_FIELDS_FALSE = {
    "socialMedia", "socialMediaAgeRestricted",
    "gambling", "unrestrictedWebAccess", "lootBox", "messagingAndChat", "parentalControls",
    "ageAssurance", "healthOrWellnessTopics", "seventeenPlus",
}


@step("Age rating questionnaire")
def set_age_rating(app_id):
    infos = get_all(f"/v1/apps/{app_id}/appInfos")
    info = next((i for i in infos if i["attributes"].get("appStoreState") in
                 ("PREPARE_FOR_SUBMISSION", "DEVELOPER_REJECTED", "REJECTED", "INVALID_BINARY", None)
                 or i["attributes"].get("state") in ("PREPARE_FOR_SUBMISSION", "READY_FOR_DISTRIBUTION_EDITABLE")), infos[0])
    decl = call("GET", f"/v1/appInfos/{info['id']}/ageRatingDeclaration")["data"]
    current = decl["attributes"]
    attrs = {}
    for k in current:
        if k in FREQUENCY_FIELDS:
            attrs[k] = "NONE"
        elif k in BOOL_FIELDS_TRUE:
            attrs[k] = True
        elif k in BOOL_FIELDS_FALSE:
            attrs[k] = False
    # Fields Apple returns but we don't recognise: fill by value type.
    for k, v in current.items():
        if k not in attrs and isinstance(v, bool):
            attrs[k] = False
    dropped = []
    for _ in range(10):
        try:
            call("PATCH", f"/v1/ageRatingDeclarations/{decl['id']}", {"data": {
                "type": "ageRatingDeclarations", "id": decl["id"], "attributes": attrs}})
            break
        except ApiError as e:
            bad = [k for k in attrs if k in str(e)]
            if not bad:
                raise
            for k in bad:
                attrs.pop(k)
                dropped.append(k)
    unset = [k for k, v in current.items() if k not in attrs and v is None and k not in
             ("kidsAgeBand", "ageRatingOverride", "ageRatingOverrideV2", "koreaAgeRatingOverride",
              "developerAgeRatingInfoUrl")]
    msg = f"set {len(attrs)} answers"
    if dropped:
        msg += f"; Apple rejected: {', '.join(dropped)}"
    if unset:
        msg += f"; still unanswered (do in web): {', '.join(unset)}"
    return msg


@step("Price: Free")
def set_free(app_id):
    try:
        existing = call("GET", f"/v1/apps/{app_id}/appPriceSchedule")
        if existing.get("data"):
            manual = call("GET", f"/v1/appPriceSchedules/{existing['data']['id']}/manualPrices",
                          params={"include": "appPricePoint", "limit": 5})
            for inc in manual.get("included", []):
                if inc["type"] == "appPricePoints" and float(inc["attributes"]["customerPrice"]) == 0:
                    return "already Free"
    except ApiError:
        pass
    points = get_all(f"/v1/apps/{app_id}/appPricePoints", {"filter[territory]": "USA"})
    free = next(p for p in points if float(p["attributes"]["customerPrice"]) == 0)
    call("POST", "/v1/appPriceSchedules", {
        "data": {"type": "appPriceSchedules", "relationships": {
            "app": {"data": {"type": "apps", "id": app_id}},
            "baseTerritory": {"data": {"type": "territories", "id": "USA"}},
            "manualPrices": {"data": [{"type": "appPrices", "id": "${p0}"}]}}},
        "included": [{"type": "appPrices", "id": "${p0}", "attributes": {"startDate": None},
                      "relationships": {"appPricePoint": {"data": {"type": "appPricePoints", "id": free["id"]}}}}],
    })


@step("Availability: all countries except mainland China")
def set_availability(app_id, terr):
    try:
        cur = call("GET", f"/v1/apps/{app_id}/appAvailabilityV2")
        if cur.get("data"):
            return "already set (left unchanged)"
    except ApiError:
        pass
    all_terr = [t["id"] for t in get_all("/v1/territories")]
    included = [{"type": "territoryAvailabilities", "id": f"${{{t}}}",
                 "attributes": {"available": t not in EXCLUDED_TERRITORIES},
                 "relationships": {"territory": {"data": {"type": "territories", "id": t}}}} for t in all_terr]
    body = {
        "data": {"type": "appAvailabilities", "attributes": {"availableInNewTerritories": True},
                 "relationships": {
                     "app": {"data": {"type": "apps", "id": app_id}},
                     "territoryAvailabilities": {"data": [{"type": "territoryAvailabilities", "id": i["id"]} for i in included]}}},
        "included": included,
    }
    try:
        call("POST", "/v2/appAvailabilities", body)
    except ApiError as e:
        if "expects an included resource with type 'territories'" not in str(e):
            raise
        body["included"] = included + [{"type": "territories", "id": t} for t in all_terr]
        call("POST", "/v2/appAvailabilities", body)
    return f"{len(terr)} countries (mainland China off)"


def upload_review_screenshot(iap_id, path):
    existing = call("GET", f"/v2/inAppPurchases/{iap_id}/appStoreReviewScreenshot")
    if existing.get("data") and existing["data"]["attributes"].get("assetDeliveryState", {}).get("state") == "COMPLETE":
        return "screenshot already there"
    blob = open(path, "rb").read()
    res = call("POST", "/v1/inAppPurchaseAppStoreReviewScreenshots", {"data": {
        "type": "inAppPurchaseAppStoreReviewScreenshots",
        "attributes": {"fileName": os.path.basename(path), "fileSize": len(blob)},
        "relationships": {"inAppPurchaseV2": {"data": {"type": "inAppPurchases", "id": iap_id}}}}})["data"]
    for op in res["attributes"]["uploadOperations"]:
        chunk = blob[op["offset"]: op["offset"] + op["length"]]
        headers = {h["name"]: h["value"] for h in op.get("requestHeaders", [])}
        r = requests.request(op["method"], op["url"], data=chunk, headers=headers, timeout=120)
        r.raise_for_status()
    call("PATCH", f"/v1/inAppPurchaseAppStoreReviewScreenshots/{res['id']}", {"data": {
        "type": "inAppPurchaseAppStoreReviewScreenshots", "id": res["id"],
        "attributes": {"uploaded": True, "sourceFileChecksum": hashlib.md5(blob).hexdigest()}}})
    return "screenshot uploaded"


def setup_iap(app_id, spec, terr):
    pid = spec["productId"]
    existing = get_all(f"/v1/apps/{app_id}/inAppPurchasesV2", {"filter[productId]": pid})
    if existing:
        iap_id = existing[0]["id"]
        notes = ["exists"]
        try:
            call("PATCH", f"/v2/inAppPurchases/{iap_id}", {"data": {"type": "inAppPurchases", "id": iap_id,
                 "attributes": {"reviewNote": spec["reviewNote"]}}})
            notes.append("review note")
        except ApiError as e:
            notes.append(f"review note not set ({e})")
    else:
        iap_id = call("POST", "/v2/inAppPurchases", {"data": {
            "type": "inAppPurchases",
            "attributes": {"name": spec["refName"], "productId": pid, "inAppPurchaseType": spec["type"],
                           "reviewNote": spec["reviewNote"], "familySharable": False},
            "relationships": {"app": {"data": {"type": "apps", "id": app_id}}}}})["data"]["id"]
        notes = ["created"]

    locs = get_all(f"/v2/inAppPurchases/{iap_id}/inAppPurchaseLocalizations")
    if not any(l["attributes"]["locale"] == "en-US" for l in locs):
        call("POST", "/v1/inAppPurchaseLocalizations", {"data": {
            "type": "inAppPurchaseLocalizations",
            "attributes": {"locale": "en-US", "name": spec["name"], "description": spec["description"]},
            "relationships": {"inAppPurchaseV2": {"data": {"type": "inAppPurchases", "id": iap_id}}}}})
        notes.append("en-US text")

    try:
        sched = call("GET", f"/v2/inAppPurchases/{iap_id}/iapPriceSchedule")
        has_price = bool(sched.get("data"))
    except ApiError:
        has_price = False
    if not has_price:
        points = get_all(f"/v2/inAppPurchases/{iap_id}/pricePoints", {"filter[territory]": "USA"})
        point = next(p for p in points if p["attributes"]["customerPrice"] in (spec["usd"], spec["usd"] + "0"))
        call("POST", "/v1/inAppPurchasePriceSchedules", {
            "data": {"type": "inAppPurchasePriceSchedules", "relationships": {
                "inAppPurchase": {"data": {"type": "inAppPurchases", "id": iap_id}},
                "baseTerritory": {"data": {"type": "territories", "id": "USA"}},
                "manualPrices": {"data": [{"type": "inAppPurchasePrices", "id": "${p0}"}]}}},
            "included": [{"type": "inAppPurchasePrices", "id": "${p0}", "attributes": {"startDate": None},
                          "relationships": {"inAppPurchasePricePoint": {"data": {
                              "type": "inAppPurchasePricePoints", "id": point["id"]}}}}],
        })
        notes.append(f"price ${spec['usd']} (other countries auto-converted)")

    try:
        avail = call("GET", f"/v2/inAppPurchases/{iap_id}/inAppPurchaseAvailability")
        has_avail = bool(avail.get("data"))
    except ApiError:
        has_avail = False
    if not has_avail:
        call("POST", "/v1/inAppPurchaseAvailabilities", {"data": {
            "type": "inAppPurchaseAvailabilities", "attributes": {"availableInNewTerritories": True},
            "relationships": {
                "inAppPurchase": {"data": {"type": "inAppPurchases", "id": iap_id}},
                "availableTerritories": {"data": [{"type": "territories", "id": t} for t in terr]}}}})
        notes.append("availability")

    shot = spec.get("screenshot") or os.environ.get("IAP_SCREENSHOT")
    if shot and os.path.exists(shot):
        notes.append(upload_review_screenshot(iap_id, shot))
    else:
        notes.append("NO review screenshot file")
    return ", ".join(notes)


def prepare():
    app = find_app()
    app_id = app["id"]
    log("OK", f"Found app {app['attributes']['name']} ({app_id})")
    set_version(app_id)
    set_content_rights(app_id)
    set_age_rating(app_id)
    set_free(app_id)
    try:
        terr = territories()
    except Exception as e:
        log("FAIL", f"List territories: {e}")
        terr = []
    if terr:
        set_availability(app_id, terr)
        for spec in IAPS:
            step(f"In-app purchase {spec['productId']}")(setup_iap)(app_id, spec, terr)


def attach_build():
    app = find_app()
    app_id = app["id"]
    version = editable_version(app_id)
    # MIN_BUILD: only attach a build at least this new (waits up to ~30 min
    # for Apple to finish processing it).
    min_build = int(os.environ.get("MIN_BUILD") or 0)
    b = None
    for _ in range(60):
        builds = call("GET", "/v1/builds", params={
            "filter[app]": app_id, "filter[preReleaseVersion.version]": VERSION,
            "filter[processingState]": "VALID", "sort": "-uploadedDate", "limit": 10})["data"]
        builds = [x for x in builds if int(x["attributes"]["version"]) >= min_build]
        if builds:
            b = max(builds, key=lambda x: int(x["attributes"]["version"]))
            break
        if not min_build:
            break
        time.sleep(30)
    if not b:
        log("FAIL", f"Attach build: no processed build >= {min_build} for version {VERSION} yet")
        return
    call("PATCH", f"/v1/appStoreVersions/{version['id']}/relationships/build",
         {"data": {"type": "builds", "id": b["id"]}})
    log("OK", f"Attach build: build {b['attributes']['version']} attached to version {VERSION}")


def submit():
    """First submission: the in-app purchases go in with the app version (Apple's rule for the first ones)."""
    app = find_app(); app_id = app["id"]
    version = editable_version(app_id)
    v = call("GET", f"/v1/appStoreVersions/{version['id']}/build").get("data")
    if not v:
        log("FAIL", "submit: no build attached to the version"); return
    log("INFO", f"version {version['attributes']['versionString']} with build {v['attributes']['version']}")
    # App Review notes + contact (also set by fastlane, kept here so a re-run of submit alone is complete)
    notes = open(os.path.join(os.path.dirname(__file__), "metadata", "review_information", "notes.txt")).read().strip()
    detail = call("GET", f"/v1/appStoreVersions/{version['id']}/appStoreReviewDetail").get("data")
    if detail:
        call("PATCH", f"/v1/appStoreReviewDetails/{detail['id']}", {"data": {"type": "appStoreReviewDetails", "id": detail["id"], "attributes": {"notes": notes}}})
        log("OK", f"review notes ({len(notes)} chars)")
    for spec in IAPS:
        iap = get_all(f"/v1/apps/{app_id}/inAppPurchasesV2", {"filter[productId]": spec["productId"]})
        if not iap: log("FAIL", f"missing IAP {spec['productId']}"); continue
        st = iap[0]["attributes"].get("state")
        if st != "READY_TO_SUBMIT":
            log("INFO", f"{spec['productId']}: {st} (not submitted again)"); continue
        try:
            call("POST", "/v1/inAppPurchaseSubmissions", {"data": {"type": "inAppPurchaseSubmissions",
                 "relationships": {"inAppPurchaseV2": {"data": {"type": "inAppPurchases", "id": iap[0]["id"]}}}}})
            log("OK", f"IAP added to the submission: {spec['productId']}")
        except ApiError as e:
            log("FAIL", f"IAP {spec['productId']}: {e}")
    subs = get_all("/v1/reviewSubmissions", {"filter[app]": app_id, "filter[platform]": "IOS"})
    sub = next((s for s in subs if s["attributes"].get("state") in ("READY_FOR_REVIEW", "UNRESOLVED_ISSUES")), None)
    if not sub:
        sub = call("POST", "/v1/reviewSubmissions", {"data": {"type": "reviewSubmissions", "attributes": {"platform": "IOS"},
                   "relationships": {"app": {"data": {"type": "apps", "id": app_id}}}}})["data"]
        log("OK", f"review submission created {sub['id']}")
    items = get_all(f"/v1/reviewSubmissions/{sub['id']}/items")
    if not any((i.get("relationships") or {}).get("appStoreVersion") for i in items) or not items:
        try:
            call("POST", "/v1/reviewSubmissionItems", {"data": {"type": "reviewSubmissionItems", "relationships": {
                "reviewSubmission": {"data": {"type": "reviewSubmissions", "id": sub["id"]}},
                "appStoreVersion": {"data": {"type": "appStoreVersions", "id": version["id"]}}}}})
            log("OK", "app version added to the submission")
        except ApiError as e:
            log("INFO", f"add version: {e}")
    if os.environ.get("DRY_RUN") == "1":
        log("INFO", "DRY_RUN: not submitting"); return
    call("PATCH", f"/v1/reviewSubmissions/{sub['id']}", {"data": {"type": "reviewSubmissions", "id": sub["id"], "attributes": {"submitted": True}}})
    time.sleep(5)
    s = call("GET", f"/v1/reviewSubmissions/{sub['id']}")["data"]
    log("OK", f"SUBMITTED for App Review: state={s['attributes'].get('state')}")


def status():
    """Read only: versions, their builds and the review submissions."""
    app = find_app(); app_id = app["id"]
    for v in get_all(f"/v1/apps/{app_id}/appStoreVersions", {"filter[platform]": "IOS"}):
        b = call("GET", f"/v1/appStoreVersions/{v['id']}/build").get("data")
        log("INFO", f"version {v['attributes']['versionString']}: {v['attributes']['appStoreState']}, build {b['attributes']['version'] if b else '-'}")
    for sub in get_all("/v1/reviewSubmissions", {"filter[app]": app_id, "filter[platform]": "IOS"})[:5]:
        log("INFO", f"submission {sub['attributes'].get('submittedDate')}: {sub['attributes'].get('state')}")
    for i in get_all(f"/v1/apps/{app_id}/inAppPurchasesV2"):
        log("INFO", f"IAP {i['attributes']['productId']}: {i['attributes'].get('state')}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "prepare"
    try:
        {"prepare": prepare, "attach-build": attach_build, "submit": submit, "status": status}[cmd]()
    except Exception as e:
        log("FAIL", f"{cmd}: {e}")
    write_report()
