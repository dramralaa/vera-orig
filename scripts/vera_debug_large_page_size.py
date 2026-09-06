"""بما إن page_number اتأكد إنه bug حقيقي في سيرفر هنجرستيشن (بيتم تجاهله دايمًا
ويرجّع صفحة 1)، الطريقة الوحيدة المتبقية لمحاولة رؤية أكتر من الكتالوج هي زيادة
page_size لأقصى حد ممكن. قراءة فقط.
"""
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

    for page_size in [500, 1000, 2000, 5000, 10000]:
        r = requests.get(URL, headers=headers, params={"page_number": 1, "page_size": page_size}, timeout=30)
        try:
            data = r.json()
            count = len(data.get("products", []))
            unique_skus = len({p["sku"] for p in data.get("products", [])})
            print(f"page_size={page_size} -> status={r.status_code}, page_size_رد={data.get('page_size')}, "
                  f"total_pages={data.get('total_pages')}, عدد فعلي={count}, unique_skus={unique_skus}")
        except Exception as e:
            print(f"page_size={page_size} -> status={r.status_code}, خطأ في التحليل: {e}, body: {r.text[:200]}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
