"""Telegram notifications for orders."""
from __future__ import annotations

from apps.core.telegram import send_message
from apps.orders.models import Order


def _divider() -> str:
    return "────────────"


def _order_status_uz(order: Order) -> str:
    m = {
        Order.Status.NEW: "Yangi",
        Order.Status.ACCEPTED: "Qabul qilindi",
        Order.Status.DELIVERED: "Yetkazildi",
        Order.Status.CANCELLED: "Bekor qilindi",
    }
    return m.get(order.status, order.status)


def notify_new_order(order: Order) -> None:
    """Sotuvchiga Telegram: yangi buyurtma (buyurtma yaratilganda, service layer)."""
    seller = order.shop.owner
    text = "\n".join(
        [
            "🛒 Yangi buyurtma!",
            f"Mijoz ismi: {order.customer_name}",
            f"Telefon: {order.phone}",
            f"Mahsulot: {order.product.name}",
        ]
    )
    send_message(seller.telegram_id, text)


def notify_order_confirmation(order: Order) -> None:
    if not order.buyer_id:
        return
    buyer_tid = order.buyer.telegram_id
    lines = [
        f"✅ Buyurtma #{order.pk} qabul qilindi.",
        _divider(),
        f"Mahsulot: {order.product.name}",
        "Tez orada siz bilan bog‘lanamiz.",
    ]
    send_message(buyer_tid, "\n".join(lines))


def notify_order_status(order: Order) -> None:
    if not order.buyer_id:
        return
    buyer_tid = order.buyer.telegram_id
    text = "\n".join(
        [
            "📦 Buyurtma yangilandi",
            _divider(),
            f"Buyurtma #{order.pk}",
            f"Holat: {_order_status_uz(order)}",
        ]
    )
    send_message(buyer_tid, text)


def notify_seller_buyer_cancelled_order(order: Order) -> None:
    """Mijoz buyurtmani bekor qilganda sotuvchiga."""
    seller = order.shop.owner
    lines = [
        f"❌ Buyurtma #{order.pk} mijoz tomonidan bekor qilindi.",
        _divider(),
        f"Do‘kon: {order.shop.name}",
        f"Mahsulot: {order.product.name}",
        f"Mijoz: {order.customer_name}",
        f"Telefon: {order.phone}",
    ]
    send_message(seller.telegram_id, "\n".join(lines))


def notify_buyer_cancel_confirmed(order: Order) -> None:
    if not order.buyer_id:
        return
    send_message(
        order.buyer.telegram_id,
        f"🚫 Buyurtma #{order.pk} bekor qilindi.",
    )
