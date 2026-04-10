from rest_framework import serializers

from apps.users.models import User
from apps.users.terms import current_terms_version, user_has_current_seller_terms


class UserSerializer(serializers.ModelSerializer):
    seller_terms_ok = serializers.SerializerMethodField()
    required_seller_terms_version = serializers.SerializerMethodField()

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
            "seller_terms_ok",
            "required_seller_terms_version",
        )
        read_only_fields = fields

    def get_seller_terms_ok(self, obj: User) -> bool:
        return user_has_current_seller_terms(obj)

    def get_required_seller_terms_version(self, obj: User) -> str:
        return current_terms_version()
