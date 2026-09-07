"""اختبار حقيقي (بإذن صاحب المشروع) لـ POST /v2/chains/{chain_id}/catalog -
endpoint "Add Products" الرسمي (BETA، يحتاج تفعيل كـ pilot partner من Account
Manager حسب التوثيق). الهدف: نتأكد فعليًا هل مفعّل لحسابنا ولا لأ، وإيه شكل
الرد بالظبط (501 لو مش مفعّل، أو 202+job_id لو مفعّل).

صنف اختباري وهمي واحد بس، active=false (مايظهرش للبيع)، SKU واضح إنه اختبار
عشان نقدر نحذفه/نتجاهله بسهولة لو ظهر فعلاً.
"""
import json
import os
import time

import requests

BASE = "https://hungerstation.partner.deliveryhero.io"
CLIENT_ID = os.environ.get("VERA_HUNGERSTATION_CLIENT_ID", "veraCL-68b31204-81e5-4ea6-a1c0-086ab7e94267")
CHAIN_ID = os.environ.get("VERA_HS_CHAIN_ID", "68b31204-81e5-4ea6-a1c0-086ab7e94267")
VENDOR_ID = "149439"  # الروابي

TEST_PAYLOAD = {
    "vendors": [VENDOR_ID],
    "products": [
        {
            "sku": "TEST-DO-NOT-SELL-0001",
            "title": {
                "ar_SA": "صنف اختباري - لا تبيع",
                "en_SA": "TEST ITEM - DO NOT SELL",
            },
            "barcodes": ["9999999999991"],
            "description": {
                "ar_SA": "اختبار تقني لتأكيد تفعيل POST /catalog",
                "en_SA": "Technical test to confirm POST /catalog is enabled",
            },
            "price": 1.00,
            "is_sold_by_weight": False,
        }
    ],
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

    url = f"{BASE}/v2/chains/{CHAIN_ID}/catalog"
    headers = {"authorization": f"Bearer {token}", "accept": "application/json", "content-type": "application/json"}

    print(f"\n=== POST {url} ===")
    print(f"payload: {json.dumps(TEST_PAYLOAD, ensure_ascii=False)}")
    r = requests.post(url, json=TEST_PAYLOAD, headers=headers, timeout=20)
    print(f"status: {r.status_code}")
    print(f"body: {r.text[:2000]}")

    if r.status_code not in (200, 201, 202):
        print("\n⛔ الـ endpoint مش شغال بالشكل المتوقع (غالبًا 501 = مش مفعّل كـ pilot partner، أو 404/403).")
        return 0

    job_id = None
    try:
        job_id = r.json().get("job_id")
    except Exception:
        pass

    if not job_id:
        print("\n⚠️ الرد اتقبل لكن مفيش job_id واضح في الرد - راجع الـ body فوق.")
        return 0

    print(f"\n✅ job_id: {job_id} - بنتابع الحالة...")
    job_url = f"{BASE}/v2/chains/{CHAIN_ID}/catalog/jobs/{job_id}"
    for attempt in range(6):
        time.sleep(15)
        jr = requests.get(job_url, headers=headers, timeout=20)
        print(f"\n=== GET job status (محاولة {attempt + 1}) ===")
        print(f"status: {jr.status_code}")
        print(f"body: {jr.text[:2000]}")
        if jr.status_code == 200:
            job_status = jr.json().get("job_status")
            if job_status in ("COMPLETED", "FAILED"):
                break

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
