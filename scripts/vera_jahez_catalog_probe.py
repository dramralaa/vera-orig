"""فحص أول (قراءة فقط) لكتالوج فيرا على جاهز/بيك (api.pik.sa) - عشان نتأكد من
Store ID الصحيح ونجيب حالة الكتالوج الحالية (نشط/غير نشط) لكل فرع.

الفروع المؤكدة من صفحة "الفروع" في Partner Portal (لقطة شاشة صاحب المشروع):
  - الروابي: رقم الفرع 4784
  - النرجس: رقم الفرع 7085

Store ID لسه مش مؤكد 100% - بنجرب مرشح واحد (2206، من بنية التوكن) ولو فشل
نطبع الخطأ عشان نطلب store id الصحيح من صاحب المشروع.
"""
import json
import os
import urllib.error
import urllib.request

API = "https://api.pik.sa"
HEADERS_BASE = {
    "accept": "application/json",
    "content-type": "application/json",
    "language": "ar",
    "origin": "https://portal-v2.pik.sa",
    "referer": "https://portal-v2.pik.sa/",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) juleb-jahez-sync",
    "x-requested-with": "XMLHttpRequest",
}

CANDIDATE_STORE_IDS = ["2206"]
BRANCH_IDS = {"الروابي": "4784", "النرجس": "7085"}


def req(method, url, token):
    headers = dict(HEADERS_BASE)
    headers["authorization"] = f"Bearer {token}"
    r = urllib.request.Request(url, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r, timeout=30) as resp:
            return resp.status, resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8")
    except Exception as e:
        return None, str(e)


def main():
    token = os.environ["JAHEZ_TOKEN_VERA"]

    print("=== محاولة 1: /portal/branches/minimal (بدون storeId) ===")
    status, body = req("GET", f"{API}/portal/branches/minimal", token)
    print(f"status={status}")
    print(body[:1500])

    for store_id in CANDIDATE_STORE_IDS:
        print(f"\n=== محاولة Store ID = {store_id} ===")
        status, body = req("GET", f"{API}/portal/stores/{store_id}/branches?page=1&pageCount=9999", token)
        print(f"GET /portal/stores/{store_id}/branches -> status={status}")
        print(body[:1500])

        status, body = req("GET", f"{API}/catalog/stores/{store_id}/products?page=1&pageCount=5", token)
        print(f"\nGET /catalog/stores/{store_id}/products -> status={status}")
        print(body[:2000])

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
