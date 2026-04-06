from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from apps.orders.models import Order, OrderIdempotency


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "shop",
        "product",
        "customer_name",
        "phone",
        "status",
        "buyer",
        "created_at",
    )
    list_filter = ("status", "created_at")
    search_fields = ("customer_name", "phone", "shop__name", "product__name", "id")
    date_hierarchy = "created_at"
    raw_id_fields = ("product", "shop", "buyer")
    readonly_fields = ("created_at",)
    list_select_related = ("shop", "product", "buyer")


@admin.register(OrderIdempotency)
class OrderIdempotencyAdmin(admin.ModelAdmin):
    list_display = ("key", "order", "created_at")
    readonly_fields = ("key", "order", "created_at")
    search_fields = ("key",)
