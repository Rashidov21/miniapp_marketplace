from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET

from apps.products.models import Product
from apps.shops.models import Shop


@require_GET
def webapp_home(request):
    return render(request, "webapp/home.html")


@require_GET
def seller_dashboard(request):
    return render(request, "webapp/seller_dashboard.html")


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
    get_object_or_404(Shop, pk=shop_id)
    get_object_or_404(Product, pk=product_id, shop_id=shop_id)
    return render(request, "webapp/product.html", {"shop_id": shop_id, "product_id": product_id})


@require_GET
def order_page(request, shop_id, product_id):
    get_object_or_404(Shop, pk=shop_id)
    get_object_or_404(Product, pk=product_id, shop_id=shop_id)
    return render(request, "webapp/order.html", {"shop_id": shop_id, "product_id": product_id})


@require_GET
def shop_settings_page(request):
    return render(request, "webapp/shop_settings.html")


@require_GET
def subscription_page(request):
    return render(request, "webapp/subscription.html")
