"""تقرير كامل لكتالوج فيرا على جاهز/بيك (api.pik.sa) - قراءة فقط.

نفس منطق سحب الكتالوج المستخدم في jahez_client.py لدوم (ريبو
juleb-daily-report) - منسوخ هنا بدل الاستيراد المباشر عشان ريبو فيرا يفضل
مستقل تمامًا (زي باقي سكربتات هنجرستيشن هنا).

Store ID فيرا مؤكَّد = 2206 (اتأكد فعليًا 7 سبتمبر 2026 - GET
/catalog/stores/2206/products رجع 200 وبيانات حقيقية فيها
"storeIntegrationId":"2206"). فروع فيرا (من صفحة "الفروع" في Partner
Portal): الروابي = 4784، النرجس = 7085.

الحالة (status) في رد جاهز: 2 = شغال/نشط (لاحظنا في أول عنصر رجع). لسه
مش مؤكَّد 100% باقي قيم status التانية معناها إيه - هنسجّلها زي ما هي.
"""
import json
import os
import time
import urllib.error
import urllib.request

API = "https://api.pik.sa"
STORE_ID = os.environ.get("VERA_JAHEZ_STORE_ID", "2206")
BRANCHES = {"4784": "الروابي", "7085": "النرجس"}

HEADERS_BASE = {
    "accept": "application/json",
    "content-type": "application/json",
    "language": "ar",
    "origin": "https://portal-v2.pik.sa",
    "referer": "https://portal-v2.pik.sa/",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) juleb-jahez-sync",
    "x-requested-with": "XMLHttpRequest",
}


class JahezError(Exception):
    pass


def _req(method, url, token, timeout=45):
    headers = dict(HEADERS_BASE)
    headers["authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            txt = r.read().decode("utf-8")
            return json.loads(txt) if txt.strip() else {}
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "ignore")[:400]
        raise JahezError(f"{method} {url} -> HTTP {e.code}: {detail}") from None
    except Exception as e:
        raise JahezError(f"{method} {url} -> {e}") from None


def _extract_list(j):
    if isinstance(j, list):
        return j
    if not isinstance(j, dict):
        return []
    for k in ("data", "items", "products", "results", "content", "list", "records", "rows"):
        v = j.get(k)
        if isinstance(v, list):
            return v
        if isinstance(v, dict):
            for kk in ("items", "data", "content"):
                if isinstance(v.get(kk), list):
                    return v[kk]
    for v in j.values():
        if isinstance(v, list):
            return v
    return []


def _total_pages(j, page_count):
    if not isinstance(j, dict):
        return None
    for key in ("totalPages", "total_pages", "pages"):
        if isinstance(j.get(key), int) and j[key] > 0:
            return j[key]
    for key in ("total", "totalCount", "count"):
        if isinstance(j.get(key), int) and j[key] > 0:
            return -(-j[key] // page_count)
    meta = j.get("meta") or {}
    for key in ("totalPages", "last_page", "total"):
        v = meta.get(key)
        if isinstance(v, int) and v > 0:
            return v if "page" in key.lower() else -(-v // page_count)
    return None


def fetch_all_products(token, store, page_count=100, sleep=0.3):
    page, out, total_pages, guard = 1, [], None, 0
    while guard < 1000:
        guard += 1
        j = _req("GET", f"{API}/catalog/stores/{store}/products?page={page}&pageCount={page_count}&search=", token)
        lst = _extract_list(j)
        if page == 1:
            total_pages = _total_pages(j, page_count)
            print(f"  صفحة 1: total_pages={total_pages}, عناصر الصفحة={len(lst)}")
        if not lst:
            break
        out.extend(lst)
        if total_pages and page >= total_pages:
            break
        if not total_pages and len(lst) < page_count:
            break
        page += 1
        time.sleep(sleep)
    return out


def main():
    token = os.environ["JAHEZ_TOKEN_VERA"]
    print(f"سحب كتالوج فيرا الكامل من جاهز (store={STORE_ID})...")
    products = fetch_all_products(token, STORE_ID)
    print(f"إجمالي المنتجات المسحوبة: {len(products)}")

    active = [p for p in products if p.get("status") == 2]
    hidden = [p for p in products if p.get("isHidden")]
    sold_out = [p for p in products if p.get("isSoldOut")]
    by_status = {}
    for p in products:
        by_status[p.get("status")] = by_status.get(p.get("status"), 0) + 1

    # توزيع حسب الفروع (hiddenBranches/soldOutBranches - قوائم IDs)
    per_branch_hidden = {b: 0 for b in BRANCHES}
    per_branch_soldout = {b: 0 for b in BRANCHES}
    for p in products:
        for bid in (p.get("hiddenBranches") or []):
            bid = str(bid)
            if bid in per_branch_hidden:
                per_branch_hidden[bid] += 1
        for bid in (p.get("soldOutBranches") or []):
            bid = str(bid)
            if bid in per_branch_soldout:
                per_branch_soldout[bid] += 1

    summary = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "store_id": STORE_ID,
        "total_products": len(products),
        "status_breakdown": by_status,
        "active_status2_count": len(active),
        "hidden_count": len(hidden),
        "sold_out_count": len(sold_out),
        "per_branch_hidden": {BRANCHES[b]: c for b, c in per_branch_hidden.items()},
        "per_branch_soldout": {BRANCHES[b]: c for b, c in per_branch_soldout.items()},
    }
    print("\n=== الخلاصة ===")
    print(json.dumps(summary, ensure_ascii=False, indent=2))

    os.makedirs("data", exist_ok=True)
    with open("data/vera_jahez_catalog_snapshot.json", "w", encoding="utf-8") as f:
        json.dump({**summary, "products": products}, f, ensure_ascii=False)
    print("\nSaved: data/vera_jahez_catalog_snapshot.json")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
