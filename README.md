# vera-orig

ريبو مستقل خاص بصيدلية فيرا (منفصل تمامًا عن مشروع دوم) — أتمتة الربط مع منصات
التوصيل (هنجرستيشن، جاهز) الخاصة بفيرا فقط.

الأسرار المطلوبة (Settings → Secrets and variables → Actions):

- `VERA_HUNGERSTATION_CLIENT_ID`
- `VERA_HUNGERSTATION_CLIENT_SECRET`
- `VERA_HS_VENDOR_ID` (لسه غير معروف — يُضاف لاحقًا بعد الحصول عليه من بوابة هنجرستيشن)

## Workflows

- `Vera HungerStation Partner API Probe` — فحص قراءة فقط (Read-only) للتوكن
  والكتالوج، صفر كتابة.
