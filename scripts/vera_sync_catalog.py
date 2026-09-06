"""مزامنة دورية (قراءة فقط - صفر كتابة على هنجرستيشن) لكتالوج فيرا على
الفرعين، بنفس فكرة `claude_data_bridge.py` عند دوم.

⚠️ قيد مؤكد من هنجرستيشن نفسها (6 سبتمبر 2026، bug مؤكد على السيرفر):
- `page_size` أقصى حد مسموح = 500 (أي رقم أكبر يرجّع 400 Bad Request).
- `page_number` بيتم تجاهله تمامًا من السيرفر - أي رقم صفحة تطلبه بيرجّعلك
  نفس الصفحة الأولى بالظبط (اتأكد بالاختبار مباشرة). يعني **مفيش طريقة
  نشوف بيها أكتر من أول 500 صنف من أي كتالوج عبر هذا الـAPI حاليًا** -
  مش مشكلة في السكربت، قيد حقيقي في الـendpoint. الكود هنا بيجيب صفحة
  واحدة بس (500 صنف) بدل ما يلف على صفحات فاضية/مكررة.
"""
import json
import os
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
    # page_number مكسور من عند هنجرستيشن (بيرجّع دايمًا صفحة 1) - بنجيب
    # page_size=500 (الحد الأقصى المسموح) مرة واحدة بس. لو الـbug اتصلح
    # مستقبلاً، السطر ده هو اللي محتاج يتغيّر لحلقة صفحات حقيقية.
    url = f"https://hungerstation.partner.deliveryhero.io/v2/chains/{CHAIN_ID}/vendors/{vendor_id}/catalog"
    headers = {"authorization": f"Bearer {token}", "accept": "application/json"}
    r = requests.get(url, headers=headers, params={"page_number": 1, "page_size": 500}, timeout=30)
    r.raise_for_status()
    data = r.json()
    return list(data["products"])


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
