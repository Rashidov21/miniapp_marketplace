from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.products.models import Product
from apps.products.serializers import ProductPublicSerializer, ProductSerializer
from apps.shops.models import Shop
from apps.shops.permissions import IsSellerOrAdmin, IsShopOwnerOrAdmin
from apps.users.models import User


@api_view(["GET"])
@permission_classes([AllowAny])
def product_list_public(request, shop_id):
    shop = Shop.objects.filter(pk=shop_id, is_active=True).first()
    if not shop or not shop.is_subscription_operational():
        return Response({"detail": _("Not found.")}, status=status.HTTP_404_NOT_FOUND)
    qs = Product.objects.filter(shop=shop, is_active=True)
    ser = ProductPublicSerializer(qs, many=True, context={"request": request})
    return Response({"results": ser.data})


@api_view(["GET"])
@permission_classes([AllowAny])
def product_detail_public(request, shop_id, product_id):
    shop = Shop.objects.filter(pk=shop_id, is_active=True).first()
    if not shop or not shop.is_subscription_operational():
        return Response({"detail": _("Not found.")}, status=status.HTTP_404_NOT_FOUND)
    p = get_object_or_404(Product, pk=product_id, shop=shop, is_active=True)
    return Response(ProductPublicSerializer(p, context={"request": request}).data)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated, IsSellerOrAdmin])
def product_list_manage(request):
    shop = Shop.objects.filter(owner=request.user).first()
    if not shop:
        return Response({"detail": _("No shop yet.")}, status=status.HTTP_404_NOT_FOUND)
    if request.method == "GET":
        qs = Product.objects.filter(shop=shop)
        ser = ProductSerializer(qs, many=True, context={"request": request})
        return Response({"results": ser.data})
    if not shop.is_subscription_operational():
        return Response(
            {"detail": _("Subscription required to add products.")},
            status=status.HTTP_403_FORBIDDEN,
        )
    ser = ProductSerializer(data=request.data, context={"request": request})
    if not ser.is_valid():
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)
    product = ser.save(shop=shop)
    return Response(ProductSerializer(product, context={"request": request}).data, status=status.HTTP_201_CREATED)


@api_view(["GET", "PATCH", "DELETE"])
@permission_classes([IsAuthenticated, IsSellerOrAdmin])
def product_detail_manage(request, product_id):
    shop = Shop.objects.filter(owner=request.user).first()
    if not shop:
        return Response({"detail": _("No shop yet.")}, status=status.HTTP_404_NOT_FOUND)
    product = Product.objects.filter(pk=product_id, shop=shop).first()
    if not product:
        return Response({"detail": _("Not found.")}, status=status.HTTP_404_NOT_FOUND)
    if not IsShopOwnerOrAdmin().has_object_permission(request, None, shop):
        return Response({"detail": _("Forbidden.")}, status=status.HTTP_403_FORBIDDEN)
    if request.method == "GET":
        return Response(ProductSerializer(product, context={"request": request}).data)
    if request.method == "DELETE":
        product.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    ser = ProductSerializer(
        product,
        data=request.data,
        partial=True,
        context={"request": request},
    )
    if not ser.is_valid():
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)
    ser.save()
    product.refresh_from_db()
    return Response(ProductSerializer(product, context={"request": request}).data)


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def product_admin_block(request, product_id):
    if request.user.role != User.Role.ADMIN and not request.user.is_superuser:
        return Response({"detail": _("Forbidden.")}, status=status.HTTP_403_FORBIDDEN)
    product = Product.objects.filter(pk=product_id).first()
    if not product:
        return Response({"detail": _("Not found.")}, status=status.HTTP_404_NOT_FOUND)
    if "is_active" in request.data:
        product.is_active = bool(request.data.get("is_active"))
        product.save(update_fields=["is_active"])
    return Response(ProductSerializer(product, context={"request": request}).data)
