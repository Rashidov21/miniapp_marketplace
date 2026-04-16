"""Telegram notifications for orders."""
from __future__ import annotations

from django.utils.translation import gettext as _

from apps.core.telegram import send_message
from apps.orders.models import Order


def _divider() -> str:
    return "────────────"


def notify_new_order(order: Order) -> None:
    """Sotuvchiga Telegram: yangi buyurtma (buyurtma yaratilganda, service layer)."""
    seller = order.shop.owner
    text = "\n".join(
        [
            "🛒 Yangi buyurtma!",
            f"Ism: {order.customer_name}",
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
        "✅ " + str(_("Your order #{id} was received.")).format(id=order.pk),
        _divider(),
        _("Product: {name}").format(name=order.product.name),
        _("We will contact you soon."),
    ]
    send_message(buyer_tid, "\n".join(lines))


def notify_order_status(order: Order) -> None:
    if not order.buyer_id:
        return
    buyer_tid = order.buyer.telegram_id
    text = "\n".join(
        [
            "📦 " + str(_("Order update")),
            _divider(),
            _("Order #{id}").format(id=order.pk),
            _("Status: {status}").format(status=order.get_status_display()),
        ]
    )
    send_message(buyer_tid, text)


def notify_seller_buyer_cancelled_order(order: Order) -> None:
    """Mijoz buyurtmani bekor qilganda sotuvchiga."""
    seller = order.shop.owner
    lines = [
        "❌ " + str(_("Order #{id} cancelled by customer.")).format(id=order.pk),
        _divider(),
        _("Shop: {name}").format(name=order.shop.name),
        _("Product: {name}").format(name=order.product.name),
        _("Customer: {name}").format(name=order.customer_name),
        _("Phone: {phone}").format(phone=order.phone),
    ]
    send_message(seller.telegram_id, "\n".join(lines))


def notify_buyer_cancel_confirmed(order: Order) -> None:
    if not order.buyer_id:
        return
    send_message(
        order.buyer.telegram_id,
        "🚫 " + str(_("Order #{id} has been cancelled.")).format(id=order.pk),
    )
