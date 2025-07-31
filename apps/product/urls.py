from django.urls import path
from apps.product import views


urlpatterns = [
    path("", views.ProductListAPIView.as_view(), name="product-list"),
    path("<slug:slug>/", views.ProductDetailAPIView.as_view(), name="product-detail"),
]
