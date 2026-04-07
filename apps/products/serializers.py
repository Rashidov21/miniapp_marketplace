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
            "price",
            "image",
            "image_url",
            "description",
            "scarcity_text",
            "social_proof_text",
            "is_active",
            "created_at",
        )
        read_only_fields = ("id", "shop_id", "image_url", "created_at")

    def get_image_url(self, obj: Product):
        request = self.context.get("request")
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return obj.image.url if obj.image else None


class ProductPublicSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    shop_name = serializers.CharField(source="shop.name", read_only=True)
    shop_verified = serializers.BooleanField(source="shop.is_verified", read_only=True)

    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "price",
            "image",
            "description",
            "created_at",
            "shop_name",
            "shop_verified",
            "scarcity_text",
            "social_proof_text",
        )
        read_only_fields = (
            "id",
            "name",
            "price",
            "image",
            "description",
            "created_at",
            "shop_name",
            "shop_verified",
            "scarcity_text",
            "social_proof_text",
        )

    def get_image(self, obj: Product):
        request = self.context.get("request")
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return obj.image.url if obj.image else None
