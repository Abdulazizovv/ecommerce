from django.db import models
from typing import TYPE_CHECKING
import random
from datetime import datetime

if TYPE_CHECKING:
    from apps.users.models import User
    from apps.product.models import Product


def generate_order_id():
    """Generate unique order ID in format YYYYMMDD-XXXXXX with sequential numbers"""
    from apps.order.models import Order

    date_str = datetime.now().strftime("%Y%m%d")

    # Find the highest order number for today
    today_orders = Order.objects.filter(order_id__startswith=date_str).order_by(
        "-order_id"
    )

    if today_orders.exists():
        # Get the last order's number and increment it
        last_order_id = today_orders.first().order_id
        last_number = int(last_order_id.split("-")[1])
        next_number = last_number + 1
    else:
        # First order of the day
        next_number = 1

    # Format with 6 digits (000001, 000002, etc.)
    return f"{date_str}-{next_number:06d}"


class Order(models.Model):
    order_id = models.CharField(max_length=100, unique=True, default=generate_order_id)
    user: "User" = models.ForeignKey(
        "users.User", on_delete=models.CASCADE, related_name="orders"
    )

    class OrderStatus(models.TextChoices):
        NEW = "new", "Yangi"
        PENDING = "pending", "Jarayonda"
        COMPLETED = "completed", "Yakunlangan"
        CANCELLED = "cancelled", "Bekor qilingan"

    status = models.CharField(
        max_length=25, choices=OrderStatus.choices, default=OrderStatus.NEW
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    items: "models.QuerySet[OrderItem]"
    
    # This field is used to store the total price of the order even if product prices change
    # after the order is created. It allows us to keep a consistent total price for the
    # order even if product prices are updated later.
    order_price = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)

    class Meta:
        verbose_name = "Buyurtma"
        verbose_name_plural = "Buyurtmalar"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Buyurtma #{self.id} - {self.get_status_display()}"

    def save(self, *args, **kwargs):
        if not self.order_id:
            self.order_id = generate_order_id()
        super().save(*args, **kwargs)

    @property
    def total_price(self):
        """Calculate the total price of all items in the order."""
        return sum(item.item_price * item.quantity for item in self.items.all())


class OrderItem(models.Model):
    order: Order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="items"
    )
    product: "Product" = models.ForeignKey(
        "product.Product", on_delete=models.CASCADE, related_name="order_items"
    )
    quantity = models.PositiveIntegerField(default=1)
    
    # This field is used to store the price of the item at the time of order creation.
    # It allows us to keep a consistent price for the item even if product prices change later.
    # This is useful for historical accuracy and to prevent issues with price changes after an order is placed.
    item_price = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )

    class Meta:
        verbose_name = "Buyurtma elementi"
        verbose_name_plural = "Buyurtma elementlari"
        unique_together = ("order", "product")

    def __str__(self):
        return f"{self.product.name} - {self.quantity} ta"

    def save(self, *args, **kwargs):
        if not self.item_price:
            self.item_price = self.product.final_price
        super().save(*args, **kwargs)

    @property
    def total_item_price(self):
        """Calculate total price for this item using stored item_price"""
        if self.item_price:
            return self.item_price * self.quantity
        return 0
