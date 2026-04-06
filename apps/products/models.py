from io import BytesIO

from django.core.files.base import ContentFile
from django.db import models
from django.utils.translation import gettext_lazy as _

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
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("product")
        verbose_name_plural = _("products")

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.pk and self.image and Image:
            self._optimize_image_once()

    def _optimize_image_once(self) -> None:
        if not self.image or not Image:
            return
        try:
            self.image.open()
            img = Image.open(self.image)
            img = img.convert("RGB")
            max_side = 1200
            w, h = img.size
            if max(w, h) > max_side:
                ratio = max_side / float(max(w, h))
                img = img.resize((int(w * ratio), int(h * ratio)), Image.Resampling.LANCZOS)
            buf = BytesIO()
            img.save(buf, format="JPEG", quality=82, optimize=True)
            name = self.image.name.rsplit("/", 1)[-1].rsplit(".", 1)[0] + ".jpg"
            self.image.save(name, ContentFile(buf.getvalue()), save=False)
            super().save(update_fields=["image"])
        except OSError:
            pass
