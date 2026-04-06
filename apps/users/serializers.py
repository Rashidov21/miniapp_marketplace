from rest_framework import serializers

from apps.users.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "telegram_id",
            "first_name",
            "last_name",
            "username",
            "role",
            "created_at",
        )
        read_only_fields = fields
