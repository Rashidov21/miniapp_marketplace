"""Seller / platform terms acceptance (versioned)."""
from __future__ import annotations

from django.conf import settings
from django.utils import timezone

from apps.users.models import User


def current_terms_version() -> str:
    return (getattr(settings, "CURRENT_SELLER_TERMS_VERSION", None) or "1").strip() or "1"


def user_has_current_seller_terms(user: User) -> bool:
    if not user or not user.is_authenticated:
        return False
    cv = current_terms_version()
    return bool(
        user.seller_terms_accepted_at
        and (user.seller_terms_version or "") == cv
    )


def record_seller_terms_acceptance(user: User) -> None:
    now = timezone.now()
    cv = current_terms_version()
    user.seller_terms_version = cv
    user.seller_terms_accepted_at = now
    user.save(update_fields=["seller_terms_version", "seller_terms_accepted_at"])
