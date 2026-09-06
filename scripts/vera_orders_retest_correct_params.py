"""إعادة اختبار orders endpoint بالبارامترات الصحيحة من الـOpenAPI spec الرسمي:
start_time/end_time (مش from/to اللي جربناها غلط قبل كده)، وpage (مش page_number).
قراءة فقط.
"""
import os
from datetime import datetime, timedelta, timezone

import requests

BASE = "https://hungerstation.partner.deliveryhero.io"
CLIENT_ID = os.environ.get("VERA_HUNGERSTATION_CLIENT_ID", "veraCL-68b31204-81e5-4ea6-a1c0-086ab7e94267")
CHAIN_ID = os.environ.get("VERA_HS_CHAIN_ID", "68b31204-81e5-4ea6-a1c0-086ab7e94267")

BRANCHES = {"al_rawabi": "149439", "narjis": "174067"}


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

    now = datetime.now(timezone.utc)
    ago_60d = now - timedelta(days=59)  # أقصى حد مسموح 60 يوم

    for label, vendor_id in BRANCHES.items():
        url = f"{BASE}/v2/chains/{CHAIN_ID}/vendors/{vendor_id}/orders"
        params = {
            "start_time": ago_60d.strftime("%Y-%m-%dT%H:%M:%S"),
            "end_time": now.strftime("%Y-%m-%dT%H:%M:%S"),
            "page": 1,
            "page_size": 50,
        }
        r = requests.get(url, headers=headers, params=params, timeout=30)
        print(f"=== {label} (vendor_id={vendor_id}) ===")
        print(f"params: {params}")
        print(f"status: {r.status_code}")
        print(f"body (أول 1000 حرف): {r.text[:1000]}\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
