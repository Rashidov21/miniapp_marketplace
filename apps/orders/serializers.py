from rest_framework import serializers

from apps.orders.models import Order


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


class OrderCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = (
            "product",
            "customer_name",
            "phone",
            "address",
        )

    def validate(self, attrs):
        product = attrs.get("product")
        if not product or not product.is_active:
            raise serializers.ValidationError({"product": "Invalid product."})
        attrs["shop"] = product.shop
        return attrs
