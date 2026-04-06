from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class Shop(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="shops",
    )
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("shop")
        verbose_name_plural = _("shops")
        constraints = [
            models.UniqueConstraint(fields=["owner"], name="shops_shop_owner_uniq"),
        ]

    def __str__(self) -> str:
        return self.name
