"""Platform JSON API (session auth — brauzer yoki keyinchalik token)."""
from datetime import timedelta

from django.utils import timezone
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.orders.models import Order
from apps.platform.models import AnalyticsEvent
from apps.platform.utils import is_platform_staff
from apps.shops.models import Shop, SubscriptionPayment
from apps.users.models import User


@api_view(["GET"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def platform_stats_json(request):
    if not is_platform_staff(request.user):
        return Response({"detail": "Forbidden"}, status=403)
    now = timezone.now()
    week_ago = now - timedelta(days=7)
    return Response(
        {
            "users_total": User.objects.count(),
            "users_active": User.objects.filter(is_active=True).count(),
            "shops_total": Shop.objects.count(),
            "orders_total": Order.objects.count(),
            "orders_week": Order.objects.filter(created_at__gte=week_ago).count(),
            "payments_pending": SubscriptionPayment.objects.filter(
                status=SubscriptionPayment.Status.PENDING
            ).count(),
            "shop_views_week": AnalyticsEvent.objects.filter(
                event_type=AnalyticsEvent.EventType.SHOP_VIEW,
                created_at__gte=week_ago,
            ).count(),
        }
    )
