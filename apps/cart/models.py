from django.conf import settings
from django.db import models
from apps.product.models import Product
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from apps.users.models import User


class Cart(models.Model):
    user: "User" = models.ForeignKey(
        "users.User", on_delete=models.CASCADE, related_name="cart"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    items: "models.QuerySet[CartItem]"

    def total_price(self):
        return sum(item.total_price for item in self.items.all())

    def __str__(self):
        return f"Cart({self.user})"


class CartItem(models.Model):
    cart: "Cart" = models.ForeignKey(
        Cart, related_name="items", on_delete=models.CASCADE
    )
    product: "Product" = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    @property
    def unit_price(self):
        return self.product.discount_price or self.product.price

    @property
    def total_price(self):
        return self.unit_price * self.quantity

    class Meta:
        unique_together = ("cart", "product")

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"
