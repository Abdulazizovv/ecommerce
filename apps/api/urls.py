from django.urls import path, include


urlpatterns = [
    path("users/", include("apps.users.urls")),
    path("products/", include("apps.product.urls")),
    path("cart/", include("apps.cart.urls")),
]
