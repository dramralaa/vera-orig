"""اختبار حاسم (بإذن صريح من صاحب المشروع لإضافة أصناف جديدة): هل PUT
.../catalog بيقدر يُنشئ صنف جديد كليًا (مش موجود قبل كده في كتالوج هنجرستيشن)
ولا بس بيعدّل صنف موجود بالفعل؟ الـschema الرسمي لـPUT مفيهوش حقل اسم/صورة/
تصنيف - بس sku/price/active/quantity/barcode - فمحتمل مايكفيش لإنشاء صنف
كامل بواجهة عرض سليمة.

بنجرب صنف واحد بس (فرع الروابي)، sku = الكود الداخلي بتاع فيرا، مش موجود
حاليًا في كتالوج هنجرستيشن (اتأكد من الفحص السابق) - عشان نشوف الرد بالظبط.
"""
import json
import os

import requests

BASE = "https://hungerstation.partner.deliveryhero.io"
CLIENT_ID = os.environ.get("VERA_HUNGERSTATION_CLIENT_ID", "veraCL-68b31204-81e5-4ea6-a1c0-086ab7e94267")
CHAIN_ID = os.environ.get("VERA_HS_CHAIN_ID", "68b31204-81e5-4ea6-a1c0-086ab7e94267")
VENDOR_ID = "149439"  # الروابي

TEST_ITEM = {
    "sku": "30064",  # Internal Reference من ماستر فيرا
    "barcode": "94015630070824",
    "price": 56.52,
    "active": True,
    "quantity": 1,
}


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

    # تأكيد إضافي إن الباركود مش موجود فعلاً قبل الاختبار
    r0 = requests.get(url, headers=headers_get, params={"page": 1, "page_size": 500, "query_term": TEST_ITEM["barcode"]}, timeout=30)
    print(f"\n=== تأكيد عدم الوجود مسبقًا (GET بالباركود) ===")
    print(f"status: {r0.status_code}, عدد النتائج: {len(r0.json().get('products', [])) if r0.status_code==200 else 'N/A'}")

    headers_put = {"authorization": f"Bearer {token}", "accept": "application/json", "content-type": "application/json"}
    payload = {"products": [TEST_ITEM]}
    print(f"\n=== PUT (إنشاء تجريبي) ===")
    print(f"payload: {json.dumps(payload, ensure_ascii=False)}")
    r = requests.put(url, json=payload, headers=headers_put, timeout=20)
    print(f"status: {r.status_code}")
    print(f"body: {r.text[:1500]}")

    # لو رجع 202 (job queued) لازم ننتظر شوية ونتأكد فعليًا ظهر الصنف كامل ولا لأ
    import time
    time.sleep(20)
    r2 = requests.get(url, headers=headers_get, params={"page": 1, "page_size": 500, "query_term": TEST_ITEM["sku"]}, timeout=30)
    print(f"\n=== التأكد بعد 20 ثانية (GET بالـsku) ===")
    print(f"status: {r2.status_code}")
    if r2.status_code == 200:
        products = r2.json().get("products", [])
        print(f"عدد النتائج: {len(products)}")
        for p in products:
            print(json.dumps(p, ensure_ascii=False, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
