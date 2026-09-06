"""🔎 فحص آمن (قراءة فقط) لتوكن Partner API الخاص بفيرا (بعته كريم 6 سبتمبر 2026)
- نفس الآلية بالظبط اللي أكدناها مع دوم (DOOMAPI2)، بس على حساب فيرا.

client_id = veraCL-68b31204-81e5-4ea6-a1c0-086ab7e94267
=> chain_id (نفس نمط DOOMAPI2-{chain_id}) = 68b31204-81e5-4ea6-a1c0-086ab7e94267

vendor_id لسه مش معروف (كان عندنا لدوم 186329 من شاشة "معرف البائع" في
البوابة) - السكربت ده بيحاول يفك تشفير الـJWT للتوكن (بدون أي secret،
فك تشفير بس مش تحقق) لعله يحتوي على vendor_id أو chain claims مفيدة،
وبعدين يجرب GET على الكتالوج - لو رجع 404 لازم نجيب vendor_id من صاحب
حساب فيرا (نفس الشاشة اللي استخدمناها لدوم).
"""
import base64
import json
import os

import requests

TOKEN_URL = "https://hungerstation.partner.deliveryhero.io/v2/oauth/token"
CLIENT_ID = os.environ.get("VERA_HUNGERSTATION_CLIENT_ID", "veraCL-68b31204-81e5-4ea6-a1c0-086ab7e94267")
CHAIN_ID = os.environ.get("VERA_HS_CHAIN_ID", "68b31204-81e5-4ea6-a1c0-086ab7e94267")
VENDOR_ID = os.environ.get("VERA_HS_VENDOR_ID")  # لسه غير معروف


def get_token():
    client_secret = os.environ["VERA_HUNGERSTATION_CLIENT_SECRET"]
    r = requests.post(
        TOKEN_URL,
        data={"grant_type": "client_credentials", "client_id": CLIENT_ID, "client_secret": client_secret},
        headers={"content-type": "application/x-www-form-urlencoded", "accept": "application/json"},
        timeout=20,
    )
    print(f"status: {r.status_code}")
    if r.status_code != 200:
        print(f"body: {r.text[:1000]}")
        return None
    return r.json()


def decode_jwt_claims(token):
    try:
        payload_b64 = token.split(".")[1]
        payload_b64 += "=" * (-len(payload_b64) % 4)
        return json.loads(base64.urlsafe_b64decode(payload_b64))
    except Exception as e:
        return {"decode_error": str(e)}


def main():
    data = get_token()
    if not data:
        print("❌ فشل الحصول على access_token - راجع الأخطاء فوق (على الأغلب الـsecret اتلصق وفيه مسافة زيادة).")
        return 1

    access_token = data["access_token"]
    print(f"✅ access_token اتحصل عليه (طوله {len(access_token)}، expires_in={data.get('expires_in')})")

    claims = decode_jwt_claims(access_token)
    print("\n=== محتوى التوكن (JWT claims - قراءة بس، من غير أي تحقق) ===")
    print(json.dumps({k: v for k, v in claims.items() if k != "access_token"}, ensure_ascii=False, indent=2))

    if not VENDOR_ID:
        print("\n⚠️ VENDOR_ID لسه مش متوفر كـ secret - مستحيل نجرب قراءة الكتالوج من غيره.")
        print("لو الـclaims فوق فيها حاجة زي vendor_id/store_id/outlet_id، ابعتها لصاحب المشروع.")
        return 0

    catalog_url = f"https://hungerstation.partner.deliveryhero.io/v2/chains/{CHAIN_ID}/vendors/{VENDOR_ID}/catalog"
    print(f"\n=== GET {catalog_url} ===")
    r = requests.get(catalog_url, headers={"authorization": f"Bearer {access_token}", "accept": "application/json"},
                      params={"page_number": 1, "page_size": 20}, timeout=30)
    print(f"status: {r.status_code}")
    print(f"body: {r.text[:2000]}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
