from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from apps.shops.models import Shop


@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "is_active", "is_verified", "created_at")
    list_display_links = ("name",)
    list_filter = ("is_active", "is_verified")
    list_editable = ("is_active", "is_verified")
    search_fields = ("name", "owner__telegram_id", "owner__username")
    raw_id_fields = ("owner",)
    readonly_fields = ("created_at",)
