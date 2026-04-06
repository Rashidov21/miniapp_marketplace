from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.shops.models import Shop
from apps.shops.permissions import IsSellerOrAdmin, IsShopOwnerOrAdmin
from apps.shops.serializers import ShopPublicSerializer, ShopSerializer
from apps.users.models import User


def _require_auth_user(request):
    if not request.user or not request.user.is_authenticated:
        return None
    return request.user


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsSellerOrAdmin])
def shop_create(request):
    user = _require_auth_user(request)
    name = (request.data or {}).get("name", "").strip()
    if not name:
        return Response({"name": [_("This field is required.")]}, status=status.HTTP_400_BAD_REQUEST)
    if Shop.objects.filter(owner=user).exists():
        return Response({"detail": _("You already have a shop.")}, status=status.HTTP_400_BAD_REQUEST)
    shop = Shop.objects.create(owner=user, name=name)
    return Response(ShopSerializer(shop).data, status=status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsSellerOrAdmin])
def shop_mine(request):
    user = _require_auth_user(request)
    shop = Shop.objects.filter(owner=user).first()
    if not shop:
        return Response({"detail": _("No shop yet.")}, status=status.HTTP_404_NOT_FOUND)
    return Response(ShopSerializer(shop).data)


@api_view(["PATCH"])
@permission_classes([IsAuthenticated, IsSellerOrAdmin, IsShopOwnerOrAdmin])
def shop_update(request, shop_id):
    shop = Shop.objects.filter(pk=shop_id).first()
    if not shop:
        return Response({"detail": _("Not found.")}, status=status.HTTP_404_NOT_FOUND)
    if not IsShopOwnerOrAdmin().has_object_permission(request, None, shop):
        return Response({"detail": _("Forbidden.")}, status=status.HTTP_403_FORBIDDEN)
    name = (request.data or {}).get("name")
    if name is not None:
        shop.name = str(name).strip() or shop.name
    if "is_active" in request.data and (request.user.is_superuser or request.user.role == User.Role.ADMIN):
        shop.is_active = bool(request.data.get("is_active"))
    shop.save()
    return Response(ShopSerializer(shop).data)


@api_view(["GET"])
@permission_classes([AllowAny])
def shop_public(request, shop_id):
    shop = Shop.objects.filter(pk=shop_id, is_active=True).first()
    if not shop:
        return Response({"detail": _("Not found.")}, status=status.HTTP_404_NOT_FOUND)
    return Response(ShopPublicSerializer(shop).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def shop_link(request, shop_id):
    shop = Shop.objects.filter(pk=shop_id).first()
    if not shop:
        return Response({"detail": _("Not found.")}, status=status.HTTP_404_NOT_FOUND)
    if shop.owner_id != request.user.id and request.user.role != User.Role.ADMIN and not request.user.is_superuser:
        return Response({"detail": _("Forbidden.")}, status=status.HTTP_403_FORBIDDEN)
    from django.conf import settings as dj_settings

    base = (getattr(dj_settings, "PUBLIC_BASE_URL", "") or "").rstrip("/")
    bot = getattr(dj_settings, "TELEGRAM_BOT_USERNAME", "") or ""
    path = f"/webapp/shop/{shop.id}/"
    full_url = f"{base}{path}" if base else path
    startapp = f"shop_{shop.id}"
    deep_link = f"https://t.me/{bot}?startapp={startapp}" if bot else ""
    return Response({"url": full_url, "startapp": startapp, "telegram_deep_link": deep_link})
