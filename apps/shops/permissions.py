from rest_framework.permissions import BasePermission

from apps.users.models import User


class IsSellerOrAdmin(BasePermission):
    def has_permission(self, request, view):
        u = request.user
        return bool(
            u
            and u.is_authenticated
            and (
                u.role in (User.Role.SELLER, User.Role.ADMIN, User.Role.PLATFORM_OWNER)
                or u.is_superuser
            )
        )


class IsShopOwnerOrAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        u = request.user
        if not u or not u.is_authenticated:
            return False
        if u.is_superuser or u.role in (User.Role.ADMIN, User.Role.PLATFORM_OWNER):
            return True
        return obj.owner_id == u.id
