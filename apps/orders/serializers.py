from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from apps.orders.models import Order
from apps.products.models import Product


class OrderSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    shop_name = serializers.CharField(source="shop.name", read_only=True)

    class Meta:
        model = Order
        fields = (
            "id",
            "product",
            "shop",
            "product_name",
            "shop_name",
            "buyer",
            "customer_name",
            "phone",
            "address",
            "status",
            "created_at",
        )
        read_only_fields = ("id", "product_name", "shop_name", "buyer", "created_at")


class OrderCreateSerializer(serializers.Serializer):
    product = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.filter(is_active=True).select_related("shop"),
    )
    customer_name = serializers.CharField(min_length=2, max_length=255, trim_whitespace=True)
    phone = serializers.CharField(max_length=32)
    address = serializers.CharField(min_length=5, max_length=2000, trim_whitespace=True)

    def validate_phone(self, value: str) -> str:
        v = value.strip()
        digits = "".join(c for c in v if c.isdigit())
        if len(digits) < 9:
            raise serializers.ValidationError(_("Enter a complete phone number."))
        return v

    def validate(self, attrs):
        product: Product = attrs["product"]
        shop = product.shop
        if not shop.is_active:
            raise serializers.ValidationError({"product": _("Shop is not available.")})
        if not shop.is_subscription_operational():
            raise serializers.ValidationError({"product": _("Shop is not available.")})
        return attrs
