from datetime import timedelta
from decimal import Decimal

from django.db import IntegrityError, transaction
from django.db.models import Sum
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.orders.models import Order
from apps.platform.models import AnalyticsEvent
from apps.products.models import Product
from apps.shops.models import Shop, SubscriptionPayment, SubscriptionPlan
from apps.shops.permissions import IsSellerOrAdmin, IsShopOwnerOrAdmin
from apps.shops.serializers import (
    ShopPublicSerializer,
    ShopSerializer,
    SubscriptionPaymentCreateSerializer,
    SubscriptionPlanSerializer,
)
from apps.core.drf_errors import error_response
from apps.shops import monetization
from apps.shops.services import apply_trial_for_new_shop
from apps.users.models import User
from apps.users.terms import user_has_current_seller_terms


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
    elevated = user.is_superuser or user.role in (User.Role.ADMIN, User.Role.PLATFORM_OWNER)
    if not elevated and not user_has_current_seller_terms(user):
        return error_response(
            str(_("Please accept the seller and marketplace terms before creating a shop.")),
            status=status.HTTP_403_FORBIDDEN,
            code="terms_required",
        )
    if Shop.objects.filter(owner=user).exists():
        return Response({"detail": _("You already have a shop.")}, status=status.HTTP_400_BAD_REQUEST)
    try:
        shop = Shop.objects.create(owner=user, name=name)
    except IntegrityError:
        return Response({"detail": _("You already have a shop.")}, status=status.HTTP_400_BAD_REQUEST)
    apply_trial_for_new_shop(shop)
    shop.refresh_from_db()
    return Response(
        ShopSerializer(shop, context={"request": request}).data,
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsSellerOrAdmin])
def seller_stats(request):
    shop = Shop.objects.filter(owner=request.user).first()
    if not shop:
        return Response({"detail": _("Create your shop first.")}, status=status.HTTP_404_NOT_FOUND)
    week_ago = timezone.now() - timedelta(days=7)
    shop_views_week = AnalyticsEvent.objects.filter(
        event_type=AnalyticsEvent.EventType.SHOP_VIEW,
        shop_id=shop.id,
        created_at__gte=week_ago,
    ).count()
    orders_week = Order.objects.filter(shop=shop, created_at__gte=week_ago).count()
    products_total = Product.objects.filter(shop=shop).count()
    rev = Order.objects.filter(shop=shop).aggregate(s=Sum("total_amount"))["s"]
    orders_total_amount = f"{Decimal(str(rev or 0)):.2f}"
    orders_total_count = Order.objects.filter(shop=shop).count()
    min_v = monetization.upsell_min_views_week()
    traffic_upsell = (
        shop_views_week >= min_v and not monetization.plan_includes_analytics(shop)
    )
    return Response(
        {
            "shop_views_week": shop_views_week,
            "orders_week": orders_week,
            "orders_total_count": orders_total_count,
            "orders_total_amount": orders_total_amount,
            "products_total": products_total,
            "plan_includes_analytics": monetization.plan_includes_analytics(shop),
            "traffic_upsell_suggested": traffic_upsell,
            "upsell_min_views_week": min_v,
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsSellerOrAdmin])
def shop_mine(request):
    user = _require_auth_user(request)
    shop = Shop.objects.filter(owner=user).first()
    if not shop:
        return Response({"detail": _("Create your shop first.")}, status=status.HTTP_404_NOT_FOUND)
    return Response(ShopSerializer(shop, context={"request": request}).data)


@api_view(["PATCH"])
@permission_classes([IsAuthenticated, IsSellerOrAdmin, IsShopOwnerOrAdmin])
def shop_update(request, shop_id):
    shop = Shop.objects.filter(pk=shop_id).first()
    if not shop:
        return Response({"detail": _("Shop not found.")}, status=status.HTTP_404_NOT_FOUND)
    if not IsShopOwnerOrAdmin().has_object_permission(request, None, shop):
        return Response({"detail": _("You do not have access.")}, status=status.HTTP_403_FORBIDDEN)
    data = request.data.copy()
    if not (
        request.user.is_superuser
        or request.user.role in (User.Role.ADMIN, User.Role.PLATFORM_OWNER)
    ):
        data.pop("is_active", None)
    ser = ShopSerializer(shop, data=data, partial=True, context={"request": request})
    if not ser.is_valid():
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)
    ser.save()
    shop.refresh_from_db()
    if request.user.is_superuser or request.user.role in (User.Role.ADMIN, User.Role.PLATFORM_OWNER):
        if "is_active" in request.data:
            shop.is_active = bool(request.data.get("is_active"))
            shop.save(update_fields=["is_active"])
    return Response(ShopSerializer(shop, context={"request": request}).data)


@api_view(["GET"])
@permission_classes([AllowAny])
def shop_public(request, shop_id):
    shop = Shop.objects.filter(pk=shop_id, is_active=True).first()
    if not shop or not shop.is_subscription_operational():
        return Response({"detail": _("Shop is unavailable.")}, status=status.HTTP_404_NOT_FOUND)
    return Response(ShopPublicSerializer(shop, context={"request": request}).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def shop_link(request, shop_id):
    shop = Shop.objects.filter(pk=shop_id).first()
    if not shop:
        return Response({"detail": _("Shop not found.")}, status=status.HTTP_404_NOT_FOUND)
    if (
        shop.owner_id != request.user.id
        and request.user.role not in (User.Role.ADMIN, User.Role.PLATFORM_OWNER)
        and not request.user.is_superuser
    ):
        return Response({"detail": _("You do not have access.")}, status=status.HTTP_403_FORBIDDEN)
    from django.conf import settings as dj_settings

    base = (getattr(dj_settings, "PUBLIC_BASE_URL", "") or "").rstrip("/")
    bot = getattr(dj_settings, "TELEGRAM_BOT_USERNAME", "") or ""
    path = f"/webapp/s/{shop.slug}/"
    full_url = f"{base}{path}" if base else path
    startapp = f"shop_{shop.id}"
    deep_link = f"https://t.me/{bot}?startapp={startapp}" if bot else ""
    return Response({"url": full_url, "startapp": startapp, "telegram_deep_link": deep_link})


@api_view(["GET"])
@permission_classes([AllowAny])
def shop_public_link(request, shop_id):
    shop = Shop.objects.filter(pk=shop_id, is_active=True).first()
    if not shop or not shop.is_subscription_operational():
        return Response({"detail": _("Shop is unavailable.")}, status=status.HTTP_404_NOT_FOUND)
    from django.conf import settings as dj_settings

    bot = getattr(dj_settings, "TELEGRAM_BOT_USERNAME", "") or ""
    base = (getattr(dj_settings, "PUBLIC_BASE_URL", "") or "").rstrip("/")
    startapp = f"shop_{shop.id}"
    path = f"/webapp/s/{shop.slug}/"
    full_url = f"{base}{path}" if base else path
    deep_link = f"https://t.me/{bot}?startapp={startapp}" if bot else ""
    return Response({"url": full_url, "startapp": startapp, "telegram_deep_link": deep_link})


@api_view(["GET"])
@permission_classes([AllowAny])
def subscription_plans_list(request):
    qs = SubscriptionPlan.objects.filter(is_active=True)
    return Response({"results": SubscriptionPlanSerializer(qs, many=True).data})


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsSellerOrAdmin])
def subscription_payment_create(request):
    shop = Shop.objects.filter(owner=request.user).first()
    if not shop:
        return Response({"detail": _("Create your shop first.")}, status=status.HTTP_404_NOT_FOUND)
    ser = SubscriptionPaymentCreateSerializer(data=request.data)
    if not ser.is_valid():
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)
    plan = SubscriptionPlan.objects.get(pk=ser.validated_data["plan_id"])
    if SubscriptionPayment.objects.filter(
        shop=shop,
        status=SubscriptionPayment.Status.PENDING,
    ).exists():
        return error_response(
            str(_("You already sent a payment. Please wait for review.")),
            status=status.HTTP_409_CONFLICT,
            code="payment_pending_exists",
        )
    try:
        with transaction.atomic():
            payment = SubscriptionPayment.objects.create(
                shop=shop,
                plan=plan,
                amount=plan.price,
                proof_image=ser.validated_data["proof_image"],
                notes=ser.validated_data.get("notes") or "",
            )
            shop.subscription_status = Shop.SubscriptionStatus.PAYMENT_PENDING
            shop.save(update_fields=["subscription_status"])
    except IntegrityError:
        return error_response(
            str(_("You already sent a payment. Please wait for review.")),
            status=status.HTTP_409_CONFLICT,
            code="payment_pending_exists",
        )
    return Response(
        {"id": payment.id, "status": payment.status, "amount": str(payment.amount)},
        status=status.HTTP_201_CREATED,
    )
