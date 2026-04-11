"""Tariflar va mahsulot limitlari (FREE / Standard / Pro)."""
from __future__ import annotations

from django.conf import settings
from apps.shops.models import Shop


def free_tier_max_products() -> int:
    return int(getattr(settings, "MONETIZATION_FREE_MAX_PRODUCTS", 5))


def upsell_min_views_week() -> int:
    return int(getattr(settings, "MONETIZATION_UPSELL_MIN_VIEWS_WEEK", 80))


def active_product_count(shop: Shop) -> int:
    from apps.products.models import Product

    return Product.objects.filter(shop=shop, is_active=True).count()


def plan_includes_analytics(shop: Shop) -> bool:
    """Kengaytirilgan analytics (Pro tarif)."""
    if not shop.is_subscription_operational():
        return False
    if shop.subscription_status == Shop.SubscriptionStatus.TRIAL:
        return False
    if shop.subscription_status == Shop.SubscriptionStatus.ACTIVE and shop.current_plan_id:
        return bool(shop.current_plan.includes_advanced_analytics)
    if shop.subscription_status == Shop.SubscriptionStatus.ACTIVE and not shop.current_plan_id:
        return True
    return False


def effective_max_products(shop: Shop) -> int | None:
    """
    None = cheksiz (Pro yoki legacy obuna).
    0 = obuna ishlamayapti — yangi mahsulot qo‘shib bo‘lmaydi.
    int > 0 = shu songacha faol mahsulot.
    """
    if not shop.is_subscription_operational():
        return 0
    if shop.subscription_status == Shop.SubscriptionStatus.TRIAL:
        return free_tier_max_products()
    if shop.subscription_status == Shop.SubscriptionStatus.ACTIVE:
        if shop.current_plan_id:
            p = shop.current_plan
            if p.max_products is None:
                return None
            return int(p.max_products)
        return None
    return 0


def can_add_product(shop: Shop) -> tuple[bool, str | None]:
    """Yangi (faol) mahsulot qo‘shish mumkinmi."""
    max_p = effective_max_products(shop)
    if max_p == 0:
        return False, "subscription_required"
    if max_p is None:
        return True, None
    if active_product_count(shop) >= max_p:
        return False, "product_limit_reached"
    return True, None


def can_activate_product(shop: Shop, *, current_active_count: int | None = None) -> tuple[bool, str | None]:
    """Nofaol mahsulotni yana faollashtirish mumkinmi."""
    max_p = effective_max_products(shop)
    if max_p == 0:
        return False, "subscription_required"
    if max_p is None:
        return True, None
    n = current_active_count if current_active_count is not None else active_product_count(shop)
    if n >= max_p:
        return False, "product_limit_reached"
    return True, None
