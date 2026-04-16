import csv
import logging
import threading

from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.core.pagination import OrderListPagination
from apps.orders.locks import advisory_xact_lock_for_string
from apps.orders.models import Order, OrderIdempotency, OrderNote
from apps.orders.serializers import (
    OrderCreateSerializer,
    OrderNoteCreateSerializer,
    OrderNoteSerializer,
    OrderSerializer,
)
from apps.orders.services import (
    notify_buyer_cancel_confirmed,
    notify_new_order,
    notify_order_confirmation,
    notify_order_status,
    notify_seller_buyer_cancelled_order,
)
from apps.orders.state_machine import can_transition
from apps.orders.throttles import OrderCreateThrottle
from apps.products.models import Product
from apps.shops.models import Shop
from apps.shops.permissions import IsSellerOrAdmin
from apps.shops.selectors import get_owner_shop
from apps.users.models import User

logger = logging.getLogger(__name__)


def _seller_apply_status_change(request, order_id: int, new_status: str) -> Response:
    """Sotuvchi do‘koni: buyurtma holatini o‘zgartirish (PATCH va POST actionlar uchun)."""
    shop = get_owner_shop(request.user)
    if not shop:
        return Response({"detail": _("Create your shop first.")}, status=status.HTTP_404_NOT_FOUND)
    order = get_object_or_404(
        Order.objects.select_related("product", "shop", "buyer"),
        pk=order_id,
        shop=shop,
    )
    if not isinstance(new_status, str) or new_status not in dict(Order.Status.choices):
        return Response({"status": [_("Invalid status.")]}, status=status.HTTP_400_BAD_REQUEST)
    old = order.status
    if new_status == old:
        return Response(OrderSerializer(order, context={"request": request}).data)
    if not can_transition(old, new_status):
        return Response(
            {"status": [_("Invalid status transition.")]},
            status=status.HTTP_400_BAD_REQUEST,
        )
    order.status = new_status
    order.save(update_fields=["status"])
    if old != new_status and new_status != Order.Status.NEW:
        notify_order_status(order)
    return Response(OrderSerializer(order, context={"request": request}).data)


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
        logger.warning(
            "order_create validation_failed user_id=%s errors=%s",
            getattr(request.user, "pk", None),
            ser.errors,
        )
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
                existing_order = existing.order
                # Never leak another user's order by shared idempotency key.
                if existing_order.buyer_id != request.user.id:
                    logger.warning(
                        "order_create idempotency_conflict key=%s buyer=%s existing_buyer=%s",
                        idem_key[:32],
                        request.user.id,
                        existing_order.buyer_id,
                    )
                    return Response(
                        {"detail": _("Idempotency key conflict.")},
                        status=status.HTTP_409_CONFLICT,
                    )
                same_payload = (
                    existing_order.product_id == product.id
                    and existing_order.customer_name.strip() == ser.validated_data["customer_name"].strip()
                    and existing_order.phone.strip() == ser.validated_data["phone"].strip()
                    and existing_order.address.strip() == ser.validated_data["address"].strip()
                )
                if not same_payload:
                    logger.warning(
                        "order_create idempotency_payload_mismatch key=%s order_id=%s",
                        idem_key[:32],
                        existing_order.pk,
                    )
                    return Response(
                        {"detail": _("Idempotency key reused with different payload.")},
                        status=status.HTTP_409_CONFLICT,
                    )
                logger.info(
                    "order_create idempotent_replay order_id=%s buyer_id=%s",
                    existing_order.pk,
                    request.user.id,
                )
                return Response(
                    OrderSerializer(existing_order).data,
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
            total_amount=product.price,
        )
        Shop.objects.filter(pk=order.shop_id, first_order_completed_at__isnull=True).update(
            first_order_completed_at=timezone.now()
        )
        if idem_key:
            OrderIdempotency.objects.create(key=idem_key, order=order)

    order = Order.objects.select_related("product", "shop", "buyer").get(pk=order.pk)
    logger.info(
        "order_create ok order_id=%s shop_id=%s product_id=%s buyer_id=%s amount=%s",
        order.pk,
        order.shop_id,
        order.product_id,
        order.buyer_id,
        order.total_amount,
    )
    _schedule_order_notifications(order.pk)
    return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsSellerOrAdmin])
def seller_orders(request):
    shop = get_owner_shop(request.user)
    if not shop:
        return Response({"detail": _("Create your shop first.")}, status=status.HTTP_404_NOT_FOUND)
    qs = Order.objects.filter(shop=shop).select_related("product", "shop", "buyer").order_by("-created_at")
    st = (request.GET.get("status") or "").strip().upper()
    if st in dict(Order.Status.choices):
        qs = qs.filter(status=st)
    paginator = OrderListPagination()
    page = paginator.paginate_queryset(qs, request)
    ser = OrderSerializer(page, many=True)
    resp = paginator.get_paginated_response(ser.data)
    today = timezone.localdate()
    resp.data["stats"] = {
        "orders_today": Order.objects.filter(shop=shop, created_at__date=today).count(),
        "orders_total": Order.objects.filter(shop=shop).count(),
    }
    return resp


@api_view(["PATCH"])
@permission_classes([IsAuthenticated, IsSellerOrAdmin])
def seller_order_update(request, order_id):
    new_status = request.data.get("status")
    return _seller_apply_status_change(request, order_id, new_status)


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsSellerOrAdmin])
def seller_order_accept(request, order_id):
    return _seller_apply_status_change(request, order_id, Order.Status.ACCEPTED)


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsSellerOrAdmin])
def seller_order_deliver(request, order_id):
    return _seller_apply_status_change(request, order_id, Order.Status.DELIVERED)


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsSellerOrAdmin])
def seller_order_cancel_by_seller(request, order_id):
    return _seller_apply_status_change(request, order_id, Order.Status.CANCELLED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def buyer_order_cancel(request, order_id):
    order = get_object_or_404(
        Order.objects.select_related("product", "shop", "shop__owner", "buyer"),
        pk=order_id,
        buyer=request.user,
    )
    if order.status != Order.Status.NEW:
        return Response(
            {
                "detail": _(
                    "This order can no longer be cancelled in the app. "
                    "Please contact the seller using the phone number on the order."
                ),
                "code": "cancel_not_allowed",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
    order.status = Order.Status.CANCELLED
    order.save(update_fields=["status"])
    notify_seller_buyer_cancelled_order(order)
    notify_buyer_cancel_confirmed(order)
    order = Order.objects.select_related("product", "shop", "buyer").get(pk=order.pk)
    return Response(OrderSerializer(order, context={"request": request}).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def buyer_orders_mine(request):
    qs = (
        Order.objects.filter(buyer=request.user)
        .select_related("product", "shop")
        .order_by("-created_at")
    )
    paginator = OrderListPagination()
    page = paginator.paginate_queryset(qs, request)
    ser = OrderSerializer(page, many=True)
    return paginator.get_paginated_response(ser.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def buyer_order_detail(request, order_id):
    order = (
        Order.objects.filter(pk=order_id)
        .select_related("product", "shop", "buyer")
        .first()
    )
    if not order:
        return Response({"detail": _("Order not found.")}, status=status.HTTP_404_NOT_FOUND)
    if (
        order.buyer_id != request.user.id
        and request.user.role not in (User.Role.ADMIN, User.Role.PLATFORM_OWNER)
        and not request.user.is_superuser
    ):
        return Response({"detail": _("You do not have access.")}, status=status.HTTP_403_FORBIDDEN)
    return Response(OrderSerializer(order, context={"request": request}).data)


def _can_access_order_notes(user: User, order: Order) -> bool:
    if user.is_superuser or user.role in (User.Role.ADMIN, User.Role.PLATFORM_OWNER):
        return True
    if order.buyer_id and order.buyer_id == user.id:
        return True
    if order.shop.owner_id == user.id:
        return True
    return False


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def order_notes(request, order_id: int):
    order = (
        Order.objects.filter(pk=order_id)
        .select_related("shop", "shop__owner", "buyer")
        .first()
    )
    if not order:
        return Response({"detail": _("Order not found.")}, status=status.HTTP_404_NOT_FOUND)
    if not _can_access_order_notes(request.user, order):
        return Response({"detail": _("You do not have access.")}, status=status.HTTP_403_FORBIDDEN)
    if request.method == "GET":
        notes = order.notes.select_related("author").order_by("created_at")
        return Response({"results": OrderNoteSerializer(notes, many=True).data})
    ser = OrderNoteCreateSerializer(data=request.data)
    if not ser.is_valid():
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)
    note = OrderNote.objects.create(
        order=order,
        author=request.user,
        body=ser.validated_data["body"],
    )
    return Response(OrderNoteSerializer(note).data, status=status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsSellerOrAdmin])
def seller_orders_export_csv(request):
    shop = get_owner_shop(request.user)
    if not shop:
        return Response({"detail": _("Create your shop first.")}, status=status.HTTP_404_NOT_FOUND)
    qs = Order.objects.filter(shop=shop).select_related("product", "buyer").order_by("-created_at")
    st = (request.GET.get("status") or "").strip().upper()
    if st in dict(Order.Status.choices):
        qs = qs.filter(status=st)
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="orders_export.csv"'
    response.write("\ufeff")
    w = csv.writer(response)
    w.writerow(
        [
            "id",
            "status",
            "created_at",
            "product_name",
            "customer_name",
            "phone",
            "address",
            "total_amount",
            "buyer_telegram_id",
        ]
    )
    for o in qs.iterator(chunk_size=500):
        w.writerow(
            [
                o.id,
                o.status,
                o.created_at.isoformat() if o.created_at else "",
                o.product.name if o.product_id else "",
                o.customer_name,
                o.phone,
                (o.address or "").replace("\r\n", " ").replace("\n", " ")[:500],
                str(o.total_amount),
                o.buyer.telegram_id if o.buyer_id and o.buyer else "",
            ]
        )
    return response
