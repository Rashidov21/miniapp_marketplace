from django.contrib import admin
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.shops.models import Shop, SubscriptionPayment, SubscriptionPlan
from apps.shops.services import approve_subscription_payment


@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "owner",
        "subscription_status",
        "is_active",
        "is_verified",
        "created_at",
    )
    list_display_links = ("name",)
    list_filter = ("is_active", "is_verified", "subscription_status")
    search_fields = ("name", "phone", "owner__telegram_id", "owner__username", "owner__first_name", "owner__last_name")
    list_select_related = ("owner", "current_plan")
    date_hierarchy = "created_at"
    raw_id_fields = ("owner", "current_plan")
    readonly_fields = ("created_at",)
    fieldsets = (
        (None, {"fields": ("owner", "name", "description", "logo")}),
        (_("Contacts"), {"fields": ("phone", "phone_secondary", "address")}),
        (_("Social"), {"fields": ("social_telegram", "social_instagram", "social_facebook")}),
        (_("Subscription"), {"fields": ("subscription_status", "trial_started_at", "trial_ends_at", "current_plan", "subscription_ends_at")}),
        (_("Flags"), {"fields": ("is_active", "is_verified", "created_at")}),
    )


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ("name", "duration_months", "price", "currency", "is_active", "sort_order")
    list_editable = ("price", "is_active", "sort_order")


@admin.register(SubscriptionPayment)
class SubscriptionPaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "shop", "plan", "amount", "status", "created_at", "reviewed_at")
    list_filter = ("status",)
    raw_id_fields = ("shop", "plan", "reviewed_by")
    readonly_fields = ("created_at", "reviewed_at", "amount", "plan", "shop", "proof_image")
    actions = ("approve_payments", "reject_payments")

    @admin.action(description=_("Approve selected payments (activates subscription)"))
    def approve_payments(self, request, queryset):
        for payment in queryset.filter(status=SubscriptionPayment.Status.PENDING):
            approve_subscription_payment(payment.shop, payment.plan)
            payment.status = SubscriptionPayment.Status.APPROVED
            payment.reviewed_at = timezone.now()
            payment.reviewed_by = request.user
            payment.save(update_fields=["status", "reviewed_at", "reviewed_by"])

    @admin.action(description=_("Reject selected payments"))
    def reject_payments(self, request, queryset):
        for payment in queryset.filter(status=SubscriptionPayment.Status.PENDING):
            payment.status = SubscriptionPayment.Status.REJECTED
            payment.reviewed_at = timezone.now()
            payment.reviewed_by = request.user
            payment.save(update_fields=["status", "reviewed_at", "reviewed_by"])
            shop = payment.shop
            if shop.subscription_status == Shop.SubscriptionStatus.PAYMENT_PENDING:
                shop.subscription_status = Shop.SubscriptionStatus.EXPIRED
                shop.save(update_fields=["subscription_status"])
