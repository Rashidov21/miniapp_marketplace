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

    class Meta:
        model = Product
        fields = ("id", "name", "price", "image", "description", "created_at")
        read_only_fields = fields

    def get_image(self, obj: Product):
        request = self.context.get("request")
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return obj.image.url if obj.image else None
