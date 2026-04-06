from django.urls import path

from apps.shops import views

urlpatterns = [
    path("subscription/plans/", views.subscription_plans_list, name="api_subscription_plans"),
    path("shops/", views.shop_create, name="api_shop_create"),
    path("shops/mine/", views.shop_mine, name="api_shop_mine"),
    path("shops/mine/payments/", views.subscription_payment_create, name="api_shop_payment_create"),
    path("shops/<int:shop_id>/", views.shop_update, name="api_shop_update"),
    path("shops/<int:shop_id>/public/", views.shop_public, name="api_shop_public"),
    path("shops/<int:shop_id>/link/", views.shop_link, name="api_shop_link"),
]
