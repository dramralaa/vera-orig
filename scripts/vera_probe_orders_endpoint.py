"""استكشاف آمن (GET فقط - صفر كتابة) لمعرفة هل الـPartner API بتاع هنجرستيشن
فيه endpoint للطلبات/المبيعات (orders) زي ما فيه للكتالوج، عشان نعرف نجيب
مبيعات فيرا فعليًا زي ما بنجيب مبيعات دوم من جوليب/Odoo.
"""
import os

import requests

BASE = "https://hungerstation.partner.deliveryhero.io"
CLIENT_ID = os.environ.get("VERA_HUNGERSTATION_CLIENT_ID", "veraCL-68b31204-81e5-4ea6-a1c0-086ab7e94267")
CHAIN_ID = os.environ.get("VERA_HS_CHAIN_ID", "68b31204-81e5-4ea6-a1c0-086ab7e94267")
VENDOR_ID = "149439"

CANDIDATE_PATHS = [
    f"/v2/chains/{CHAIN_ID}/vendors/{VENDOR_ID}/orders",
    f"/v2/vendors/{VENDOR_ID}/orders",
    f"/v1/chains/{CHAIN_ID}/vendors/{VENDOR_ID}/orders",
    f"/v2/chains/{CHAIN_ID}/orders",
    f"/v2/orders",
    f"/v2/chains/{CHAIN_ID}/vendors/{VENDOR_ID}/order-history",
    f"/v2/chains/{CHAIN_ID}/vendors/{VENDOR_ID}/sales",
    f"/v2/chains/{CHAIN_ID}/vendors/{VENDOR_ID}/reports",
    f"/v2/chains/{CHAIN_ID}/vendors/{VENDOR_ID}/analytics",
    f"/v2/chains/{CHAIN_ID}/vendors/{VENDOR_ID}",
]


def get_token():
    client_secret = os.environ["VERA_HUNGERSTATION_CLIENT_SECRET"]
    r = requests.post(
        f"{BASE}/v2/oauth/token",
        data={"grant_type": "client_credentials", "client_id": CLIENT_ID, "client_secret": client_secret},
        headers={"content-type": "application/x-www-form-urlencoded", "accept": "application/json"},
        timeout=20,
    )
    r.raise_for_status()
    return r.json()["access_token"]


def main():
    token = get_token()
    print("✅ access_token اتحصل عليه بنجاح\n")
    headers = {"authorization": f"Bearer {token}", "accept": "application/json"}

    for path in CANDIDATE_PATHS:
        url = f"{BASE}{path}"
        try:
            r = requests.get(url, headers=headers, timeout=15)
            print(f"[{r.status_code}] GET {path}")
            if r.status_code == 200:
                print(f"   ✅ body (أول 500 حرف): {r.text[:500]}")
            elif r.status_code not in (404,):
                print(f"   ⚠️ body: {r.text[:300]}")
        except requests.RequestException as e:
            print(f"[ERROR] GET {path}: {e}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
