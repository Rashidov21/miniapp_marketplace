from django.urls import path

from apps.platform import api

urlpatterns = [
    path("stats/", api.platform_stats_json, name="api_platform_stats"),
]
