from __future__ import annotations

from django.contrib.auth import get_user_model

User = get_user_model()


def is_platform_staff(user) -> bool:
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return getattr(user, "role", None) == User.Role.PLATFORM_OWNER
