from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from apps.users.models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ("-created_at",)
    list_display = ("telegram_id", "username", "first_name", "last_name", "role", "is_staff", "created_at")
    list_filter = ("role", "is_staff", "is_active")
    search_fields = ("telegram_id", "username", "first_name", "last_name")
    readonly_fields = ("created_at", "last_login")

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
