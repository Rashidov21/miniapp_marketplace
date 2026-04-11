from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from apps.core import views as core_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("platform/", include("apps.platform.urls")),
    path("api/platform/", include("apps.platform.api_urls")),
    path("api/", include("apps.users.urls")),
    path("api/", include("apps.shops.urls")),
    path("api/", include("apps.products.urls")),
    path("api/", include("apps.orders.urls")),
    path("api/landing/lead/", core_views.landing_lead_submit, name="landing_lead_submit"),
    path("webapp/", include("apps.core.urls")),
    path("", core_views.landing_page, name="landing"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = "apps.core.views.page_not_found"
