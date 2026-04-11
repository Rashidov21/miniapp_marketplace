from django.urls import path

from apps.core import views

urlpatterns = [
    path("", views.webapp_home, name="webapp_home"),
    path("legal/terms/", views.legal_terms, name="legal_terms"),
    path("legal/privacy/", views.legal_privacy, name="legal_privacy"),
    path("legal/seller/", views.legal_seller_agreement, name="legal_seller_agreement"),
    path("legal/content/", views.legal_content_policy, name="legal_content_policy"),
    path("my-orders/", views.my_orders_page, name="webapp_my_orders"),
    path("seller/", views.seller_dashboard, name="seller_dashboard"),
    path("seller/products/", views.seller_products_list_page, name="seller_products_list"),
    path("seller/shop/", views.shop_settings_page, name="shop_settings"),
    path("seller/subscription/", views.subscription_page, name="subscription"),
    path("seller/products/new/", views.product_form, name="product_new"),
    path("seller/products/<int:product_id>/edit/", views.product_form, name="product_edit"),
    path(
        "s/<slug:shop_slug>/p/<slug:product_slug>/order/",
        views.order_page,
        name="webapp_order_slug",
    ),
    path(
        "s/<slug:shop_slug>/p/<slug:product_slug>/",
        views.product_page,
        name="webapp_product_slug",
    ),
    path("s/<slug:shop_slug>/", views.shop_page, name="webapp_shop_slug"),
    path(
        "shop/<int:shop_id>/product/<int:product_id>/order/",
        views.order_legacy_redirect,
        name="order_page_legacy",
    ),
    path(
        "shop/<int:shop_id>/product/<int:product_id>/",
        views.product_legacy_redirect,
        name="product_page_legacy",
    ),
    path("shop/<int:shop_id>/", views.shop_legacy_redirect, name="shop_page_legacy"),
]
