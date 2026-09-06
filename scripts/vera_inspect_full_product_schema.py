"""فحص سريع (قراءة فقط) - نطلع أول 3 أصناف كاملين بكل الحقول (من غير حذف أي
حقل) عشان نلاقي أي مرجع خارجي (external_id / merchant_sku / remote id) ممكن
يربط الـsku الأبجدي-الرقمي بتاع هنجرستيشن بكود جوليب/الصيدلية الحقيقي - ده
أهم حاجة ناقصانا عشان مستقبلاً نقدر نعمل مزامنة أسعار حقيقية.
"""
import json
import os

import requests

TOKEN_URL = "https://hungerstation.partner.deliveryhero.io/v2/oauth/token"
CLIENT_ID = os.environ.get("VERA_HUNGERSTATION_CLIENT_ID", "veraCL-68b31204-81e5-4ea6-a1c0-086ab7e94267")
CHAIN_ID = os.environ.get("VERA_HS_CHAIN_ID", "68b31204-81e5-4ea6-a1c0-086ab7e94267")
VENDOR_ID = "149439"


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
    print("✅ access_token اتحصل عليه بنجاح")
    url = f"https://hungerstation.partner.deliveryhero.io/v2/chains/{CHAIN_ID}/vendors/{VENDOR_ID}/catalog"
    headers = {"authorization": f"Bearer {token}", "accept": "application/json"}
    r = requests.get(url, headers=headers, params={"page_number": 1, "page_size": 3}, timeout=30)
    r.raise_for_status()

    print("\n=== Response headers (rate limit وغيرها) ===")
    for k, v in r.headers.items():
        if any(x in k.lower() for x in ("rate", "limit", "request-id", "trace")):
            print(f"  {k}: {v}")

    data = r.json()
    print(f"\ncatalog-level keys: {list(data.keys())}")

    products = data.get("products", [])
    for i, p in enumerate(products):
        print(f"\n=== صنف رقم {i+1} - كل الحقول بدون استثناء ===")
        print(f"كل المفاتيح: {list(p.keys())}")
        print(json.dumps(p, ensure_ascii=False, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
