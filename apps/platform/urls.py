from django.contrib.auth import views as auth_views
from django.urls import path

from apps.platform import views

urlpatterns = [
    path("login/", views.PlatformLoginView.as_view(), name="platform_login"),
    path(
        "logout/",
        auth_views.LogoutView.as_view(),
        name="platform_logout",
    ),
    path("", views.dashboard, name="platform_dashboard"),
    path("payments/", views.payments_list, name="platform_payments"),
    path("payments/<int:payment_id>/approve/", views.payment_approve, name="platform_payment_approve"),
    path("payments/<int:payment_id>/reject/", views.payment_reject, name="platform_payment_reject"),
    path("users/", views.users_list, name="platform_users"),
    path("users/<int:user_id>/toggle/", views.user_toggle_active, name="platform_user_toggle"),
    path("shops/", views.shops_list, name="platform_shops"),
    path("shops/<int:shop_id>/toggle-active/", views.shop_toggle_active, name="platform_shop_toggle_active"),
    path("shops/<int:shop_id>/toggle-verified/", views.shop_toggle_verified, name="platform_shop_toggle_verified"),
    path("orders/", views.orders_list, name="platform_orders"),
    path("broadcast/", views.broadcast, name="platform_broadcast"),
    path("audit/", views.audit_log, name="platform_audit"),
    path("leads/", views.leads_list, name="platform_leads"),
    path("export/orders.csv", views.export_orders_csv, name="platform_export_orders"),
    path("export/payments.csv", views.export_payments_csv, name="platform_export_payments"),
]
