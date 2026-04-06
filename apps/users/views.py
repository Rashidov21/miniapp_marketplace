from django.conf import settings
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.core.initdata import verify_init_data
from apps.users.authentication import upsert_user_from_telegram_user
from apps.users.models import User
from apps.users.serializers import UserSerializer


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
    if user.role == User.Role.ADMIN:
        return Response(UserSerializer(user).data)
    user.role = User.Role.SELLER
    user.save(update_fields=["role"])
    return Response(UserSerializer(user).data)
