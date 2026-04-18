from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from apps.orders.models import Order, OrderNote
from apps.products.models import Product


def phone_to_tel_href(phone: str) -> str:
    """tel: uchun raqam (mijoz telefoni)."""
    d = "".join(c for c in (phone or "") if c.isdigit())
    if len(d) < 9:
        return ""
    if d.startswith("998"):
        return "tel:+" + d
    if len(d) == 9:
        return "tel:+998" + d
    if d.startswith("0") and len(d) == 10:
        return "tel:+998" + d[1:]
    return "tel:+" + d


class OrderNoteSerializer(serializers.ModelSerializer):
    is_seller = serializers.SerializerMethodField()

    class Meta:
        model = OrderNote
        fields = ("id", "body", "created_at", "is_seller")
        read_only_fields = ("id", "body", "created_at", "is_seller")

    def get_is_seller(self, obj: OrderNote) -> bool:
        return obj.author_id == obj.order.shop.owner_id


class OrderNoteCreateSerializer(serializers.Serializer):
    body = serializers.CharField(min_length=1, max_length=2000, trim_whitespace=True)


class OrderSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    shop_name = serializers.CharField(source="shop.name", read_only=True)
    shop_slug = serializers.CharField(source="shop.slug", read_only=True)
    product_slug = serializers.CharField(source="product.slug", read_only=True)
    shop_payment_note = serializers.CharField(source="shop.payment_note", read_only=True)
    phone_tel = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = (
            "id",
            "product",
            "shop",
            "product_name",
            "shop_name",
            "shop_slug",
            "product_slug",
            "shop_payment_note",
            "buyer",
            "customer_name",
            "phone",
            "phone_tel",
            "address",
            "status",
            "total_amount",
            "created_at",
        )
        read_only_fields = (
            "id",
            "product_name",
            "shop_name",
            "shop_slug",
            "product_slug",
            "shop_payment_note",
            "buyer",
            "total_amount",
            "created_at",
            "phone_tel",
        )

    def get_phone_tel(self, obj: Order) -> str:
        return phone_to_tel_href(obj.phone)


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
            raise serializers.ValidationError(_("Telefon raqamini to‘liq kiriting."))
        return v

    def validate(self, attrs):
        product: Product = attrs["product"]
        shop = product.shop
        if not shop.is_active:
            raise serializers.ValidationError({"product": _("Do‘kon mavjud emas.")})
        if not shop.is_subscription_operational():
            raise serializers.ValidationError({"product": _("Do‘kon mavjud emas.")})
        return attrs
