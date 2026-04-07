import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.image_utils import PRODUCT_MAX_SIDE, file_to_optimized_content

try:
    from PIL import Image
except ImportError:  # pragma: no cover
    Image = None


class Product(models.Model):
    shop = models.ForeignKey(
        "shops.Shop",
        on_delete=models.CASCADE,
        related_name="products",
    )
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    image = models.ImageField(upload_to="products/%Y/%m/")
    description = models.TextField(blank=True)
    scarcity_text = models.CharField(
        max_length=120,
        blank=True,
        help_text=_("Optional urgency line, e.g. few items left."),
    )
    social_proof_text = models.CharField(
        max_length=120,
        blank=True,
        help_text=_("Optional social proof line for the product card."),
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("product")
        verbose_name_plural = _("products")
        indexes = [
            models.Index(fields=["shop", "is_active", "-created_at"]),
        ]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        update_fields = kwargs.get("update_fields")
        if self.image and Image and (update_fields is None or "image" in update_fields):
            try:
                cf, storage_name = file_to_optimized_content(
                    self.image,
                    basename=f"p_{uuid.uuid4().hex[:16]}",
                    max_side=PRODUCT_MAX_SIDE,
                )
                self.image.save(storage_name, cf, save=False)
            except OSError:
                pass
        super().save(*args, **kwargs)
