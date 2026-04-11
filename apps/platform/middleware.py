import logging
import re

from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)

_SHOP_ID_PATH = re.compile(r"^/webapp/shop/(\d+)/")
_SHOP_SLUG_PATH = re.compile(r"^/webapp/s/([^/]+)/")


class AnalyticsMiddleware(MiddlewareMixin):
    """GET /webapp/s/<slug>/ yoki /webapp/shop/<id>/ uchun AnalyticsEvent yozadi (engil)."""

    def process_response(self, request, response):
        if request.method != "GET" or response.status_code != 200:
            return response
        if request.path.startswith("/platform/") or request.path.startswith("/admin/"):
            return response
        shop_id = None
        m_id = _SHOP_ID_PATH.match(request.path)
        if m_id:
            shop_id = int(m_id.group(1))
        else:
            m_slug = _SHOP_SLUG_PATH.match(request.path)
            if m_slug:
                try:
                    from apps.shops.models import Shop

                    shop_id = (
                        Shop.objects.filter(slug=m_slug.group(1))
                        .values_list("id", flat=True)
                        .first()
                    )
                except Exception:
                    shop_id = None
        if shop_id is None:
            return response
        try:
            from apps.platform.models import AnalyticsEvent

            AnalyticsEvent.objects.create(
                event_type=AnalyticsEvent.EventType.SHOP_VIEW,
                shop_id=shop_id,
                path=request.get_full_path()[:512],
            )
        except Exception:
            logger.exception("AnalyticsMiddleware failed")
        return response
