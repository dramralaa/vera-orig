"""اختبار كتابة آمن جدًا (بإذن صريح من صاحب المشروع، 6 سبتمبر 2026) على فرع
واحد بس من فيرا (الروابي) - صفر تغيير حقيقي: بناخد أول صنف من الكتالوج
الحقيقي المُزامَن، ونعيد إرسال نفس السعر بالظبط (no-op) عشان نشوف هل PUT
بيشتغل على فيرا (حساب شغّال فعليًا وبيبيع) ولا برضه بيرجع نفس خطأ
"Platform Not Found" اللي عند دوم - ده هيحسم نهائيًا هل المشكلة عامة في
الـPartner API ولا خاصة بحساب دوم بالذات.
"""
import json
import os

import requests

BASE = "https://hungerstation.partner.deliveryhero.io"
CLIENT_ID = os.environ.get("VERA_HUNGERSTATION_CLIENT_ID", "veraCL-68b31204-81e5-4ea6-a1c0-086ab7e94267")
CHAIN_ID = os.environ.get("VERA_HS_CHAIN_ID", "68b31204-81e5-4ea6-a1c0-086ab7e94267")
VENDOR_ID = "149439"  # فيرا 1 - الروابي بس، مش الاتنين


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
    print("✅ access_token اتحصل عليه بنجاح")
    url = f"{BASE}/v2/chains/{CHAIN_ID}/vendors/{VENDOR_ID}/catalog"
    headers_get = {"authorization": f"Bearer {token}", "accept": "application/json"}

    # نجيب صنف حقيقي وسعره الحالي بالظبط (أول صفحة كفاية)
    r = requests.get(url, headers=headers_get, params={"page": 1, "page_size": 1}, timeout=30)
    r.raise_for_status()
    product = r.json()["products"][0]
    sku = product["sku"]
    price = product["price"]
    print(f"صنف الاختبار: sku={sku}, السعر الحالي={price} (هنبعت نفس القيمة بالظبط - صفر تغيير)")

    headers_put = {"authorization": f"Bearer {token}", "accept": "application/json", "content-type": "application/json"}
    payload = {"products": [{"sku": sku, "price": float(price)}]}

    r = requests.put(url, json=payload, headers=headers_put, timeout=20)
    print(f"\n=== PUT (no-op) على فيرا 1 - الروابي ===")
    print(f"status: {r.status_code}")
    print(f"body: {r.text[:1000]}")

    # تأكيد إضافي: نعيد قراءة نفس الصنف بعد الطلب للتأكد إن السعر لسه زي ما هو
    r2 = requests.get(url, headers=headers_get, params={"page": 1, "page_size": 1, "query_term": sku}, timeout=30)
    if r2.status_code == 200 and r2.json().get("products"):
        after_price = r2.json()["products"][0].get("price")
        print(f"\nالسعر بعد الطلب: {after_price} (المفروض يبقى {price} بالظبط)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
