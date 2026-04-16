"""Shop subscription and visibility helpers."""
from __future__ import annotations

import logging
from datetime import timedelta

from django.utils import timezone

from apps.shops.models import Shop, SubscriptionPlan

logger = logging.getLogger(__name__)


def apply_trial_for_new_shop(shop: Shop) -> None:
    """Yangi do‘kon: 7 kunlik demo."""
    now = timezone.now()
    shop.subscription_status = Shop.SubscriptionStatus.TRIAL
    shop.trial_started_at = now
    shop.trial_ends_at = now + timedelta(days=7)
    shop.current_plan = None
    shop.subscription_ends_at = None
    shop.save(
        update_fields=[
            "subscription_status",
            "trial_started_at",
            "trial_ends_at",
            "current_plan",
            "subscription_ends_at",
        ]
    )


def approve_subscription_payment(shop: Shop, plan: SubscriptionPlan) -> None:
    """Admin tasdiqlagach: obuna muddati."""
    logger.info(
        "subscription_payment_approved shop_id=%s plan_id=%s plan_name=%s",
        shop.pk,
        plan.pk,
        plan.name,
    )
    now = timezone.now()
    shop.subscription_status = Shop.SubscriptionStatus.ACTIVE
    shop.current_plan = plan
    shop.subscription_ends_at = now + timedelta(days=30 * plan.duration_months)
    shop.trial_started_at = None
    shop.trial_ends_at = None
    shop.is_active = True
    shop.save(
        update_fields=[
            "subscription_status",
            "current_plan",
            "subscription_ends_at",
            "trial_started_at",
            "trial_ends_at",
            "is_active",
        ]
    )
