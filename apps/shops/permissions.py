from rest_framework.permissions import BasePermission

from apps.shops.models import Shop
from apps.users.models import User


class IsSellerOrAdmin(BasePermission):
    """
    Sotuvchi / admin — yoki do‘kon egasi (bazida role buyer qolgan edge case uchun).
    """

    def has_permission(self, request, view):
        u = request.user
        if not u or not u.is_authenticated:
            return False
        if u.is_superuser or u.role in (
            User.Role.SELLER,
            User.Role.ADMIN,
            User.Role.PLATFORM_OWNER,
        ):
            return True
        return Shop.objects.filter(owner_id=u.pk).exists()


class IsShopOwnerOrAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        u = request.user
        if not u or not u.is_authenticated:
            return False
        if u.is_superuser or u.role in (User.Role.ADMIN, User.Role.PLATFORM_OWNER):
            return True
        return obj.owner_id == u.id
