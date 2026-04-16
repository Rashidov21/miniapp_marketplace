from django.urls import path

from apps.orders import views

urlpatterns = [
    path("orders/mine/", views.buyer_orders_mine, name="api_buyer_orders_mine"),
    path("orders/", views.order_create, name="api_order_create"),
    path("orders/<int:order_id>/cancel/", views.buyer_order_cancel, name="api_buyer_order_cancel"),
    path("orders/<int:order_id>/", views.buyer_order_detail, name="api_order_detail"),
    path("seller/orders/", views.seller_orders, name="api_seller_orders"),
    path(
        "seller/orders/<int:order_id>/accept/",
        views.seller_order_accept,
        name="api_seller_order_accept",
    ),
    path(
        "seller/orders/<int:order_id>/deliver/",
        views.seller_order_deliver,
        name="api_seller_order_deliver",
    ),
    path(
        "seller/orders/<int:order_id>/cancel/",
        views.seller_order_cancel_by_seller,
        name="api_seller_order_cancel",
    ),
    path("seller/orders/<int:order_id>/", views.seller_order_update, name="api_seller_order_update"),
]
