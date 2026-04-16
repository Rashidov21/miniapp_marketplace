import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.image_utils import PRODUCT_MAX_SIDE, file_to_optimized_content
from apps.core.slug_utils import unique_product_slug

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
    slug = models.SlugField(
        max_length=120,
        db_index=True,
        help_text=_("URL va havolalarda (do‘kon ichida noyob)."),
    )
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
    sort_order = models.PositiveSmallIntegerField(
        default=0,
        help_text=_("Lower numbers appear first in the catalog (0 = default)."),
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["sort_order", "-created_at"]
        verbose_name = _("product")
        verbose_name_plural = _("products")
        constraints = [
            models.UniqueConstraint(fields=["shop", "slug"], name="products_product_shop_slug_uniq"),
        ]
        indexes = [
            models.Index(
                fields=["shop", "is_active", "sort_order", "-created_at"],
                name="products_pr_shop_act_sort_idx",
            ),
        ]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if self.shop_id and not (self.slug or "").strip():
            self.slug = unique_product_slug(self.shop_id, self.name, self.pk)
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
