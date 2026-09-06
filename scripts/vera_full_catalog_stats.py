"""فحص كامل (كل الصفحات، قراءة فقط - صفر كتابة) لكتالوج فيرا على الفرعين
عشان نطلع تقرير حالة شامل: إجمالي الأصناف، active/inactive، عينة أكواد،
التصنيفات المستخدمة، وشكل الباركود.
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


def fetch_all(token, vendor_id):
    url = f"https://hungerstation.partner.deliveryhero.io/v2/chains/{CHAIN_ID}/vendors/{vendor_id}/catalog"
    headers = {"authorization": f"Bearer {token}", "accept": "application/json"}
    r = requests.get(url, headers=headers, params={"page_number": 1, "page_size": 500}, timeout=30)
    r.raise_for_status()
    data = r.json()
    total_pages = data["total_pages"]
    products = list(data["products"])
    for page in range(2, total_pages + 1):
        r = requests.get(url, headers=headers, params={"page_number": page, "page_size": 500}, timeout=30)
        r.raise_for_status()
        products.extend(r.json().get("products", []))
        time.sleep(0.15)
    return products


def report(label, products):
    print(f"\n{'='*60}\n{label}\n{'='*60}")
    total = len(products)
    active = sum(1 for p in products if p.get("active"))
    print(f"إجمالي الأصناف: {total}")
    print(f"active=true: {active} ({active/total*100:.1f}%)")
    print(f"active=false: {total-active} ({(total-active)/total*100:.1f}%)")

    skus = [p["sku"] for p in products]
    numeric_skus = [s for s in skus if s.isdigit()]
    alnum_skus = [s for s in skus if not s.isdigit()]
    print(f"أكواد رقمية بحتة (زي جوليب): {len(numeric_skus)} ({len(numeric_skus)/total*100:.1f}%)")
    print(f"أكواد أبجدية-رقمية (ماستر قديم محتمل): {len(alnum_skus)} ({len(alnum_skus)/total*100:.1f}%)")

    has_barcode = sum(1 for p in products if p.get("barcodes"))
    has_image = sum(1 for p in products if p.get("images"))
    print(f"عندها باركود: {has_barcode} ({has_barcode/total*100:.1f}%)")
    print(f"عندها صورة: {has_image} ({has_image/total*100:.1f}%)")

    active_numeric = sum(1 for p in products if p.get("active") and p["sku"].isdigit())
    active_alnum = sum(1 for p in products if p.get("active") and not p["sku"].isdigit())
    print(f"من الـactive: رقمية={active_numeric}, أبجدية-رقمية={active_alnum}")

    cat_counter = Counter()
    for p in products:
        for c in p.get("categories", []):
            name = c.get("details", {}).get("name", {}).get("ar_SA")
            if name:
                cat_counter[name] += 1
    print("\nأهم 10 تصنيفات:")
    for name, count in cat_counter.most_common(10):
        print(f"  - {name}: {count}")

    print("\nعينة أصناف active=true:")
    for p in [p for p in products if p.get("active")][:5]:
        print(f"  sku={p['sku']}, price={p.get('price')}, barcode={p.get('barcodes')}, "
              f"title={p.get('title', '')[:50]}")

    return {"total": total, "active": active, "numeric_skus": len(numeric_skus),
            "has_barcode": has_barcode, "has_image": has_image}


def main():
    token = get_token()
    print("✅ access_token اتحصل عليه بنجاح\n")

    summary = {}
    for label, vendor_id in BRANCHES.items():
        products = fetch_all(token, vendor_id)
        summary[label] = report(label, products)

    print(f"\n{'='*60}\nملخص نهائي\n{'='*60}")
    print(json.dumps(summary, ensure_ascii=False, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
