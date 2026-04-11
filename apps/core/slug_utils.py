"""Unique URL slugs for shops and products."""
from __future__ import annotations

from django.utils.text import slugify


def unique_shop_slug(name: str, exclude_pk: int | None = None) -> str:
    from apps.shops.models import Shop

    base = slugify(name or "")[:60].strip("-") or "do-kon"
    slug = base
    n = 0
    qs = Shop.objects.all()
    if exclude_pk is not None:
        qs = qs.exclude(pk=exclude_pk)
    while qs.filter(slug=slug).exists():
        n += 1
        suffix = f"-{n}"
        slug = (base[: max(1, 60 - len(suffix))] + suffix).strip("-")
    return slug


def unique_product_slug(shop_id: int, name: str, exclude_pk: int | None = None) -> str:
    from apps.products.models import Product

    base = slugify(name or "")[:80].strip("-") or "mahsulot"
    slug = base
    n = 0
    qs = Product.objects.filter(shop_id=shop_id)
    if exclude_pk is not None:
        qs = qs.exclude(pk=exclude_pk)
    while qs.filter(slug=slug).exists():
        n += 1
        suffix = f"-{n}"
        slug = (base[: max(1, 80 - len(suffix))] + suffix).strip("-")
    return slug
