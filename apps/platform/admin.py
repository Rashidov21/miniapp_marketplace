from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from apps.platform.models import AnalyticsEvent, StaffAuditLog


@admin.register(StaffAuditLog)
class StaffAuditLogAdmin(admin.ModelAdmin):
    list_display = ("id", "action", "actor", "target_type", "target_id", "created_at")
    list_filter = ("action", "created_at")
    search_fields = ("action", "target_id", "target_type", "actor__telegram_id", "actor__username")
    date_hierarchy = "created_at"
    list_select_related = ("actor",)
    readonly_fields = ("actor", "action", "target_type", "target_id", "payload", "created_at")


@admin.register(AnalyticsEvent)
class AnalyticsEventAdmin(admin.ModelAdmin):
    list_display = ("id", "event_type", "shop_id", "path", "created_at")
    list_filter = ("event_type", "created_at")
    search_fields = ("path", "event_type")
    date_hierarchy = "created_at"
