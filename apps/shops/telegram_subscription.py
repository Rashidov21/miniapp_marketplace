"""Obuna to‘lovi: Telegram Bot Payments (createInvoiceLink, pre_checkout_query, successful_payment)."""
from __future__ import annotations

import logging
import secrets
from decimal import ROUND_HALF_UP, Decimal

from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.core.telegram import answer_pre_checkout_query, telegram_bot_api_post_json
from apps.shops.models import Shop, SubscriptionPayment, SubscriptionPlan
from apps.shops.selectors import get_owner_shop
from apps.shops.services import approve_subscription_payment

logger = logging.getLogger(__name__)


def plan_amount_minor_units(amount: Decimal) -> int:
    """Telegram LabeledPrice.amount — UZS kichik birlik (env: TELEGRAM_UZS_MINOR_UNIT_MULTIPLIER, default 100)."""
    m = int(getattr(settings, "TELEGRAM_UZS_MINOR_UNIT_MULTIPLIER", 100) or 100)
    q = (Decimal(amount) * Decimal(m)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return int(q)


def create_telegram_subscription_invoice(*, user, plan_id: int) -> tuple[str | None, str | None, int | None]:
    """
    Pending SubscriptionPayment yaratadi, do‘konni payment_pending qiladi, createInvoiceLink URL qaytaradi.
    (None, error_detail, None) yoki (invoice_url, None, payment_id)
    """
    provider = (getattr(settings, "TELEGRAM_PAYMENT_PROVIDER_TOKEN", "") or "").strip()
    if not provider:
        return None, "telegram_provider_not_configured", None

    shop = get_owner_shop(user)
    if not shop:
        return None, "no_shop", None

    if SubscriptionPayment.objects.filter(
        shop=shop,
        status=SubscriptionPayment.Status.PENDING,
    ).exists():
        return None, "payment_pending_exists", None

    try:
        plan = SubscriptionPlan.objects.get(pk=plan_id, is_active=True)
    except SubscriptionPlan.DoesNotExist:
        return None, "plan_not_found", None

    amount_minor = plan_amount_minor_units(plan.price)
    if amount_minor <= 0:
        return None, "invalid_amount", None

    payload = secrets.token_urlsafe(32)[:96]
    if len(payload) > 128:
        payload = payload[:128]

    st_before = shop.subscription_status
    payment_pk: int | None = None
    try:
        with transaction.atomic():
            payment = SubscriptionPayment.objects.create(
                shop=shop,
                plan=plan,
                amount=plan.price,
                status=SubscriptionPayment.Status.PENDING,
                channel=SubscriptionPayment.Channel.TELEGRAM,
                invoice_payload=payload,
                proof_image=None,
                notes="",
            )
            payment_pk = payment.pk
            shop.subscription_status = Shop.SubscriptionStatus.PAYMENT_PENDING
            shop.save(update_fields=["subscription_status"])

        title = (plan.name or "Subscription")[:32]
        description = f"{shop.name} — {plan.name}"[:255]
        link = telegram_bot_api_post_json(
            "createInvoiceLink",
            {
                "title": title,
                "description": description,
                "payload": payload,
                "provider_token": provider,
                "currency": "UZS",
                "prices": [{"label": plan.name[:64] or "Plan", "amount": amount_minor}],
            },
        )
        if not link or not isinstance(link, str):
            raise RuntimeError("createInvoiceLink_failed")
        return link, None, payment.pk
    except IntegrityError as e:
        logger.warning("create_telegram_subscription_invoice integrity: %s", e)
        return None, "payment_pending_exists", None
    except (RuntimeError, Exception) as e:
        logger.warning("create_telegram_subscription_invoice rollback: %s", e)
        if payment_pk:
            SubscriptionPayment.objects.filter(pk=payment_pk).delete()
        else:
            SubscriptionPayment.objects.filter(
                shop=shop,
                invoice_payload=payload,
                channel=SubscriptionPayment.Channel.TELEGRAM,
                status=SubscriptionPayment.Status.PENDING,
            ).delete()
        shop.refresh_from_db()
        shop.subscription_status = st_before
        shop.save(update_fields=["subscription_status"])
        return None, "invoice_create_failed", None


def handle_pre_checkout_query(query: dict) -> None:
    """Telegram webhook: pre_checkout_query."""
    qid = query.get("id")
    if not qid:
        return
    from_user = query.get("from") or {}
    tg_uid = from_user.get("id")
    if tg_uid is None:
        answer_pre_checkout_query(str(qid), ok=False, error_message="Invalid user")
        return

    payload = (query.get("invoice_payload") or "").strip()
    currency = (query.get("currency") or "").upper()
    total_amount = query.get("total_amount")

    if currency != "UZS" or not isinstance(total_amount, int):
        answer_pre_checkout_query(str(qid), ok=False, error_message="Invalid currency")
        return

    payment = (
        SubscriptionPayment.objects.select_related("shop", "shop__owner", "plan")
        .filter(
            invoice_payload=payload,
            status=SubscriptionPayment.Status.PENDING,
            channel=SubscriptionPayment.Channel.TELEGRAM,
        )
        .first()
    )
    if not payment:
        answer_pre_checkout_query(str(qid), ok=False, error_message="Invoice expired")
        return

    shop = payment.shop
    owner = shop.owner
    if int(owner.telegram_id) != int(tg_uid):
        answer_pre_checkout_query(str(qid), ok=False, error_message="Not allowed")
        return

    expected_minor = plan_amount_minor_units(payment.plan.price)
    if int(total_amount) != expected_minor:
        logger.warning(
            "pre_checkout amount mismatch payment_id=%s expected=%s got=%s",
            payment.pk,
            expected_minor,
            total_amount,
        )
        answer_pre_checkout_query(str(qid), ok=False, error_message="Amount mismatch")
        return

    answer_pre_checkout_query(str(qid), ok=True)


def handle_successful_payment(message: dict) -> None:
    """Telegram webhook: message.successful_payment."""
    sp = message.get("successful_payment") or {}
    payload = (sp.get("invoice_payload") or "").strip()
    charge_id = (sp.get("telegram_payment_charge_id") or "").strip()
    provider_charge = (sp.get("provider_payment_charge_id") or "").strip()
    currency = (sp.get("currency") or "").upper()
    total_amount = sp.get("total_amount")

    if not payload or not charge_id or currency != "UZS" or not isinstance(total_amount, int):
        logger.warning("successful_payment missing fields: %s", sp)
        return

    if SubscriptionPayment.objects.filter(telegram_payment_charge_id=charge_id).exists():
        return

    with transaction.atomic():
        payment = (
            SubscriptionPayment.objects.select_for_update()
            .select_related("shop", "plan")
            .filter(
                invoice_payload=payload,
                status=SubscriptionPayment.Status.PENDING,
                channel=SubscriptionPayment.Channel.TELEGRAM,
            )
            .first()
        )
        if not payment:
            return
        minor = int(total_amount)
        if minor != plan_amount_minor_units(payment.plan.price):
            logger.error(
                "successful_payment amount mismatch payment_id=%s expected_minor=%s got=%s",
                payment.pk,
                plan_amount_minor_units(payment.plan.price),
                minor,
            )
            return

        payment.telegram_payment_charge_id = charge_id
        payment.telegram_provider_payment_charge_id = provider_charge[:256]
        payment.status = SubscriptionPayment.Status.APPROVED
        payment.reviewed_at = timezone.now()
        payment.save(
            update_fields=[
                "telegram_payment_charge_id",
                "telegram_provider_payment_charge_id",
                "status",
                "reviewed_at",
            ]
        )
        approve_subscription_payment(payment.shop, payment.plan)
