from rest_framework import serializers

from apps.shops.models import Shop


class ShopSerializer(serializers.ModelSerializer):
    owner_id = serializers.IntegerField(source="owner_id", read_only=True)

    class Meta:
        model = Shop
        fields = (
            "id",
            "owner_id",
            "name",
            "is_active",
            "is_verified",
            "created_at",
        )
        read_only_fields = ("id", "owner_id", "is_verified", "created_at")


class ShopPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = ("id", "name", "is_active", "is_verified", "created_at")
        read_only_fields = fields
