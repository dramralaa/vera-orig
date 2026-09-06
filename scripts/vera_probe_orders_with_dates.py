"""endpoint الطلبات موجود ورجع 200 لكن فاضي (total_pages=0) بدون بارامترات.
نجرب أسماء بارامترات تاريخ شائعة (قراءة فقط) لنشوف هل محتاج نطاق تاريخ
عشان يرجّع طلبات فعلية.
"""
import os
from datetime import datetime, timedelta, timezone

import requests

BASE = "https://hungerstation.partner.deliveryhero.io"
CLIENT_ID = os.environ.get("VERA_HUNGERSTATION_CLIENT_ID", "veraCL-68b31204-81e5-4ea6-a1c0-086ab7e94267")
CHAIN_ID = os.environ.get("VERA_HS_CHAIN_ID", "68b31204-81e5-4ea6-a1c0-086ab7e94267")
VENDOR_ID = "149439"
URL = f"{BASE}/v2/chains/{CHAIN_ID}/vendors/{VENDOR_ID}/orders"


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
    ago_30d = now - timedelta(days=30)
    ago_90d = now - timedelta(days=90)

    date_fmt_variants = {
        "from/to (ISO date, 30d)": {"from": ago_30d.strftime("%Y-%m-%d"), "to": now.strftime("%Y-%m-%d")},
        "start_date/end_date (30d)": {"start_date": ago_30d.strftime("%Y-%m-%d"), "end_date": now.strftime("%Y-%m-%d")},
        "created_at_from/to (30d)": {"created_at_from": ago_30d.strftime("%Y-%m-%d"),
                                      "created_at_to": now.strftime("%Y-%m-%d")},
        "from/to (ISO datetime, 90d)": {"from": ago_90d.isoformat(), "to": now.isoformat()},
        "date_from/date_to (90d)": {"date_from": ago_90d.strftime("%Y-%m-%d"), "date_to": now.strftime("%Y-%m-%d")},
        "no params, page_size=100": {"page_size": 100},
    }

    for label, params in date_fmt_variants.items():
        r = requests.get(URL, headers=headers, params=params, timeout=20)
        print(f"[{r.status_code}] {label} -> params={params}")
        print(f"   body: {r.text[:400]}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
