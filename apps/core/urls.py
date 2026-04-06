from django.urls import path

from apps.core import views

urlpatterns = [
    path("", views.webapp_home, name="webapp_home"),
    path("seller/", views.seller_dashboard, name="seller_dashboard"),
    path("seller/products/new/", views.product_form, name="product_new"),
    path("seller/products/<int:product_id>/edit/", views.product_form, name="product_edit"),
    path("shop/<int:shop_id>/", views.shop_page, name="shop_page"),
    path("shop/<int:shop_id>/product/<int:product_id>/", views.product_page, name="product_page"),
    path(
        "shop/<int:shop_id>/product/<int:product_id>/order/",
        views.order_page,
        name="order_page",
    ),
]
