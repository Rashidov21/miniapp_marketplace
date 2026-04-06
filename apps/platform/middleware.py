import logging
import re

from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)

_SHOP_PATH = re.compile(r"^/webapp/shop/(\d+)/")


class AnalyticsMiddleware(MiddlewareMixin):
    """GET /webapp/shop/<id>/ uchun AnalyticsEvent yozadi (engil)."""

    def process_response(self, request, response):
        if request.method != "GET" or response.status_code != 200:
            return response
        if request.path.startswith("/platform/") or request.path.startswith("/admin/"):
            return response
        m = _SHOP_PATH.match(request.path)
        if not m:
            return response
        try:
            from apps.platform.models import AnalyticsEvent

            AnalyticsEvent.objects.create(
                event_type=AnalyticsEvent.EventType.SHOP_VIEW,
                shop_id=int(m.group(1)),
                path=request.get_full_path()[:512],
            )
        except Exception:
            logger.exception("AnalyticsMiddleware failed")
        return response
