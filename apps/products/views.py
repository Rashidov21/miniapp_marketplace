from django.core.cache import cache
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.core.pagination import ProductListPagination
from apps.products.cache_utils import (
    get_product_list_cache_version,
    product_list_public_cache_key,
    product_public_cache_key,
)
from apps.core.drf_errors import error_response
from apps.products.models import Product
from apps.products.serializers import ProductPublicSerializer, ProductSerializer
from apps.shops import monetization
from apps.shops.models import Shop
from apps.shops.permissions import IsSellerOrAdmin, IsShopOwnerOrAdmin
from apps.users.models import User


@api_view(["GET"])
@permission_classes([AllowAny])
def product_list_public(request, shop_id):
    shop = Shop.objects.filter(pk=shop_id, is_active=True).first()
    if not shop or not shop.is_subscription_operational():
        return Response({"detail": _("Shop is unavailable.")}, status=status.HTTP_404_NOT_FOUND)
    qs = (
        Product.objects.filter(shop=shop, is_active=True)
        .select_related("shop")
        .order_by("sort_order", "-created_at")
    )
    q = (request.GET.get("q") or "").strip()
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(description__icontains=q))
    paginator = ProductListPagination()
    page = paginator.paginate_queryset(qs, request)
    page_num = paginator.page.number
    ver = get_product_list_cache_version(shop_id)
    list_ck = product_list_public_cache_key(shop_id, q, page_num, ver)
    cached_list = cache.get(list_ck)
    if cached_list is not None:
        return Response(cached_list)
    ser = ProductPublicSerializer(page, many=True, context={"request": request})
    resp = paginator.get_paginated_response(ser.data)
    cache.set(list_ck, resp.data, 90)
    return resp


@api_view(["GET"])
@permission_classes([AllowAny])
def product_detail_public(request, shop_id, product_id):
    shop = Shop.objects.filter(pk=shop_id, is_active=True).first()
    if not shop or not shop.is_subscription_operational():
        return Response({"detail": _("Shop is unavailable.")}, status=status.HTTP_404_NOT_FOUND)
    cache_key = product_public_cache_key(shop_id, product_id)
    cached = cache.get(cache_key)
    if cached is not None:
        return Response(cached)
    p = get_object_or_404(
        Product.objects.select_related("shop"),
        pk=product_id,
        shop=shop,
        is_active=True,
    )
    data = ProductPublicSerializer(p, context={"request": request}).data
    cache.set(cache_key, data, 90)
    return Response(data)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated, IsSellerOrAdmin])
def product_list_manage(request):
    shop = Shop.objects.filter(owner=request.user).first()
    if not shop:
        return Response({"detail": _("Create your shop first.")}, status=status.HTTP_404_NOT_FOUND)
    if request.method == "GET":
        qs = Product.objects.filter(shop=shop).select_related("shop").order_by("sort_order", "-created_at")
        paginator = ProductListPagination()
        page = paginator.paginate_queryset(qs, request)
        ser = ProductSerializer(page, many=True, context={"request": request})
        return paginator.get_paginated_response(ser.data)
    if not shop.is_subscription_operational():
        return Response(
            {"detail": _("To add products, activate your subscription.")},
            status=status.HTTP_403_FORBIDDEN,
        )
    ok, lim_code = monetization.can_add_product(shop)
    if not ok:
        return error_response(
            _("Active product limit reached. Upgrade your subscription."),
            status=status.HTTP_409_CONFLICT,
            code=lim_code or "product_limit_reached",
            extra={
                "products_active_count": monetization.active_product_count(shop),
                "max_products": monetization.effective_max_products(shop),
            },
        )
    ser = ProductSerializer(data=request.data, context={"request": request, "shop": shop})
    if not ser.is_valid():
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)
    product = ser.save(shop=shop)
    return Response(ProductSerializer(product, context={"request": request}).data, status=status.HTTP_201_CREATED)


@api_view(["GET", "PATCH", "DELETE"])
@permission_classes([IsAuthenticated, IsSellerOrAdmin])
def product_detail_manage(request, product_id):
    shop = Shop.objects.filter(owner=request.user).first()
    if not shop:
        return Response({"detail": _("Create your shop first.")}, status=status.HTTP_404_NOT_FOUND)
    product = (
        Product.objects.filter(pk=product_id, shop=shop)
        .select_related("shop")
        .first()
    )
    if not product:
        return Response({"detail": _("Product not found.")}, status=status.HTTP_404_NOT_FOUND)
    if not IsShopOwnerOrAdmin().has_object_permission(request, None, shop):
        return Response({"detail": _("You do not have access.")}, status=status.HTTP_403_FORBIDDEN)
    if request.method == "GET":
        return Response(ProductSerializer(product, context={"request": request}).data)
    if request.method == "DELETE":
        product.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    ser = ProductSerializer(
        product,
        data=request.data,
        partial=True,
        context={"request": request, "shop": shop},
    )
    if not ser.is_valid():
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)
    wants_active = ser.validated_data.get("is_active")
    if wants_active is True and not product.is_active:
        ok, lim_code = monetization.can_activate_product(shop)
        if not ok:
            return error_response(
                _("Active product limit reached. Deactivate another product or upgrade."),
                status=status.HTTP_409_CONFLICT,
                code=lim_code or "product_limit_reached",
                extra={
                    "products_active_count": monetization.active_product_count(shop),
                    "max_products": monetization.effective_max_products(shop),
                },
            )
    ser.save()
    product.refresh_from_db()
    return Response(ProductSerializer(product, context={"request": request}).data)


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def product_admin_block(request, product_id):
    if (
        request.user.role not in (User.Role.ADMIN, User.Role.PLATFORM_OWNER)
        and not request.user.is_superuser
    ):
        return Response({"detail": _("You do not have access.")}, status=status.HTTP_403_FORBIDDEN)
    product = Product.objects.filter(pk=product_id).select_related("shop").first()
    if not product:
        return Response({"detail": _("Product not found.")}, status=status.HTTP_404_NOT_FOUND)
    if "is_active" in request.data:
        product.is_active = bool(request.data.get("is_active"))
        product.save(update_fields=["is_active"])
    return Response(ProductSerializer(product, context={"request": request}).data)


@api_view(["GET"])
@permission_classes([AllowAny])
def product_public_link(request, shop_id, product_id):
    shop = Shop.objects.filter(pk=shop_id, is_active=True).first()
    if not shop or not shop.is_subscription_operational():
        return Response({"detail": _("Shop is unavailable.")}, status=status.HTTP_404_NOT_FOUND)
    product = Product.objects.filter(pk=product_id, shop=shop, is_active=True).first()
    if not product:
        return Response({"detail": _("Product not found.")}, status=status.HTTP_404_NOT_FOUND)
    from django.conf import settings as dj_settings

    bot = getattr(dj_settings, "TELEGRAM_BOT_USERNAME", "") or ""
    base = (getattr(dj_settings, "PUBLIC_BASE_URL", "") or "").rstrip("/")
    startapp = f"product_{shop.id}_{product.id}"
    path = f"/webapp/s/{shop.slug}/p/{product.slug}/"
    full_url = f"{base}{path}" if base else path
    deep_link = f"https://t.me/{bot}?startapp={startapp}" if bot else ""
    return Response({"url": full_url, "startapp": startapp, "telegram_deep_link": deep_link})
