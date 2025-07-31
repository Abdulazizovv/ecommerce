from django.urls import path
from apps.cart.views import (
    CartView, AddToCartView,
    UpdateCartItemView, RemoveCartItemView
)

urlpatterns = [
    path('', CartView.as_view(), name='cart-detail'),
    path('add/', AddToCartView.as_view(), name='cart-add'),
    path('update/<int:pk>/', UpdateCartItemView.as_view(), name='cart-update'),
    path('remove/<int:pk>/', RemoveCartItemView.as_view(), name='cart-remove'),
]
