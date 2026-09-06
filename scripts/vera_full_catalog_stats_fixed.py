"""إصلاح جذري: لقينا في الـOpenAPI spec الرسمي إن اسم الـquery parameter
الصحيح لرقم الصفحة هو "page" مش "page_number" اللي كنا بنبعته طول الوقت.
هذا يفسر ليه كل صفحة كانت بترجع نفس البيانات (السيرفر كان بيتجاهل
"page_number" غير المعروف وبيستخدم الافتراضي page=1 دايمًا).

فحص كامل حقيقي (بالباراميتر الصحيح) لكتالوج الفرعين.
"""
import json
import os
import time
from collections import Counter

import requests

TOKEN_URL = "https://hungerstation.partner.deliveryhero.io/v2/oauth/token"
CLIENT_ID = os.environ.get("VERA_HUNGERSTATION_CLIENT_ID", "veraCL-68b31204-81e5-4ea6-a1c0-086ab7e94267")
CHAIN_ID = os.environ.get("VERA_HS_CHAIN_ID", "68b31204-81e5-4ea6-a1c0-086ab7e94267")

BRANCHES = {
    "al_rawabi": {"label": "فيرا 1 - الروابي", "vendor_id": "149439"},
    "narjis": {"label": "فيرا 2 - النرجس", "vendor_id": "174067"},
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


def fetch_all(token, vendor_id, label):
    url = f"https://hungerstation.partner.deliveryhero.io/v2/chains/{CHAIN_ID}/vendors/{vendor_id}/catalog"
    headers = {"authorization": f"Bearer {token}", "accept": "application/json"}
    r = requests.get(url, headers=headers, params={"page": 1, "page_size": 500}, timeout=30)
    r.raise_for_status()
    data = r.json()
    total_pages = data["total_pages"]
    products = list(data["products"])
    print(f"{label}: صفحة 1/{total_pages}, أول sku={products[0]['sku'] if products else None}")

    for page in range(2, total_pages + 1):
        r = requests.get(url, headers=headers, params={"page": page, "page_size": 500}, timeout=30)
        r.raise_for_status()
        page_data = r.json()
        page_products = page_data.get("products", [])
        print(f"{label}: صفحة {page}/{total_pages}, رد page_number={page_data.get('page_number')}, "
              f"أول sku في الصفحة={page_products[0]['sku'] if page_products else None}")
        products.extend(page_products)
        time.sleep(0.2)
    return products


def main():
    token = get_token()
    print("✅ access_token اتحصل عليه بنجاح\n")

    for key, info in BRANCHES.items():
        products = fetch_all(token, info["vendor_id"], info["label"])
        unique_skus = len({p["sku"] for p in products})
        active = sum(1 for p in products if p.get("active"))
        print(f"\n=== {info['label']} - النتيجة النهائية ===")
        print(f"إجمالي مجموع: {len(products)}, unique SKUs: {unique_skus}, active=true: {active} "
              f"({active/len(products)*100:.1f}%)\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
