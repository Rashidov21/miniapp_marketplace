from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET

from apps.products.models import Product
from apps.shops.models import Shop
from apps.users.terms import current_terms_version


@require_GET
def webapp_home(request):
    return render(request, "webapp/home.html")


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


@require_GET
def shop_page(request, shop_id):
    get_object_or_404(Shop, pk=shop_id)
    return render(request, "webapp/shop.html", {"shop_id": shop_id})


@require_GET
def product_page(request, shop_id, product_id):
    product = get_object_or_404(
        Product.objects.select_related("shop"),
        pk=product_id,
        shop_id=shop_id,
    )
    shop = product.shop
    if (
        not shop.is_active
        or not product.is_active
        or not shop.is_subscription_operational()
    ):
        raise Http404()
    desc = (product.description or "").strip()
    og_desc = (desc[:200] if desc else "") or product.name
    og_image = ""
    if product.image:
        og_image = request.build_absolute_uri(product.image.url)
    return render(
        request,
        "webapp/product.html",
        {
            "shop_id": shop_id,
            "product_id": product_id,
            "og_title": product.name,
            "og_description": og_desc[:300],
            "og_image": og_image,
            "og_url": request.build_absolute_uri(request.get_full_path()),
        },
    )


@require_GET
def order_page(request, shop_id, product_id):
    product = get_object_or_404(
        Product.objects.select_related("shop"),
        pk=product_id,
        shop_id=shop_id,
    )
    shop = product.shop
    if (
        not shop.is_active
        or not product.is_active
        or not shop.is_subscription_operational()
    ):
        raise Http404()
    return render(request, "webapp/order.html", {"shop_id": shop_id, "product_id": product_id})


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
