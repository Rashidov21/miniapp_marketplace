"""Core models (landing leads, etc.)."""
from __future__ import annotations

from django.db import models


class Lead(models.Model):
    """Marketing landing — ariza (modal form)."""

    class Source(models.TextChoices):
        LANDING_MODAL = "landing_modal", "Landing modal"
        LANDING_STICKY = "landing_sticky", "Landing sticky CTA"
        LANDING_HERO = "landing_hero", "Landing hero"
        LANDING_FINAL = "landing_final", "Landing final CTA"

    name = models.CharField(max_length=120)
    phone = models.CharField(max_length=40)
    comment = models.CharField(max_length=500, blank=True)
    source = models.CharField(
        max_length=32,
        choices=Source.choices,
        default=Source.LANDING_MODAL,
    )
    user_agent = models.CharField(max_length=512, blank=True)
    referrer = models.CharField(max_length=512, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Landing arizasi"
        verbose_name_plural = "Landing arizalari"

    def __str__(self) -> str:
        return f"{self.name} · {self.phone} · {self.created_at:%Y-%m-%d %H:%M}"
