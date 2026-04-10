from django.contrib import admin
from django.contrib.admin import RelatedOnlyFieldListFilter
from django.utils.translation import gettext_lazy as _

from apps.orders.models import Order, OrderIdempotency
from apps.orders.state_machine import can_transition


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
    list_filter = (
        "status",
        "created_at",
        ("shop", RelatedOnlyFieldListFilter),
    )
    search_fields = ("customer_name", "phone", "shop__name", "product__name", "id")
    date_hierarchy = "created_at"
    raw_id_fields = ("product", "shop", "buyer")
    readonly_fields = ("created_at",)
    list_select_related = ("shop", "product", "buyer")
    actions = ("mark_accepted", "mark_delivered")

    @admin.action(description=_("Move to accepted (valid transitions only)"))
    def mark_accepted(self, request, queryset):
        for order in queryset:
            if can_transition(order.status, Order.Status.ACCEPTED):
                order.status = Order.Status.ACCEPTED
                order.save(update_fields=["status"])

    @admin.action(description=_("Move to delivered (valid transitions only)"))
    def mark_delivered(self, request, queryset):
        for order in queryset:
            if can_transition(order.status, Order.Status.DELIVERED):
                order.status = Order.Status.DELIVERED
                order.save(update_fields=["status"])


@admin.register(OrderIdempotency)
class OrderIdempotencyAdmin(admin.ModelAdmin):
    list_display = ("key", "order", "created_at")
    readonly_fields = ("key", "order", "created_at")
    search_fields = ("key",)
