from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.db.models import Count
from django.utils.translation import gettext_lazy as _

from apps.users.models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ("-created_at",)
    list_display = (
        "telegram_id",
        "username",
        "first_name",
        "last_name",
        "role",
        "shop_count_display",
        "is_active",
        "is_staff",
        "created_at",
    )
    list_filter = ("role", "is_staff", "is_active")
    search_fields = ("telegram_id", "username", "first_name", "last_name")
    readonly_fields = ("created_at", "last_login")
    actions = (
        "activate_users",
        "deactivate_users",
        "set_role_buyer",
        "set_role_seller",
        "set_role_admin",
        "set_role_platform_owner",
    )

    fieldsets = (
        (None, {"fields": ("telegram_id", "password")}),
        (_("Personal info"), {"fields": ("first_name", "last_name", "username")}),
        (_("Permissions"), {"fields": ("role", "is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        (_("Important dates"), {"fields": ("last_login", "created_at")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("telegram_id", "role", "is_staff", "is_superuser"),
            },
        ),
    )

    @admin.display(description=_("Shops"), ordering="_shop_count")
    def shop_count_display(self, obj):
        return getattr(obj, "_shop_count", 0)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(_shop_count=Count("shops", distinct=True))

    @admin.action(description=_("Activate selected users"))
    def activate_users(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description=_("Deactivate selected users"))
    def deactivate_users(self, request, queryset):
        queryset.update(is_active=False)

    @admin.action(description=_("Set role: buyer"))
    def set_role_buyer(self, request, queryset):
        queryset.update(role=User.Role.BUYER)

    @admin.action(description=_("Set role: seller"))
    def set_role_seller(self, request, queryset):
        queryset.update(role=User.Role.SELLER)

    @admin.action(description=_("Set role: admin"))
    def set_role_admin(self, request, queryset):
        queryset.update(role=User.Role.ADMIN)

    @admin.action(description=_("Set role: platform owner"))
    def set_role_platform_owner(self, request, queryset):
        queryset.update(role=User.Role.PLATFORM_OWNER)
