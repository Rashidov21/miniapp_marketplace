from django.urls import path

from apps.orders import views

urlpatterns = [
    path("orders/mine/", views.buyer_orders_mine, name="api_buyer_orders_mine"),
    path("orders/", views.order_create, name="api_order_create"),
    path("orders/<int:order_id>/", views.buyer_order_detail, name="api_order_detail"),
    path("seller/orders/", views.seller_orders, name="api_seller_orders"),
    path("seller/orders/<int:order_id>/", views.seller_order_update, name="api_seller_order_update"),
]
