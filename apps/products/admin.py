from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from apps.products.models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "shop", "price", "sort_order", "is_active", "created_at")
    list_display_links = ("name",)
    list_editable = ("sort_order",)
    list_filter = ("is_active", "created_at")
    search_fields = ("name", "slug", "shop__name", "scarcity_text", "social_proof_text")
    raw_id_fields = ("shop",)
    list_select_related = ("shop",)
    readonly_fields = ("created_at",)
    actions = ("activate_products", "deactivate_products")
    fieldsets = (
        (None, {"fields": ("shop", "name", "slug", "price", "image", "description")}),
        (_("Conversion (optional)"), {"fields": ("scarcity_text", "social_proof_text")}),
        (_("Catalog"), {"fields": ("sort_order",)}),
        (_("Flags"), {"fields": ("is_active", "created_at")}),
    )

    @admin.action(description=_("Activate selected products"))
    def activate_products(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description=_("Deactivate selected products"))
    def deactivate_products(self, request, queryset):
        queryset.update(is_active=False)
