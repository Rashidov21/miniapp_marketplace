import logging
import threading

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.core.pagination import OrderListPagination
from apps.orders.locks import advisory_xact_lock_for_string
from apps.orders.models import Order, OrderIdempotency
from apps.orders.serializers import OrderCreateSerializer, OrderSerializer
from apps.orders.services import notify_new_order, notify_order_confirmation, notify_order_status
from apps.orders.state_machine import can_transition
from apps.orders.throttles import OrderCreateThrottle
from apps.products.models import Product
from apps.shops.models import Shop
from apps.shops.permissions import IsSellerOrAdmin
from apps.users.models import User

logger = logging.getLogger(__name__)


def _schedule_order_notifications(order_id: int) -> None:
    def run() -> None:
        try:
            order = (
                Order.objects.select_related("product", "shop", "shop__owner", "buyer")
                .get(pk=order_id)
            )
            notify_new_order(order)
            notify_order_confirmation(order)
        except Exception:
            logger.exception("Order notification failed for order_id=%s", order_id)

    threading.Thread(target=run, daemon=True).start()


def _normalize_idempotency_key(raw: str | None) -> str | None:
    if not raw:
        return None
    key = raw.strip()[:128]
    return key or None


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([OrderCreateThrottle])
def order_create(request):
    ser = OrderCreateSerializer(data=request.data)
    if not ser.is_valid():
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)
    product: Product = ser.validated_data["product"]

    idem_raw = request.headers.get("Idempotency-Key") or request.headers.get("X-Idempotency-Key")
    idem_key = _normalize_idempotency_key(idem_raw)

    with transaction.atomic():
        if idem_key:
            advisory_xact_lock_for_string(idem_key)
            existing = (
                OrderIdempotency.objects.filter(key=idem_key)
                .select_related("order", "order__product", "order__shop", "order__buyer")
                .first()
            )
            if existing:
                return Response(
                    OrderSerializer(existing.order).data,
                    status=status.HTTP_200_OK,
                )

        order = Order.objects.create(
            product=product,
            shop=product.shop,
            buyer=request.user,
            customer_name=ser.validated_data["customer_name"].strip(),
            phone=ser.validated_data["phone"].strip(),
            address=ser.validated_data["address"].strip(),
            status=Order.Status.NEW,
        )
        if idem_key:
            OrderIdempotency.objects.create(key=idem_key, order=order)

    order = Order.objects.select_related("product", "shop", "buyer").get(pk=order.pk)
    _schedule_order_notifications(order.pk)
    return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsSellerOrAdmin])
def seller_orders(request):
    shop = Shop.objects.filter(owner=request.user).first()
    if not shop:
        return Response({"detail": _("No shop yet.")}, status=status.HTTP_404_NOT_FOUND)
    qs = Order.objects.filter(shop=shop).select_related("product", "shop", "buyer").order_by("-created_at")
    paginator = OrderListPagination()
    page = paginator.paginate_queryset(qs, request)
    ser = OrderSerializer(page, many=True)
    return paginator.get_paginated_response(ser.data)


@api_view(["PATCH"])
@permission_classes([IsAuthenticated, IsSellerOrAdmin])
def seller_order_update(request, order_id):
    shop = Shop.objects.filter(owner=request.user).first()
    if not shop:
        return Response({"detail": _("No shop yet.")}, status=status.HTTP_404_NOT_FOUND)
    order = get_object_or_404(
        Order.objects.select_related("product", "shop", "buyer"),
        pk=order_id,
        shop=shop,
    )
    new_status = request.data.get("status")
    if new_status not in dict(Order.Status.choices):
        return Response({"status": [_("Invalid status.")]}, status=status.HTTP_400_BAD_REQUEST)
    old = order.status
    if new_status == old:
        return Response(OrderSerializer(order).data)
    if not can_transition(old, new_status):
        return Response(
            {"status": [_("Invalid status transition.")]},
            status=status.HTTP_400_BAD_REQUEST,
        )
    order.status = new_status
    order.save(update_fields=["status"])
    if old != new_status and new_status != Order.Status.NEW:
        notify_order_status(order)
    return Response(OrderSerializer(order).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def buyer_order_detail(request, order_id):
    order = (
        Order.objects.filter(pk=order_id)
        .select_related("product", "shop", "buyer")
        .first()
    )
    if not order:
        return Response({"detail": _("Not found.")}, status=status.HTTP_404_NOT_FOUND)
    if order.buyer_id != request.user.id and request.user.role != User.Role.ADMIN and not request.user.is_superuser:
        return Response({"detail": _("Forbidden.")}, status=status.HTTP_403_FORBIDDEN)
    return Response(OrderSerializer(order).data)
