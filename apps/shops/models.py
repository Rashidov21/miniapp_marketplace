import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.image_utils import SHOP_LOGO_MAX_SIDE, file_to_optimized_content
from apps.core.slug_utils import unique_shop_slug

try:
    from PIL import Image
except ImportError:  # pragma: no cover
    Image = None


class SubscriptionPlan(models.Model):
    """Obuna tariflari: mahsulot limiti va analytics huquqi."""

    name = models.CharField(max_length=128)
    duration_months = models.PositiveSmallIntegerField()
    price = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=8, default="UZS")
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveSmallIntegerField(default=0)
    max_products = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text=_("Null — cheksiz mahsulot (Pro). Raqam — faol mahsulot limiti."),
    )
    includes_advanced_analytics = models.BooleanField(
        default=False,
        help_text=_("Haftalik analytics va keyingi bosqichdagi hisobotlar."),
    )

    class Meta:
        ordering = ["sort_order", "duration_months"]
        verbose_name = _("subscription plan")
        verbose_name_plural = _("subscription plans")

    def __str__(self) -> str:
        return f"{self.name} ({self.duration_months}m)"


class Shop(models.Model):
    class SubscriptionStatus(models.TextChoices):
        TRIAL = "trial", _("Trial")
        ACTIVE = "active", _("Active")
        EXPIRED = "expired", _("Expired")
        PAYMENT_PENDING = "payment_pending", _("Payment pending")
        SUSPENDED = "suspended", _("Suspended")

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="shops",
    )
    name = models.CharField(max_length=255)
    slug = models.SlugField(
        max_length=80,
        unique=True,
        db_index=True,
        help_text=_("URL va havolalarda ko‘rinadi (lotin harflar, raqam, tire)."),
    )
    description = models.TextField(blank=True)
    phone = models.CharField(max_length=32, blank=True)
    phone_secondary = models.CharField(max_length=32, blank=True)
    address = models.TextField(blank=True)
    social_telegram = models.URLField(blank=True)
    social_instagram = models.URLField(blank=True)
    social_facebook = models.URLField(blank=True)
    logo = models.ImageField(upload_to="shop_logos/", null=True, blank=True)

    subscription_status = models.CharField(
        max_length=32,
        choices=SubscriptionStatus.choices,
        default=SubscriptionStatus.ACTIVE,
    )
    trial_started_at = models.DateTimeField(null=True, blank=True)
    trial_ends_at = models.DateTimeField(null=True, blank=True)
    current_plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="shops",
    )
    subscription_ends_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_("Null means unlimited while status is active (legacy)."),
    )

    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    first_order_completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_("Birinchi muvaffaqiyatli buyurtma vaqti (upsell / CRO)."),
    )
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

    def save(self, *args, **kwargs):
        if not (self.slug or "").strip():
            self.slug = unique_shop_slug(self.name, self.pk)
        update_fields = kwargs.get("update_fields")
        if self.logo and Image and (update_fields is None or "logo" in update_fields):
            try:
                cf, storage_name = file_to_optimized_content(
                    self.logo,
                    basename=f"logo_{uuid.uuid4().hex[:12]}",
                    max_side=SHOP_LOGO_MAX_SIDE,
                )
                self.logo.save(storage_name, cf, save=False)
            except OSError:
                pass
        super().save(*args, **kwargs)

    def is_subscription_operational(self) -> bool:
        """Do‘kon mijozlarga ochiq (vitrina, buyurtma) bo‘lishi mumkinmi."""
        now = timezone.now()
        st = self.subscription_status
        if st == self.SubscriptionStatus.TRIAL:
            return self.trial_ends_at is not None and now < self.trial_ends_at
        if st == self.SubscriptionStatus.ACTIVE:
            if self.subscription_ends_at is None:
                return True
            return now < self.subscription_ends_at
        return False


class SubscriptionPayment(models.Model):
    """Skrinshot orqali yuborilgan obuna to‘lovi (admin tasdiqi)."""

    class Status(models.TextChoices):
        PENDING = "pending", _("Pending")
        APPROVED = "approved", _("Approved")
        REJECTED = "rejected", _("Rejected")

    shop = models.ForeignKey(
        Shop,
        on_delete=models.CASCADE,
        related_name="subscription_payments",
    )
    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.PROTECT,
        related_name="payments",
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
    )
    proof_image = models.ImageField(upload_to="subscription_payments/")
    notes = models.TextField(blank=True)
    admin_note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_subscription_payments",
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("subscription payment")
        verbose_name_plural = _("subscription payments")
        constraints = [
            models.UniqueConstraint(
                fields=["shop"],
                condition=models.Q(status="pending"),
                name="uniq_subscriptionpayment_pending_per_shop",
            ),
        ]

    def __str__(self) -> str:
        return f"Payment {self.pk} ({self.status})"
