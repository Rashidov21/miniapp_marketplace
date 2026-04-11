from datetime import timedelta

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
    search_fields = (
        "name",
        "slug",
        "phone",
        "owner__telegram_id",
        "owner__username",
        "owner__first_name",
        "owner__last_name",
    )
    list_select_related = ("owner", "current_plan")
    date_hierarchy = "created_at"
    raw_id_fields = ("owner", "current_plan")
    readonly_fields = ("created_at",)
    actions = (
        "verify_shops",
        "unverify_shops",
        "activate_shops",
        "deactivate_shops",
        "set_subscription_active",
        "extend_trial_7_days",
    )
    fieldsets = (
        (None, {"fields": ("owner", "name", "slug", "description", "logo")}),
        (_("Contacts"), {"fields": ("phone", "phone_secondary", "address")}),
        (_("Social"), {"fields": ("social_telegram", "social_instagram", "social_facebook")}),
        (_("Subscription"), {"fields": ("subscription_status", "trial_started_at", "trial_ends_at", "current_plan", "subscription_ends_at")}),
        (_("Flags"), {"fields": ("is_active", "is_verified", "created_at")}),
    )

    @admin.action(description=_("Verify selected shops"))
    def verify_shops(self, request, queryset):
        queryset.update(is_verified=True)

    @admin.action(description=_("Remove verification from selected shops"))
    def unverify_shops(self, request, queryset):
        queryset.update(is_verified=False)

    @admin.action(description=_("Activate selected shops (visible)"))
    def activate_shops(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description=_("Deactivate selected shops (hidden)"))
    def deactivate_shops(self, request, queryset):
        queryset.update(is_active=False)

    @admin.action(description=_("Set subscription status: active"))
    def set_subscription_active(self, request, queryset):
        queryset.update(subscription_status=Shop.SubscriptionStatus.ACTIVE)

    @admin.action(description=_("Extend trial end date by 7 days"))
    def extend_trial_7_days(self, request, queryset):
        now = timezone.now()
        for shop in queryset:
            if shop.trial_ends_at:
                shop.trial_ends_at = shop.trial_ends_at + timedelta(days=7)
            else:
                shop.trial_ends_at = now + timedelta(days=7)
            if shop.subscription_status != Shop.SubscriptionStatus.TRIAL:
                shop.subscription_status = Shop.SubscriptionStatus.TRIAL
            shop.save(update_fields=["trial_ends_at", "subscription_status"])


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "duration_months",
        "price",
        "currency",
        "max_products",
        "includes_advanced_analytics",
        "is_active",
        "sort_order",
    )
    list_editable = ("price", "is_active", "sort_order")
    list_filter = ("is_active", "includes_advanced_analytics")


@admin.register(SubscriptionPayment)
class SubscriptionPaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "shop", "plan", "amount", "status", "created_at", "reviewed_at")
    list_filter = ("status", "created_at")
    search_fields = ("shop__name", "shop__owner__telegram_id", "id")
    date_hierarchy = "created_at"
    raw_id_fields = ("shop", "plan", "reviewed_by")
    readonly_fields = ("created_at", "reviewed_at", "amount", "plan", "shop", "proof_image")
    list_select_related = ("shop", "plan", "reviewed_by")
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
