"""تشخيص: هل الـpage_number بيتم تجاهله فعليًا من السيرفر؟ نطلب صفحة 1 و2 و3
صراحة بـpage_size صغير (20) ونقارن أول sku في كل رد + قيمة page_number
المرجعة نفسها في الرد (لو موجودة) عشان نفهم هل المشكلة عندنا ولا عند السيرفر.
"""
import json
import os

import requests

TOKEN_URL = "https://hungerstation.partner.deliveryhero.io/v2/oauth/token"
CLIENT_ID = os.environ.get("VERA_HUNGERSTATION_CLIENT_ID", "veraCL-68b31204-81e5-4ea6-a1c0-086ab7e94267")
CHAIN_ID = os.environ.get("VERA_HS_CHAIN_ID", "68b31204-81e5-4ea6-a1c0-086ab7e94267")
VENDOR_ID = "149439"
URL = f"https://hungerstation.partner.deliveryhero.io/v2/chains/{CHAIN_ID}/vendors/{VENDOR_ID}/catalog"


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


def main():
    token = get_token()
    print("✅ access_token اتحصل عليه بنجاح\n")
    headers = {"authorization": f"Bearer {token}", "accept": "application/json"}

    for page in [1, 2, 3, 1]:
        r = requests.get(URL, headers=headers, params={"page_number": page, "page_size": 20}, timeout=20)
        data = r.json()
        first_sku = data["products"][0]["sku"] if data.get("products") else None
        last_sku = data["products"][-1]["sku"] if data.get("products") else None
        print(f"طلب page_number={page} -> رد page_number={data.get('page_number')}, "
              f"total_pages={data.get('total_pages')}, أول sku={first_sku}, آخر sku={last_sku}")

    print("\n=== نفس الاختبار بـpage_size=500 (زي المزامنة) ===")
    for page in [1, 2, 3]:
        r = requests.get(URL, headers=headers, params={"page_number": page, "page_size": 500}, timeout=20)
        data = r.json()
        first_sku = data["products"][0]["sku"] if data.get("products") else None
        count = len(data.get("products", []))
        print(f"طلب page_number={page}, page_size=500 -> رد page_number={data.get('page_number')}, "
              f"total_pages={data.get('total_pages')}, عدد المنتجات={count}, أول sku={first_sku}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
