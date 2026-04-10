import hmac

from django.conf import settings
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.core.drf_errors import error_response
from apps.core.initdata import verify_init_data
from apps.core.telegram import send_message_with_markup
from apps.users.authentication import upsert_user_from_telegram_user
from apps.users.models import User
from apps.users.serializers import UserSerializer
from apps.users.terms import record_seller_terms_acceptance, user_has_current_seller_terms


@api_view(["POST"])
@permission_classes([AllowAny])
def telegram_auth(request):
    """
    Body: { "init_data": "<raw initData string>" }
    Verifies hash, creates/updates user, starts Django session.
    """
    init_data = (request.data or {}).get("init_data") or request.data.get("initData")
    if not init_data:
        return Response({"detail": _("init_data is required")}, status=status.HTTP_400_BAD_REQUEST)
    token = getattr(settings, "TELEGRAM_BOT_TOKEN", "") or ""
    if not token:
        return Response(
            {"detail": _("Telegram bot is not configured")},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    payload = verify_init_data(init_data, token)
    if not payload:
        return Response({"detail": _("Invalid initData")}, status=status.HTTP_401_UNAUTHORIZED)
    user = upsert_user_from_telegram_user(payload["user"])
    return Response(
        {
            "user": UserSerializer(user).data,
            "start_param": payload.get("start_param") or "",
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request):
    return Response(UserSerializer(request.user).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def become_seller(request):
    """Promote current user to seller (MVP onboarding)."""
    user: User = request.user
    if user.role in {User.Role.ADMIN, User.Role.PLATFORM_OWNER} or user.is_superuser:
        return Response(UserSerializer(user).data)
    if not user_has_current_seller_terms(user):
        return error_response(
            str(_("Please accept the seller and marketplace terms first.")),
            status=status.HTTP_403_FORBIDDEN,
            code="terms_required",
        )
    user.role = User.Role.SELLER
    user.save(update_fields=["role"])
    return Response(UserSerializer(user).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def accept_seller_terms(request):
    """Record acceptance of the current seller/marketplace terms version."""
    record_seller_terms_acceptance(request.user)
    return Response(UserSerializer(request.user).data)


def _build_webapp_url(start_param: str) -> str:
    base = (getattr(settings, "PUBLIC_BASE_URL", "") or "").rstrip("/")
    if start_param.startswith("shop_"):
        sid = start_param.replace("shop_", "", 1)
        if sid.isdigit():
            return f"{base}/webapp/shop/{sid}/"
    if start_param.startswith("product_"):
        parts = start_param.split("_", 2)
        if len(parts) == 3 and parts[1].isdigit() and parts[2].isdigit():
            return f"{base}/webapp/shop/{parts[1]}/product/{parts[2]}/"
    return f"{base}/webapp/"


def _start_text() -> str:
    return (
        "Assalomu alaykum!\n\n"
        "Mini do'kon ilovasiga xush kelibsiz.\n"
        "Quyidagi tugma orqali WebApp'ni ochib, katalogni ko'ring yoki sotuvchi kabinetiga o'ting."
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def telegram_webhook(request, secret: str):
    cfg_secret = (getattr(settings, "TELEGRAM_WEBHOOK_SECRET", "") or "").strip()
    if not cfg_secret:
        return Response({"detail": "Webhook not configured."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    if not hmac.compare_digest(secret, cfg_secret):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

    update = request.data or {}
    message = update.get("message") or {}
    chat = message.get("chat") or {}
    text = (message.get("text") or "").strip()
    if not chat.get("id"):
        return Response({"ok": True})

    # Handle /start and /start <param>
    if text.startswith("/start"):
        parts = text.split(maxsplit=1)
        start_param = parts[1].strip() if len(parts) > 1 else ""
        webapp_url = _build_webapp_url(start_param)
        inline_markup = {
            "inline_keyboard": [
                [{"text": "Mini Appni ochish", "web_app": {"url": webapp_url}}],
                [{"text": "Sotuvchi kabineti", "web_app": {"url": f"{(getattr(settings, 'PUBLIC_BASE_URL', '') or '').rstrip('/')}/webapp/seller/"}}],
            ]
        }
        reply_markup = {
            "keyboard": [
                [{"text": "Mini Appni ochish", "web_app": {"url": webapp_url}}],
            ],
            "resize_keyboard": True,
            "is_persistent": True,
        }
        send_message_with_markup(chat["id"], _start_text(), reply_markup=inline_markup)
        send_message_with_markup(chat["id"], "Yoki pastdagi tugma bilan ham ochishingiz mumkin:", reply_markup=reply_markup)

    return Response({"ok": True})
