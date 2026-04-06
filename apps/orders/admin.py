from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from apps.orders.models import Order


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "shop", "product", "customer_name", "phone", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("customer_name", "phone", "shop__name")
    raw_id_fields = ("product", "shop", "buyer")
    readonly_fields = ("created_at",)
