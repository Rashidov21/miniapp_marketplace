from __future__ import annotations

from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.request import Request

from apps.core.initdata import verify_init_data
from apps.users.models import User


def upsert_user_from_telegram_user(tg_user: dict) -> User:
    tid = tg_user.get("id")
    if tid is None:
        raise AuthenticationFailed("Invalid Telegram user payload")
    tid_int = int(tid)
    defaults = {
        "first_name": tg_user.get("first_name") or "",
        "last_name": tg_user.get("last_name") or "",
        "username": tg_user.get("username") or "",
    }
    try:
        user = User.objects.get(telegram_id=tid_int)
    except User.DoesNotExist:
        return User.objects.create_user(telegram_id=tid_int, **defaults)

    changed_fields: list[str] = []
    for field, value in defaults.items():
        if getattr(user, field) != value:
            setattr(user, field, value)
            changed_fields.append(field)
    if changed_fields:
        user.save(update_fields=changed_fields)
    return user


class TelegramInitDataAuthentication(BaseAuthentication):
    """
    Send initData in header: X-Telegram-Init-Data (raw query string from Telegram.WebApp.initData).
    """

    header_name = "HTTP_X_TELEGRAM_INIT_DATA"

    def authenticate(self, request: Request):
        raw = request.META.get(self.header_name) or request.headers.get("X-Telegram-Init-Data")
        if not raw:
            return None
        token = getattr(settings, "TELEGRAM_BOT_TOKEN", "") or ""
        if not token:
            raise AuthenticationFailed("Server missing TELEGRAM_BOT_TOKEN")
        payload = verify_init_data(raw, token)
        if not payload:
            raise AuthenticationFailed("Invalid initData")
        user = upsert_user_from_telegram_user(payload["user"])
        return (user, None)
