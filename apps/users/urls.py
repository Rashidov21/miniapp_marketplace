from django.urls import path

from apps.users import views

urlpatterns = [
    path("auth/telegram/", views.telegram_auth, name="api_telegram_auth"),
    path("bot/webhook/<str:secret>/", views.telegram_webhook, name="api_telegram_webhook"),
    path("me/", views.me, name="api_me"),
    path("me/become-seller/", views.become_seller, name="api_become_seller"),
    path("me/accept-seller-terms/", views.accept_seller_terms, name="api_accept_seller_terms"),
]
