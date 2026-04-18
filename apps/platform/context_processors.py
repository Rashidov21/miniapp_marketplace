"""Platform paneli shablonlari uchun umumiy havolalar (PUBLIC_BASE_URL, bot)."""
from __future__ import annotations

from django.conf import settings


def platform_public_settings(request):
    """Faqat `/platform/` marshrutlarida — boshqa sahifalarga aralashmaydi."""
    path = (request.path or "").lower()
    if not path.startswith("/platform"):
        return {}
    base = (getattr(settings, "PUBLIC_BASE_URL", "") or "").rstrip("/")
    bot = (getattr(settings, "TELEGRAM_BOT_USERNAME", "") or "").strip().lstrip("@")
    return {
        "platform_public_base_url": base,
        "platform_bot_username": bot,
        "platform_support_email": (getattr(settings, "PLATFORM_SUPPORT_EMAIL", "") or "").strip(),
        "platform_has_public_url": bool(base),
    }
