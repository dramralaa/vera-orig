"""فحص قراءة فقط (صفر كتابة) لكتالوج فيرا الحقيقي - على الفرعين المعروفين من
شاشة "معرف البائع" في بوابة هنجرستيشن (6 سبتمبر 2026):
- فيرا 1 (الروابي): vendor_id = 149439
- فيرا 2 (النرجس):  vendor_id = 174067
(84296 هو معرف الـ"Brand" مش vendor_id - مش هنستخدمه هنا).

الهدف: نشوف شكل كتالوج فيرا وهو شغّال وبيبيع فعليًا (على عكس دوم اللي كله
active=false)، عشان نفهم الفرق الحقيقي ونستخدمه كمرجع لحل لغز دوم لاحقًا.
"""
import json
import os

import requests

TOKEN_URL = "https://hungerstation.partner.deliveryhero.io/v2/oauth/token"
CLIENT_ID = os.environ.get("VERA_HUNGERSTATION_CLIENT_ID", "veraCL-68b31204-81e5-4ea6-a1c0-086ab7e94267")
CHAIN_ID = os.environ.get("VERA_HS_CHAIN_ID", "68b31204-81e5-4ea6-a1c0-086ab7e94267")

BRANCHES = {
    "فيرا 1 - الروابي": "149439",
    "فيرا 2 - النرجس": "174067",
}


def get_token():
    client_secret = os.environ["VERA_HUNGERSTATION_CLIENT_SECRET"]
    r = requests.post(
        TOKEN_URL,
        data={"grant_type": "client_credentials", "client_id": CLIENT_ID, "client_secret": client_secret},
        headers={"content-type": "application/x-www-form-urlencoded", "accept": "application/json"},
        timeout=20,
    )
    r.raise_for_status()
    return r.json()["access_token"]


def probe_branch(token, label, vendor_id):
    url = f"https://hungerstation.partner.deliveryhero.io/v2/chains/{CHAIN_ID}/vendors/{vendor_id}/catalog"
    print(f"\n=== {label} (vendor_id={vendor_id}) ===")
    r = requests.get(url, headers={"authorization": f"Bearer {token}", "accept": "application/json"},
                      params={"page_number": 1, "page_size": 50}, timeout=30)
    print(f"status: {r.status_code}")
    if r.status_code != 200:
        print(f"body: {r.text[:500]}")
        return
    data = r.json()
    products = data.get("products", [])
    total_pages = data.get("total_pages")
    active_count = sum(1 for p in products if p.get("active"))
    print(f"total_pages: {total_pages}, في هذه الصفحة: {len(products)}, active=true: {active_count}")
    if products:
        sample = products[0]
        print("مثال أول صنف:")
        print(json.dumps({k: v for k, v in sample.items() if k not in ("images", "translations")},
                          ensure_ascii=False, indent=2)[:1200])


def main():
    token = get_token()
    print("✅ access_token اتحصل عليه بنجاح")
    for label, vendor_id in BRANCHES.items():
        probe_branch(token, label, vendor_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
