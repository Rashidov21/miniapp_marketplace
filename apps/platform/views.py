from __future__ import annotations

from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import LoginView
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods, require_POST

from apps.core.telegram import send_message
from apps.orders.models import Order
from apps.platform.forms import BroadcastForm, PlatformLoginForm
from apps.platform.services import log_staff_action
from apps.platform.utils import is_platform_staff
from apps.shops.models import Shop, SubscriptionPayment, SubscriptionPlan
from apps.shops.services import approve_subscription_payment
from apps.users.models import User

UserModel = get_user_model()


class PlatformLoginView(LoginView):
    template_name = "platform/login.html"
    authentication_form = PlatformLoginForm

    def form_valid(self, form):
        user = form.get_user()
        if not is_platform_staff(user):
            messages.error(self.request, _("Access denied. Platform staff only."))
            return redirect("platform_login")
        return super().form_valid(form)


def _staff_required(view_func):
    decorated = login_required(
        user_passes_test(is_platform_staff, login_url="/platform/login/")(view_func)
    )
    return decorated


@_staff_required
def dashboard(request: HttpRequest) -> HttpResponse:
    from apps.platform.models import AnalyticsEvent

    now = timezone.now()
    day_ago = now - timedelta(days=1)
    week_ago = now - timedelta(days=7)

    shop_views_day = AnalyticsEvent.objects.filter(
        event_type=AnalyticsEvent.EventType.SHOP_VIEW,
        created_at__gte=day_ago,
    ).count()
    shop_views_week = AnalyticsEvent.objects.filter(
        event_type=AnalyticsEvent.EventType.SHOP_VIEW,
        created_at__gte=week_ago,
    ).count()

    top_shops = (
        AnalyticsEvent.objects.filter(
            event_type=AnalyticsEvent.EventType.SHOP_VIEW,
            created_at__gte=week_ago,
            shop_id__isnull=False,
        )
        .values("shop_id")
        .annotate(c=Count("id"))
        .order_by("-c")[:10]
    )
    shop_names = {s.id: s.name for s in Shop.objects.filter(id__in=[x["shop_id"] for x in top_shops])}

    ctx = {
        "stats": {
            "users_total": UserModel.objects.count(),
            "users_active": UserModel.objects.filter(is_active=True).count(),
            "shops_total": Shop.objects.count(),
            "shops_active": Shop.objects.filter(is_active=True).count(),
            "orders_total": Order.objects.count(),
            "orders_week": Order.objects.filter(created_at__gte=week_ago).count(),
            "payments_pending": SubscriptionPayment.objects.filter(
                status=SubscriptionPayment.Status.PENDING
            ).count(),
            "payments_approved_week": SubscriptionPayment.objects.filter(
                status=SubscriptionPayment.Status.APPROVED,
                reviewed_at__gte=week_ago,
            ).count(),
            "shop_views_day": shop_views_day,
            "shop_views_week": shop_views_week,
        },
        "top_shops": [
            {"shop_id": row["shop_id"], "name": shop_names.get(row["shop_id"], "?"), "views": row["c"]}
            for row in top_shops
        ],
        "plans": SubscriptionPlan.objects.filter(is_active=True),
    }
    return render(request, "platform/dashboard.html", ctx)


@_staff_required
def payments_list(request: HttpRequest) -> HttpResponse:
    status_filter = request.GET.get("status") or "pending"
    qs = SubscriptionPayment.objects.select_related("shop", "plan", "reviewed_by").order_by("-created_at")
    if status_filter == "pending":
        qs = qs.filter(status=SubscriptionPayment.Status.PENDING)
    elif status_filter == "approved":
        qs = qs.filter(status=SubscriptionPayment.Status.APPROVED)
    elif status_filter == "rejected":
        qs = qs.filter(status=SubscriptionPayment.Status.REJECTED)

    paginator = Paginator(qs, 25)
    page = paginator.get_page(request.GET.get("page"))
    return render(
        request,
        "platform/payments.html",
        {"page": page, "status_filter": status_filter},
    )


@_staff_required
@require_POST
def payment_approve(request: HttpRequest, payment_id: int) -> HttpResponse:
    payment = get_object_or_404(SubscriptionPayment, pk=payment_id)
    if payment.status != SubscriptionPayment.Status.PENDING:
        messages.warning(request, _("Already processed."))
        return redirect("platform_payments")
    approve_subscription_payment(payment.shop, payment.plan)
    payment.status = SubscriptionPayment.Status.APPROVED
    payment.reviewed_at = timezone.now()
    payment.reviewed_by = request.user
    payment.save(update_fields=["status", "reviewed_at", "reviewed_by"])
    log_staff_action(
        request.user,
        "payment_approve",
        target_type="SubscriptionPayment",
        target_id=str(payment.pk),
        payload={"shop_id": payment.shop_id},
    )
    messages.success(request, _("Payment approved."))
    return redirect("platform_payments")


@_staff_required
@require_POST
def payment_reject(request: HttpRequest, payment_id: int) -> HttpResponse:
    payment = get_object_or_404(SubscriptionPayment, pk=payment_id)
    if payment.status != SubscriptionPayment.Status.PENDING:
        messages.warning(request, _("Already processed."))
        return redirect("platform_payments")
    payment.status = SubscriptionPayment.Status.REJECTED
    payment.reviewed_at = timezone.now()
    payment.reviewed_by = request.user
    payment.save(update_fields=["status", "reviewed_at", "reviewed_by"])
    shop = payment.shop
    if shop.subscription_status == Shop.SubscriptionStatus.PAYMENT_PENDING:
        shop.subscription_status = Shop.SubscriptionStatus.EXPIRED
        shop.save(update_fields=["subscription_status"])
    log_staff_action(
        request.user,
        "payment_reject",
        target_type="SubscriptionPayment",
        target_id=str(payment.pk),
    )
    messages.success(request, _("Payment rejected."))
    return redirect("platform_payments")


@_staff_required
def users_list(request: HttpRequest) -> HttpResponse:
    qs = UserModel.objects.all().order_by("-created_at")
    q = (request.GET.get("q") or "").strip()
    if q:
        if q.isdigit():
            qs = qs.filter(telegram_id=int(q))
        else:
            qs = qs.filter(Q(username__icontains=q) | Q(first_name__icontains=q))
    paginator = Paginator(qs, 30)
    page = paginator.get_page(request.GET.get("page"))
    return render(request, "platform/users.html", {"page": page, "q": q})


@_staff_required
@require_POST
def user_toggle_active(request: HttpRequest, user_id: int) -> HttpResponse:
    u = get_object_or_404(UserModel, pk=user_id)
    if u.is_superuser and u != request.user:
        messages.error(request, _("Cannot block superuser."))
        return redirect("platform_users")
    if u.role == User.Role.PLATFORM_OWNER and not request.user.is_superuser:
        messages.error(request, _("Only superuser can block platform owner."))
        return redirect("platform_users")
    u.is_active = not u.is_active
    u.save(update_fields=["is_active"])
    log_staff_action(
        request.user,
        "user_toggle_active",
        target_type="User",
        target_id=str(u.pk),
        payload={"is_active": u.is_active},
    )
    messages.success(request, _("User updated."))
    return redirect("platform_users")


@_staff_required
def shops_list(request: HttpRequest) -> HttpResponse:
    qs = Shop.objects.select_related("owner").order_by("-created_at")
    paginator = Paginator(qs, 25)
    page = paginator.get_page(request.GET.get("page"))
    return render(request, "platform/shops.html", {"page": page})


@_staff_required
@require_http_methods(["GET", "POST"])
def broadcast(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = BroadcastForm(request.POST)
        if form.is_valid():
            msg = form.cleaned_data["message"]
            seg = form.cleaned_data["segment"]
            qs = UserModel.objects.filter(is_active=True)
            if seg == "sellers":
                qs = qs.filter(role=User.Role.SELLER)
            elif seg == "buyers":
                qs = qs.filter(role=User.Role.BUYER)
            sent = 0
            for u in qs.iterator():
                if send_message(u.telegram_id, msg):
                    sent += 1
            log_staff_action(
                request.user,
                "broadcast",
                payload={"segment": seg, "sent": sent},
            )
            messages.success(request, _("Sent to %(n)s users.") % {"n": sent})
            return redirect("platform_broadcast")
    else:
        form = BroadcastForm()
    return render(request, "platform/broadcast.html", {"form": form})


@_staff_required
def audit_log(request: HttpRequest) -> HttpResponse:
    from apps.platform.models import StaffAuditLog

    qs = StaffAuditLog.objects.select_related("actor").order_by("-created_at")[:200]
    return render(request, "platform/audit.html", {"logs": qs})
