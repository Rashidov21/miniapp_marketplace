import json
import logging

from django.core.cache import cache
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_GET, require_POST

from apps.core.models import Lead

from apps.products.models import Product
from apps.shops.models import Shop
from apps.users.terms import current_terms_version

logger = logging.getLogger(__name__)


def _client_ip(request):
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()[:45]
    return (request.META.get("REMOTE_ADDR") or "")[:45] or None


@require_GET
def landing_page(request):
    """SavdoLink marketing landing (conversion)."""
    from django.conf import settings

    return render(
        request,
        "landing/savdolink.html",
        {
            "telegram_bot_username": getattr(settings, "TELEGRAM_BOT_USERNAME", "") or "",
            "public_base_url": (getattr(settings, "PUBLIC_BASE_URL", "") or "").rstrip("/"),
        },
    )


@csrf_protect
@require_POST
def landing_lead_submit(request):
    """Modal/sticky lead form — JSON body, CSRF header."""
    ip = _client_ip(request) or ""
    rk = f"landing_lead:{ip or 'unknown'}"
    n = cache.get(rk, 0)
    if n >= 12:
        return JsonResponse({"ok": False, "detail": "too_many"}, status=429)
    try:
        data = json.loads(request.body.decode())
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"ok": False, "detail": "bad_json"}, status=400)
    name = (data.get("name") or "").strip()[:120]
    phone = (data.get("phone") or "").strip()[:40]
    comment = (data.get("comment") or "").strip()[:500]
    source = (data.get("source") or Lead.Source.LANDING_MODAL)[:32]
    if not name or not phone:
        return JsonResponse({"ok": False, "detail": "required"}, status=400)
    valid_sources = {c[0] for c in Lead.Source.choices}
    if source not in valid_sources:
        source = Lead.Source.LANDING_MODAL
    lead = Lead.objects.create(
        name=name,
        phone=phone,
        comment=comment,
        source=source,
        user_agent=(request.META.get("HTTP_USER_AGENT") or "")[:512],
        referrer=(request.META.get("HTTP_REFERER") or "")[:512],
        ip_address=ip,
    )
    cache.set(rk, n + 1, 3600)
    try:
        from apps.core.lead_services import notify_lead_admins

        notify_lead_admins(lead)
    except Exception:
        logger.exception("notify_lead_admins")
    return JsonResponse({"ok": True})


@require_GET
def webapp_home(request):
    return render(request, "webapp/home.html")


@require_GET
def discover_page(request):
    """Mijozlar: platformadagi ochiq do‘konlar ro‘yxati (API orqali to‘ldiriladi)."""
    return render(request, "webapp/discover.html")


@require_GET
def seller_dashboard(request):
    return render(request, "webapp/seller_dashboard.html")


@require_GET
def seller_products_list_page(request):
    return render(request, "webapp/seller_products.html")


@require_GET
def product_form(request, product_id=None):
    ctx = {"product_id": product_id}
    return render(request, "webapp/product_form.html", ctx)


def _shop_page_ctx(shop: Shop) -> dict:
    return {"shop_id": shop.id, "shop_slug": shop.slug}


@require_GET
def shop_legacy_redirect(request, shop_id):
    shop = get_object_or_404(Shop, pk=shop_id)
    return redirect("webapp_shop_slug", shop_slug=shop.slug, permanent=True)


def _render_catalog_unavailable(
    request,
    *,
    reason: str,
    shop_name: str = "",
    shop_slug: str = "",
):
    return render(
        request,
        "webapp/shop_unavailable.html",
        {
            "reason": reason,
            "shop_name": shop_name,
            "shop_slug": shop_slug,
        },
        status=200,
    )


@require_GET
def shop_page(request, shop_slug):
    shop = Shop.objects.filter(slug=shop_slug).first()
    if not shop:
        raise Http404()
    if not shop.is_active:
        return _render_catalog_unavailable(request, reason="inactive", shop_name=shop.name)
    if not shop.is_subscription_operational():
        return _render_catalog_unavailable(request, reason="subscription", shop_name=shop.name)
    return render(request, "webapp/shop.html", _shop_page_ctx(shop))


@require_GET
def product_legacy_redirect(request, shop_id, product_id):
    product = get_object_or_404(
        Product.objects.select_related("shop"),
        pk=product_id,
        shop_id=shop_id,
    )
    return redirect(
        "webapp_product_slug",
        shop_slug=product.shop.slug,
        product_slug=product.slug,
        permanent=True,
    )


@require_GET
def product_page(request, shop_slug, product_slug):
    shop = Shop.objects.filter(slug=shop_slug).first()
    if not shop:
        raise Http404()
    if not shop.is_active:
        return _render_catalog_unavailable(request, reason="inactive", shop_name=shop.name)
    if not shop.is_subscription_operational():
        return _render_catalog_unavailable(request, reason="subscription", shop_name=shop.name)
    product = Product.objects.select_related("shop").filter(slug=product_slug, shop=shop).first()
    if not product:
        raise Http404()
    if not product.is_active:
        return _render_catalog_unavailable(
            request,
            reason="product_inactive",
            shop_name=shop.name,
            shop_slug=shop.slug,
        )
    desc = (product.description or "").strip()
    og_desc = (desc[:200] if desc else "") or product.name
    og_image = ""
    if product.image:
        og_image = request.build_absolute_uri(product.image.url)
    return render(
        request,
        "webapp/product.html",
        {
            "shop_id": shop.id,
            "product_id": product.id,
            "shop_slug": shop.slug,
            "product_slug": product.slug,
            "og_title": product.name,
            "og_description": og_desc[:300],
            "og_image": og_image,
            "og_url": request.build_absolute_uri(request.get_full_path()),
        },
    )


@require_GET
def order_legacy_redirect(request, shop_id, product_id):
    product = get_object_or_404(
        Product.objects.select_related("shop"),
        pk=product_id,
        shop_id=shop_id,
    )
    return redirect(
        "webapp_order_slug",
        shop_slug=product.shop.slug,
        product_slug=product.slug,
        permanent=True,
    )


@require_GET
def order_page(request, shop_slug, product_slug):
    shop = Shop.objects.filter(slug=shop_slug).first()
    if not shop:
        raise Http404()
    if not shop.is_active:
        return _render_catalog_unavailable(request, reason="inactive", shop_name=shop.name)
    if not shop.is_subscription_operational():
        return _render_catalog_unavailable(request, reason="subscription", shop_name=shop.name)
    product = Product.objects.select_related("shop").filter(slug=product_slug, shop=shop).first()
    if not product:
        raise Http404()
    if not product.is_active:
        return _render_catalog_unavailable(
            request,
            reason="product_inactive",
            shop_name=shop.name,
            shop_slug=shop.slug,
        )
    return render(
        request,
        "webapp/order.html",
        {
            "shop_id": shop.id,
            "product_id": product.id,
            "shop_slug": shop.slug,
            "product_slug": product.slug,
            "shop_payment_note": (shop.payment_note or "").strip(),
        },
    )


@require_GET
def shop_settings_page(request):
    return render(request, "webapp/shop_settings.html")


@require_GET
def subscription_page(request):
    return render(request, "webapp/subscription.html")


@require_GET
def legal_terms(request):
    return render(
        request,
        "webapp/legal_terms.html",
        {"terms_version": current_terms_version()},
    )


@require_GET
def legal_privacy(request):
    return render(request, "webapp/legal_privacy.html", {})


@require_GET
def legal_seller_agreement(request):
    return render(
        request,
        "webapp/legal_seller_agreement.html",
        {"terms_version": current_terms_version()},
    )


@require_GET
def legal_content_policy(request):
    return render(request, "webapp/legal_content_policy.html", {})


@require_GET
def my_orders_page(request):
    return render(request, "webapp/my_orders.html")


@require_GET
def buyer_order_detail_page(request, order_id: int):
    return render(request, "webapp/buyer_order_detail.html", {"order_id": order_id})


def page_not_found(request, exception):
    """DEBUG=False paytida slug bo‘yicha 404 uchun do‘stona sahifa."""
    return render(request, "404.html", status=404)
