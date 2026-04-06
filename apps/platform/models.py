from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class StaffAuditLog(models.Model):
    """Platform egasi harakatlari."""

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="staff_audit_actions",
    )
    action = models.CharField(max_length=64, db_index=True)
    target_type = models.CharField(max_length=32, blank=True)
    target_id = models.CharField(max_length=64, blank=True)
    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("staff audit log")
        verbose_name_plural = _("staff audit logs")


class AnalyticsEvent(models.Model):
    """Minimal tashrif logi (do‘kon sahifasi)."""

    class EventType(models.TextChoices):
        SHOP_VIEW = "shop_view", _("Shop view")

    event_type = models.CharField(max_length=32, choices=EventType.choices, db_index=True)
    path = models.CharField(max_length=512, blank=True)
    shop_id = models.PositiveIntegerField(null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["-created_at", "event_type"]),
        ]
        verbose_name = _("analytics event")
        verbose_name_plural = _("analytics events")
