from __future__ import annotations

from django.contrib.auth import get_user_model

User = get_user_model()


def is_platform_staff(user) -> bool:
    """Django admin / platform panel: superuser yoki admin/platform_owner roli."""
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    role = getattr(user, "role", None)
    return role in (User.Role.ADMIN, User.Role.PLATFORM_OWNER)


def is_platform_superuser(user) -> bool:
    """Kuchli platform amallari (masalan, platform_owner holatini o‘zgartirish): superuser yoki admin/platform_owner."""
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    role = getattr(user, "role", None)
    return role in (User.Role.ADMIN, User.Role.PLATFORM_OWNER)
