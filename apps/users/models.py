from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    def create_user(self, telegram_id, **extra_fields):
        if not telegram_id:
            raise ValueError("telegram_id is required")
        user = self.model(telegram_id=telegram_id, **extra_fields)
        user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, telegram_id, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", User.Role.ADMIN)
        return self.create_user(telegram_id, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        BUYER = "buyer", _("Buyer")
        SELLER = "seller", _("Seller")
        ADMIN = "admin", _("Admin")
        PLATFORM_OWNER = "platform_owner", _("Platform owner")

    telegram_id = models.BigIntegerField(unique=True, db_index=True)
    first_name = models.CharField(max_length=255, blank=True)
    last_name = models.CharField(max_length=255, blank=True)
    username = models.CharField(max_length=255, blank=True)
    role = models.CharField(
        max_length=16,
        choices=Role.choices,
        default=Role.BUYER,
    )
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    seller_terms_version = models.CharField(
        max_length=16,
        blank=True,
        help_text=_("Last accepted marketplace / seller terms version (empty = not accepted)."),
    )
    seller_terms_accepted_at = models.DateTimeField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = "telegram_id"
    REQUIRED_FIELDS: list[str] = []

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("user")
        verbose_name_plural = _("users")

    def __str__(self) -> str:
        return f"{self.telegram_id} ({self.get_role_display()})"


class TelegramWebhookDedup(models.Model):
    """Telegram webhook bir xil update ni ikki marta qayta ishlamaslik (takror yetkazish)."""

    update_id = models.BigIntegerField(unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Telegram webhook update")
        verbose_name_plural = _("Telegram webhook updates")


class BotOnboardingQuota(models.Model):
    """Kuniga chat uchun onboarding nudge ketma-ketligi soni (LocMem o‘rniga, barcha workerlar uchun)."""

    chat_id = models.BigIntegerField(db_index=True)
    day = models.DateField(db_index=True)
    count = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["chat_id", "day"], name="uniq_bot_onboarding_quota_chat_day"),
        ]
        verbose_name = _("Bot onboarding quota")
        verbose_name_plural = _("Bot onboarding quotas")
