from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from apps.products.models import Product


class ProductSerializer(serializers.ModelSerializer):
    shop_id = serializers.IntegerField(read_only=True)
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            "id",
            "shop_id",
            "name",
            "slug",
            "price",
            "image",
            "image_url",
            "description",
            "scarcity_text",
            "social_proof_text",
            "is_active",
            "sort_order",
            "created_at",
        )
        read_only_fields = ("id", "shop_id", "image_url", "created_at")
        extra_kwargs = {"slug": {"required": False}}

    def validate_slug(self, value: str | None) -> str | None:
        if value is None:
            return None
        v = str(value).strip()
        if not v:
            return ""
        from django.core.validators import validate_slug

        validate_slug(v)
        shop = self.context.get("shop")
        if shop is None and self.instance:
            shop = self.instance.shop
        if shop is not None:
            qs = Product.objects.filter(shop=shop, slug=v)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError(
                    _("Bu do‘konda bunday slug bilan mahsulot allaqachon mavjud.")
                )
        return v

    def get_image_url(self, obj: Product):
        request = self.context.get("request")
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return obj.image.url if obj.image else None


class ProductPublicSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    shop_name = serializers.CharField(source="shop.name", read_only=True)
    shop_verified = serializers.BooleanField(source="shop.is_verified", read_only=True)
    shop_payment_note = serializers.CharField(source="shop.payment_note", read_only=True)

    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "slug",
            "price",
            "image",
            "description",
            "created_at",
            "shop_name",
            "shop_verified",
            "shop_payment_note",
            "scarcity_text",
            "social_proof_text",
        )
        read_only_fields = (
            "id",
            "name",
            "slug",
            "price",
            "image",
            "description",
            "created_at",
            "shop_name",
            "shop_verified",
            "shop_payment_note",
            "scarcity_text",
            "social_proof_text",
        )

    def get_image(self, obj: Product):
        request = self.context.get("request")
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return obj.image.url if obj.image else None
