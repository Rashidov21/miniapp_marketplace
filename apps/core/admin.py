from __future__ import annotations

from django.contrib import admin

from apps.core.models import Lead


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "phone", "source", "created_at", "ip_address")
    list_filter = ("source", "created_at")
    search_fields = ("name", "phone", "comment")
    readonly_fields = ("user_agent", "referrer", "ip_address", "created_at")
    ordering = ("-created_at",)
