from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from apps.platform.models import AnalyticsEvent, StaffAuditLog


@admin.register(StaffAuditLog)
class StaffAuditLogAdmin(admin.ModelAdmin):
    list_display = ("id", "action", "actor", "target_type", "target_id", "created_at")
    list_filter = ("action",)
    search_fields = ("action", "target_id")
    readonly_fields = ("actor", "action", "target_type", "target_id", "payload", "created_at")


@admin.register(AnalyticsEvent)
class AnalyticsEventAdmin(admin.ModelAdmin):
    list_display = ("id", "event_type", "shop_id", "path", "created_at")
    list_filter = ("event_type",)
