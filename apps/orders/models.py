from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class Order(models.Model):
    class Status(models.TextChoices):
        NEW = "NEW", _("New")
        ACCEPTED = "ACCEPTED", _("Accepted")
        DELIVERED = "DELIVERED", _("Delivered")

    product = models.ForeignKey(
        "products.Product",
        on_delete=models.CASCADE,
        related_name="orders",
    )
    shop = models.ForeignKey(
        "shops.Shop",
        on_delete=models.CASCADE,
        related_name="orders",
    )
    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
    )
    customer_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=32)
    address = models.TextField()
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.NEW,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("order")
        verbose_name_plural = _("orders")

    def __str__(self) -> str:
        return f"Order {self.pk} ({self.status})"


class OrderIdempotency(models.Model):
    """Maps client Idempotency-Key to created order (replay-safe POST /api/orders/)."""

    key = models.CharField(max_length=128, unique=True)
    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name="idempotency_record",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("order idempotency record")
        verbose_name_plural = _("order idempotency records")
