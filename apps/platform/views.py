from __future__ import annotations

import csv
import logging
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import LoginView
from django.core.paginator import Paginator
from django.core.cache import cache
from django.db.models import Count, Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods, require_POST

from apps.core.models import Lead
from apps.core.telegram import send_message
from apps.orders.models import Order
from apps.platform.forms import BroadcastForm, PlatformLoginForm
from apps.platform.services import log_staff_action
from apps.platform.utils import is_platform_staff, is_platform_superuser
from apps.shops.models import Shop, SubscriptionPayment, SubscriptionPlan
from apps.shops.services import approve_subscription_payment
from apps.users.models import User

logger = logging.getLogger(__name__)

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
    pending_payments_qs = SubscriptionPayment.objects.filter(
        status=SubscriptionPayment.Status.PENDING
    ).select_related("shop", "plan")
    pending_oldest = pending_payments_qs.order_by("created_at").first()
    trial_expiring_qs = Shop.objects.filter(
        subscription_status=Shop.SubscriptionStatus.TRIAL,
        trial_ends_at__isnull=False,
        trial_ends_at__gte=now,
        trial_ends_at__lte=now + timedelta(days=3),
    ).select_related("owner")
    action_queue = []
    for p in pending_payments_qs.order_by("created_at")[:6]:
        action_queue.append(
            {
                "type": "payment_pending",
                "title": f"{p.shop.name} · {p.plan.name}",
                "meta": str(_("Pending payment since %(dt)s")) % {"dt": timezone.localtime(p.created_at).strftime("%Y-%m-%d %H:%M")},
                "url": f"{reverse('platform_payments')}?status=pending&q={p.id}",
            }
        )
    for s in trial_expiring_qs.order_by("trial_ends_at")[:6]:
        action_queue.append(
            {
                "type": "trial_expiring",
                "title": s.name,
                "meta": str(_("Trial ends at %(dt)s")) % {"dt": timezone.localtime(s.trial_ends_at).strftime("%Y-%m-%d %H:%M")},
                "url": f"{reverse('platform_shops')}?q={s.id}",
            }
        )

    ctx = {
        "stats": {
            "users_total": UserModel.objects.count(),
            "users_active": UserModel.objects.filter(is_active=True).count(),
            "shops_total": Shop.objects.count(),
            "shops_active": Shop.objects.filter(is_active=True).count(),
            "orders_total": Order.objects.count(),
            "orders_today": Order.objects.filter(
                created_at__gte=timezone.localtime(now).replace(hour=0, minute=0, second=0, microsecond=0)
            ).count(),
            "orders_week": Order.objects.filter(created_at__gte=week_ago).count(),
            "shops_week": Shop.objects.filter(created_at__gte=week_ago).count(),
            "payments_pending": SubscriptionPayment.objects.filter(
                status=SubscriptionPayment.Status.PENDING
            ).count(),
            "payments_approved_week": SubscriptionPayment.objects.filter(
                status=SubscriptionPayment.Status.APPROVED,
                reviewed_at__gte=week_ago,
            ).count(),
            "pending_oldest_at": pending_oldest.created_at if pending_oldest else None,
            "trial_expiring_3d": trial_expiring_qs.count(),
            "shop_views_day": shop_views_day,
            "shop_views_week": shop_views_week,
        },
        "top_shops": [
            {"shop_id": row["shop_id"], "name": shop_names.get(row["shop_id"], "?"), "views": row["c"]}
            for row in top_shops
        ],
        "plans": SubscriptionPlan.objects.filter(is_active=True),
        "action_queue": action_queue[:10],
        "recent_leads": Lead.objects.order_by("-created_at")[:8],
        "leads_week": Lead.objects.filter(created_at__gte=week_ago).count(),
    }
    return render(request, "platform/dashboard.html", ctx)


@_staff_required
def leads_list(request: HttpRequest) -> HttpResponse:
    qs = Lead.objects.all()
    q = (request.GET.get("q") or "").strip()
    if q:
        qs = qs.filter(
            Q(name__icontains=q) | Q(phone__icontains=q) | Q(comment__icontains=q)
        )
    paginator = Paginator(qs.order_by("-created_at"), 40)
    page = paginator.get_page(request.GET.get("page"))
    return render(
        request,
        "platform/leads.html",
        {"page": page, "q": q},
    )


@_staff_required
def payments_list(request: HttpRequest) -> HttpResponse:
    status_filter = request.GET.get("status") or "pending"
    channel_filter = (request.GET.get("channel") or "").strip()
    q = (request.GET.get("q") or "").strip()
    qs = SubscriptionPayment.objects.select_related("shop", "plan", "reviewed_by").order_by("-created_at")
    if status_filter == "pending":
        qs = qs.filter(status=SubscriptionPayment.Status.PENDING)
    elif status_filter == "approved":
        qs = qs.filter(status=SubscriptionPayment.Status.APPROVED)
    elif status_filter == "rejected":
        qs = qs.filter(status=SubscriptionPayment.Status.REJECTED)
    if channel_filter in (
        SubscriptionPayment.Channel.MANUAL_SCREENSHOT,
        SubscriptionPayment.Channel.TELEGRAM,
    ):
        qs = qs.filter(channel=channel_filter)
    if q:
        q_filter = (
            Q(shop__name__icontains=q)
            | Q(plan__name__icontains=q)
            | Q(telegram_payment_charge_id__icontains=q)
            | Q(invoice_payload__icontains=q)
        )
        if q.isdigit():
            q_filter |= Q(id=int(q)) | Q(shop__owner__telegram_id=int(q))
        qs = qs.filter(q_filter)

    pending_count = SubscriptionPayment.objects.filter(status=SubscriptionPayment.Status.PENDING).count()
    approved_count = SubscriptionPayment.objects.filter(status=SubscriptionPayment.Status.APPROVED).count()
    rejected_count = SubscriptionPayment.objects.filter(status=SubscriptionPayment.Status.REJECTED).count()
    paginator = Paginator(qs, 25)
    page = paginator.get_page(request.GET.get("page"))
    return render(
        request,
        "platform/payments.html",
        {
            "page": page,
            "status_filter": status_filter,
            "channel_filter": channel_filter,
            "q": q,
            "pending_count": pending_count,
            "approved_count": approved_count,
            "rejected_count": rejected_count,
        },
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
    logger.info(
        "platform_payment_approved payment_id=%s shop_id=%s reviewer_id=%s",
        payment.pk,
        payment.shop_id,
        request.user.pk,
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
    admin_note = (request.POST.get("admin_note") or "").strip()
    if not admin_note:
        messages.error(request, _("Reject reason is required."))
        return redirect("platform_payments")
    payment.status = SubscriptionPayment.Status.REJECTED
    payment.admin_note = admin_note
    payment.reviewed_at = timezone.now()
    payment.reviewed_by = request.user
    payment.save(update_fields=["status", "admin_note", "reviewed_at", "reviewed_by"])
    shop = payment.shop
    if shop.subscription_status == Shop.SubscriptionStatus.PAYMENT_PENDING:
        shop.subscription_status = Shop.SubscriptionStatus.EXPIRED
        shop.save(update_fields=["subscription_status"])
    log_staff_action(
        request.user,
        "payment_reject",
        target_type="SubscriptionPayment",
        target_id=str(payment.pk),
        payload={"reason": admin_note},
    )
    logger.info(
        "platform_payment_rejected payment_id=%s shop_id=%s reviewer_id=%s",
        payment.pk,
        payment.shop_id,
        request.user.pk,
    )
    messages.success(request, _("Payment rejected."))
    return redirect("platform_payments")


@_staff_required
def users_list(request: HttpRequest) -> HttpResponse:
    qs = UserModel.objects.all().order_by("-created_at")
    q = (request.GET.get("q") or "").strip()
    role = (request.GET.get("role") or "").strip()
    is_active = (request.GET.get("is_active") or "").strip()
    if q:
        if q.isdigit():
            qs = qs.filter(telegram_id=int(q))
        else:
            qs = qs.filter(
                Q(username__icontains=q)
                | Q(first_name__icontains=q)
                | Q(last_name__icontains=q)
            )
    if role in {User.Role.BUYER, User.Role.SELLER, User.Role.ADMIN, User.Role.PLATFORM_OWNER}:
        qs = qs.filter(role=role)
    if is_active == "1":
        qs = qs.filter(is_active=True)
    elif is_active == "0":
        qs = qs.filter(is_active=False)
    paginator = Paginator(qs, 30)
    page = paginator.get_page(request.GET.get("page"))
    return render(
        request,
        "platform/users.html",
        {"page": page, "q": q, "role": role, "is_active": is_active},
    )


@_staff_required
@require_POST
def user_toggle_active(request: HttpRequest, user_id: int) -> HttpResponse:
    u = get_object_or_404(UserModel, pk=user_id)
    if u.is_superuser and u != request.user:
        messages.error(request, _("Cannot block superuser."))
        return redirect("platform_users")
    if u.role == User.Role.PLATFORM_OWNER and not is_platform_superuser(request.user):
        messages.error(request, _("Only platform administrators can change this account."))
        return redirect("platform_users")
    reason = (request.POST.get("reason") or "").strip()
    if not reason:
        messages.error(request, _("Please provide a reason."))
        return redirect("platform_users")
    u.is_active = not u.is_active
    u.save(update_fields=["is_active"])
    log_staff_action(
        request.user,
        "user_toggle_active",
        target_type="User",
        target_id=str(u.pk),
        payload={"is_active": u.is_active, "reason": reason},
    )
    messages.success(request, _("User updated."))
    return redirect("platform_users")


@_staff_required
def shops_list(request: HttpRequest) -> HttpResponse:
    qs = Shop.objects.select_related("owner").order_by("-created_at")
    q = (request.GET.get("q") or "").strip()
    is_active = (request.GET.get("is_active") or "").strip()
    is_verified = (request.GET.get("is_verified") or "").strip()
    subscription_status = (request.GET.get("subscription_status") or "").strip()
    if q:
        if q.isdigit():
            qs = qs.filter(Q(id=int(q)) | Q(owner__telegram_id=int(q)))
        else:
            qs = qs.filter(Q(name__icontains=q) | Q(owner__username__icontains=q))
    if is_active == "1":
        qs = qs.filter(is_active=True)
    elif is_active == "0":
        qs = qs.filter(is_active=False)
    if is_verified == "1":
        qs = qs.filter(is_verified=True)
    elif is_verified == "0":
        qs = qs.filter(is_verified=False)
    if subscription_status in dict(Shop.SubscriptionStatus.choices):
        qs = qs.filter(subscription_status=subscription_status)
    paginator = Paginator(qs, 25)
    page = paginator.get_page(request.GET.get("page"))
    return render(
        request,
        "platform/shops.html",
        {
            "page": page,
            "q": q,
            "is_active": is_active,
            "is_verified": is_verified,
            "subscription_status": subscription_status,
            "subscription_choices": Shop.SubscriptionStatus.choices,
        },
    )


@_staff_required
@require_POST
def shop_toggle_active(request: HttpRequest, shop_id: int) -> HttpResponse:
    shop = get_object_or_404(Shop, pk=shop_id)
    reason = (request.POST.get("reason") or "").strip()
    if not reason:
        messages.error(request, _("Please provide a reason."))
        return redirect("platform_shops")
    shop.is_active = not shop.is_active
    shop.save(update_fields=["is_active"])
    log_staff_action(
        request.user,
        "shop_toggle_active",
        target_type="Shop",
        target_id=str(shop.pk),
        payload={"is_active": shop.is_active, "reason": reason},
    )
    messages.success(request, _("Shop updated."))
    return redirect("platform_shops")


@_staff_required
@require_POST
def shop_toggle_verified(request: HttpRequest, shop_id: int) -> HttpResponse:
    shop = get_object_or_404(Shop, pk=shop_id)
    reason = (request.POST.get("reason") or "").strip()
    if not reason:
        messages.error(request, _("Please provide a reason."))
        return redirect("platform_shops")
    shop.is_verified = not shop.is_verified
    shop.save(update_fields=["is_verified"])
    log_staff_action(
        request.user,
        "shop_toggle_verified",
        target_type="Shop",
        target_id=str(shop.pk),
        payload={"is_verified": shop.is_verified, "reason": reason},
    )
    messages.success(request, _("Shop updated."))
    return redirect("platform_shops")


@_staff_required
@require_http_methods(["GET", "POST"])
def broadcast(request: HttpRequest) -> HttpResponse:
    buyers_count = UserModel.objects.filter(is_active=True, role=User.Role.BUYER).count()
    sellers_count = UserModel.objects.filter(is_active=True, role=User.Role.SELLER).count()
    all_count = UserModel.objects.filter(is_active=True).count()
    if request.method == "POST":
        form = BroadcastForm(request.POST)
        if form.is_valid():
            if not cache.add(f"platform_broadcast:{request.user.pk}", "1", timeout=60):
                messages.error(request, _("Please wait about a minute before sending another broadcast."))
                return redirect("platform_broadcast")
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
    return render(
        request,
        "platform/broadcast.html",
        {
            "form": form,
            "buyers_count": buyers_count,
            "sellers_count": sellers_count,
            "all_count": all_count,
        },
    )


@_staff_required
def audit_log(request: HttpRequest) -> HttpResponse:
    from apps.platform.models import StaffAuditLog

    qs = StaffAuditLog.objects.select_related("actor").order_by("-created_at")
    q = (request.GET.get("q") or "").strip()
    action = (request.GET.get("action") or "").strip()
    days = (request.GET.get("days") or "").strip()
    if q:
        qs = qs.filter(
            Q(target_id__icontains=q)
            | Q(target_type__icontains=q)
            | Q(actor__username__icontains=q)
            | Q(actor__first_name__icontains=q)
        )
    if action:
        qs = qs.filter(action__icontains=action)
    if days.isdigit():
        qs = qs.filter(created_at__gte=timezone.now() - timedelta(days=int(days)))
    paginator = Paginator(qs, 50)
    page = paginator.get_page(request.GET.get("page"))
    return render(
        request,
        "platform/audit.html",
        {"page": page, "q": q, "action": action, "days": days},
    )


@_staff_required
def orders_list(request: HttpRequest) -> HttpResponse:
    qs = Order.objects.select_related("shop", "product", "buyer").order_by("-created_at")
    q = (request.GET.get("q") or "").strip()
    status_filter = (request.GET.get("status") or "").strip()
    shop_id = (request.GET.get("shop_id") or "").strip()
    if q:
        if q.isdigit():
            qs = qs.filter(Q(id=int(q)) | Q(phone__icontains=q) | Q(shop__owner__telegram_id=int(q)))
        else:
            qs = qs.filter(
                Q(customer_name__icontains=q)
                | Q(phone__icontains=q)
                | Q(shop__name__icontains=q)
                | Q(product__name__icontains=q)
            )
    if status_filter in dict(Order.Status.choices):
        qs = qs.filter(status=status_filter)
    if shop_id.isdigit():
        qs = qs.filter(shop_id=int(shop_id))
    paginator = Paginator(qs, 30)
    page = paginator.get_page(request.GET.get("page"))
    return render(
        request,
        "platform/orders.html",
        {
            "page": page,
            "q": q,
            "status_filter": status_filter,
            "shop_id": shop_id,
            "status_choices": Order.Status.choices,
        },
    )


@_staff_required
def export_orders_csv(request: HttpRequest) -> HttpResponse:
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="orders_export.csv"'
    w = csv.writer(response)
    w.writerow(["id", "shop", "product", "status", "customer_name", "phone", "created_at"])
    qs = Order.objects.select_related("shop", "product").order_by("-created_at")[:8000]
    for o in qs.iterator():
        w.writerow(
            [
                o.id,
                o.shop.name,
                o.product.name,
                o.status,
                o.customer_name,
                o.phone,
                o.created_at.isoformat(),
            ]
        )
    return response


@_staff_required
def export_payments_csv(request: HttpRequest) -> HttpResponse:
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="payments_export.csv"'
    w = csv.writer(response)
    w.writerow(["id", "shop", "plan", "amount", "status", "created_at", "reviewed_at"])
    qs = SubscriptionPayment.objects.select_related("shop", "plan").order_by("-created_at")[:8000]
    for p in qs.iterator():
        w.writerow(
            [
                p.id,
                p.shop.name,
                p.plan.name if p.plan_id else "",
                str(p.amount),
                p.status,
                p.created_at.isoformat(),
                p.reviewed_at.isoformat() if p.reviewed_at else "",
            ]
        )
    return response
