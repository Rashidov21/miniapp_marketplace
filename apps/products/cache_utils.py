import hashlib

from django.core.cache import cache


def product_public_cache_key(shop_id: int, product_id: int) -> str:
    return f"product:public:v1:{shop_id}:{product_id}"


def _product_list_version_key(shop_id: int) -> str:
    return f"product:list:ver:v1:{shop_id}"


def get_product_list_cache_version(shop_id: int) -> int:
    v = cache.get(_product_list_version_key(shop_id))
    try:
        return int(v) if v is not None else 0
    except (TypeError, ValueError):
        return 0


def bump_product_list_cache_version(shop_id: int) -> None:
    """Mahsulot ro‘yxati keshi (barcha sahifa/qidiruv) — versiya oshadi."""
    key = _product_list_version_key(shop_id)
    try:
        cache.incr(key)
    except ValueError:
        cache.set(key, 1, timeout=None)


def product_list_public_cache_key(shop_id: int, query: str, page: int, version: int) -> str:
    q = (query or "").strip()
    qh = hashlib.sha256(q.encode("utf-8")).hexdigest()[:12]
    return f"product:list:v1:{shop_id}:{version}:{qh}:{page}"
