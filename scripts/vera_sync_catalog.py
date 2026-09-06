"""مزامنة دورية (قراءة فقط - صفر كتابة على هنجرستيشن) لكتالوج فيرا الكامل على
الفرعين، بنفس فكرة `claude_data_bridge.py` عند دوم.

⚠️ تصحيح حرج (6 سبتمبر 2026): الفرضية السابقة إن "page_number مكسور من عند
هنجرستيشن" كانت غلط - السبب الحقيقي إن اسم الـquery parameter الصحيح هو
"page" مش "page_number" (اتأكد من الـOpenAPI spec الرسمي). دلوقتي بنستخدم
"page" الصح وبنسحب الكتالوج الكامل الحقيقي (مش أول 500 صنف بس).
`page_size` لسه أقصى حد مسموح = 500 لكل طلب.
"""
import json
import os
import time
from collections import Counter
from datetime import datetime, timezone

import requests

TOKEN_URL = "https://hungerstation.partner.deliveryhero.io/v2/oauth/token"
CLIENT_ID = os.environ.get("VERA_HUNGERSTATION_CLIENT_ID", "veraCL-68b31204-81e5-4ea6-a1c0-086ab7e94267")
CHAIN_ID = os.environ.get("VERA_HS_CHAIN_ID", "68b31204-81e5-4ea6-a1c0-086ab7e94267")

BRANCHES = {
    "al_rawabi": {"label": "فيرا 1 - الروابي", "vendor_id": "149439"},
    "narjis": {"label": "فيرا 2 - النرجس", "vendor_id": "174067"},
}

DATA_DIR = "data"


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
    r = requests.get(url, headers=headers, params={"page": 1, "page_size": 500}, timeout=30)
    r.raise_for_status()
    data = r.json()
    total_pages = data["total_pages"]
    products = list(data["products"])
    for page in range(2, total_pages + 1):
        r = requests.get(url, headers=headers, params={"page": page, "page_size": 500}, timeout=30)
        r.raise_for_status()
        products.extend(r.json().get("products", []))
        time.sleep(0.2)
    return products


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    token = get_token()
    print("✅ access_token اتحصل عليه بنجاح")

    summary = {"synced_at_utc": datetime.now(timezone.utc).isoformat(), "branches": {}}

    for key, info in BRANCHES.items():
        products = fetch_all(token, info["vendor_id"])
        out_path = os.path.join(DATA_DIR, f"vera_catalog_{key}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(products, f, ensure_ascii=False)
        print(f"💾 {info['label']}: {len(products)} صنف -> {out_path}")

        active = sum(1 for p in products if p.get("active"))
        cat_counter = Counter()
        for p in products:
            for c in p.get("categories", []):
                name = c.get("details", {}).get("name", {}).get("ar_SA")
                if name:
                    cat_counter[name] += 1

        summary["branches"][key] = {
            "label": info["label"],
            "vendor_id": info["vendor_id"],
            "total": len(products),
            "active": active,
            "active_pct": round(active / len(products) * 100, 1) if products else 0,
            "top_categories": cat_counter.most_common(10),
        }

    summary_path = os.path.join(DATA_DIR, "vera_catalog_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"💾 ملخص -> {summary_path}")
    print(json.dumps(summary, ensure_ascii=False, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
