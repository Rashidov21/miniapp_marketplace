from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from apps.shops import monetization
from apps.shops.models import Shop, SubscriptionPayment, SubscriptionPlan


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = (
            "id",
            "name",
            "duration_months",
            "price",
            "currency",
            "sort_order",
            "max_products",
            "includes_advanced_analytics",
        )
        read_only_fields = fields


class ShopSerializer(serializers.ModelSerializer):
    owner_id = serializers.IntegerField(read_only=True)
    logo = serializers.ImageField(required=False, allow_null=True)
    subscription_operational = serializers.SerializerMethodField()
    trial_days_left = serializers.SerializerMethodField()
    products_active_count = serializers.SerializerMethodField()
    max_products = serializers.SerializerMethodField()
    can_add_product = serializers.SerializerMethodField()
    plan_includes_analytics = serializers.SerializerMethodField()

    class Meta:
        model = Shop
        fields = (
            "id",
            "owner_id",
            "name",
            "slug",
            "description",
            "phone",
            "phone_secondary",
            "address",
            "social_telegram",
            "social_instagram",
            "social_facebook",
            "logo",
            "subscription_status",
            "trial_started_at",
            "trial_ends_at",
            "subscription_ends_at",
            "current_plan",
            "first_order_completed_at",
            "is_active",
            "is_verified",
            "created_at",
            "subscription_operational",
            "trial_days_left",
            "products_active_count",
            "max_products",
            "can_add_product",
            "plan_includes_analytics",
        )
        read_only_fields = (
            "id",
            "owner_id",
            "is_active",
            "is_verified",
            "created_at",
            "subscription_status",
            "trial_started_at",
            "trial_ends_at",
            "subscription_ends_at",
            "current_plan",
            "first_order_completed_at",
            "subscription_operational",
            "trial_days_left",
            "products_active_count",
            "max_products",
            "can_add_product",
            "plan_includes_analytics",
        )
        extra_kwargs = {
            "name": {"required": False},
            "slug": {"required": False},
            "description": {"required": False},
            "phone": {"required": False},
            "phone_secondary": {"required": False},
            "address": {"required": False},
            "social_telegram": {"required": False},
            "social_instagram": {"required": False},
            "social_facebook": {"required": False},
        }

    def get_subscription_operational(self, obj: Shop) -> bool:
        return obj.is_subscription_operational()

    def get_products_active_count(self, obj: Shop) -> int:
        return monetization.active_product_count(obj)

    def get_max_products(self, obj: Shop) -> int | None:
        return monetization.effective_max_products(obj)

    def get_can_add_product(self, obj: Shop) -> bool:
        ok, _ = monetization.can_add_product(obj)
        return ok

    def get_plan_includes_analytics(self, obj: Shop) -> bool:
        return monetization.plan_includes_analytics(obj)

    def validate_slug(self, value: str | None) -> str | None:
        if value is None:
            return None
        v = str(value).strip()
        if not v:
            raise serializers.ValidationError(_("This field may not be blank."))
        from django.core.validators import validate_slug

        validate_slug(v)
        qs = Shop.objects.filter(slug=v)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(_("A shop with this slug already exists."))
        return v

    def get_trial_days_left(self, obj: Shop) -> int | None:
        if obj.subscription_status != Shop.SubscriptionStatus.TRIAL or not obj.trial_ends_at:
            return None
        from django.utils import timezone

        delta = obj.trial_ends_at - timezone.now()
        if delta.total_seconds() <= 0:
            return 0
        return max(0, int(delta.total_seconds() // 86400))


class ShopPublicSerializer(serializers.ModelSerializer):
    logo = serializers.SerializerMethodField()

    class Meta:
        model = Shop
        fields = (
            "id",
            "name",
            "slug",
            "description",
            "phone",
            "phone_secondary",
            "address",
            "social_telegram",
            "social_instagram",
            "social_facebook",
            "logo",
            "is_verified",
            "created_at",
        )
        read_only_fields = fields

    def get_logo(self, obj: Shop) -> str | None:
        if not obj.logo:
            return None
        request = self.context.get("request")
        url = obj.logo.url
        if request:
            return request.build_absolute_uri(url)
        return url


class SubscriptionPaymentCreateSerializer(serializers.Serializer):
    plan_id = serializers.IntegerField()
    proof_image = serializers.ImageField()
    notes = serializers.CharField(required=False, allow_blank=True, default="")

    def validate_plan_id(self, value: int) -> int:
        if not SubscriptionPlan.objects.filter(pk=value, is_active=True).exists():
            raise serializers.ValidationError("Invalid plan.")
        return value
