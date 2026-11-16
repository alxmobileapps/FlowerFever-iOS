#!/usr/bin/env python3
"""Makes sure the App ID com.alxmobileapps.flowerfever exists in the Apple developer account
and has Sign in with Apple turned on (needed for the App Store signing profile). Safe to run every build.
Env: ASC_KEY_ID, ASC_ISSUER_ID, ASC_KEY_PATH (the .p8 file)."""
import os, sys, time
import jwt, requests

API = "https://api.appstoreconnect.apple.com"
BUNDLE_ID = "com.alxmobileapps.flowerfever"
NEED_APPLE_SIGNIN = "--apple-signin" in sys.argv

def token():
    now = int(time.time())
    return jwt.encode({"iss": os.environ["ASC_ISSUER_ID"], "iat": now, "exp": now + 1100, "aud": "appstoreconnect-v1"},
                      open(os.environ["ASC_KEY_PATH"]).read(), algorithm="ES256", headers={"kid": os.environ["ASC_KEY_ID"], "typ": "JWT"})

def call(method, path, body=None, params=None):
    r = requests.request(method, API + path, params=params, json=body, timeout=60,
                         headers={"Authorization": f"Bearer {token()}", "Content-Type": "application/json"})
    if r.status_code not in (200, 201, 204):
        raise SystemExit(f"{method} {path} -> {r.status_code}: {r.text[:500]}")
    return r.json() if r.content else {}

ids = call("GET", "/v1/bundleIds", params={"filter[identifier]": BUNDLE_ID, "limit": 20})["data"]
bundle = next((b for b in ids if b["attributes"].get("identifier") == BUNDLE_ID), None)
if not bundle:
    bundle = call("POST", "/v1/bundleIds", {"data": {"type": "bundleIds", "attributes": {
        "identifier": BUNDLE_ID, "name": "Flower Fever", "platform": "IOS"}}})["data"]
    print("App ID created:", BUNDLE_ID)
else:
    print("App ID exists:", BUNDLE_ID)

if NEED_APPLE_SIGNIN:
    caps = call("GET", f"/v1/bundleIds/{bundle['id']}/bundleIdCapabilities")["data"]
    have = {c["attributes"].get("capabilityType") for c in caps}
    if "APPLE_ID_AUTH" in have:
        print("Sign in with Apple: already on")
    else:
        call("POST", "/v1/bundleIdCapabilities", {"data": {"type": "bundleIdCapabilities",
            "attributes": {"capabilityType": "APPLE_ID_AUTH", "settings": [{"key": "APPLE_ID_AUTH_APP_CONSENT", "options": [{"key": "PRIMARY_APP_CONSENT"}]}]},
            "relationships": {"bundleId": {"data": {"type": "bundleIds", "id": bundle["id"]}}}}})
        print("Sign in with Apple: turned on")
