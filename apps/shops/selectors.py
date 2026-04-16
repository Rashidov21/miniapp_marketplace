"""Do‘kon tanlash (seller panel). API orqali bitta do‘kon yaratish mumkin — bir nechtasi bo‘lsa, eng kichik id."""

from __future__ import annotations

from apps.shops.models import Shop
from apps.users.models import User


def get_owner_shop(user: User) -> Shop | None:
    """Egasining do‘koni (birinchi yaratilgan). Admin orqali bir nechta bo‘lsa ham barqaror tanlov."""
    if not user or not user.is_authenticated:
        return None
    return Shop.objects.filter(owner_id=user.pk).order_by("pk").first()
