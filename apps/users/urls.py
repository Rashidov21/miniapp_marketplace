from django.urls import path

from apps.users import views

urlpatterns = [
    path("auth/telegram/", views.telegram_auth, name="api_telegram_auth"),
    path("me/", views.me, name="api_me"),
    path("me/become-seller/", views.become_seller, name="api_become_seller"),
]
