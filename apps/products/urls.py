from django.urls import path

from apps.products import views

urlpatterns = [
    path("shops/<int:shop_id>/products/", views.product_list_public, name="api_product_list_public"),
    path(
        "shops/<int:shop_id>/products/<int:product_id>/public/",
        views.product_detail_public,
        name="api_product_detail_public",
    ),
    path("seller/products/", views.product_list_manage, name="api_seller_products"),
    path("seller/products/<int:product_id>/", views.product_detail_manage, name="api_seller_product_detail"),
    path("admin/products/<int:product_id>/", views.product_admin_block, name="api_admin_product"),
]
