from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from apps.products.models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "shop", "price", "is_active", "created_at")
    list_filter = ("is_active", "created_at")
    search_fields = ("name", "shop__name")
    raw_id_fields = ("shop",)
    list_select_related = ("shop",)
    readonly_fields = ("created_at",)
