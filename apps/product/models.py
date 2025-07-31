from django.db import models
from django.utils.text import slugify
from taggit.managers import TaggableManager


class Product(models.Model):
    class ProductStatus(models.TextChoices):
        AVAILABLE = "available", "Available"
        OUT_OF_STOCK = "out_of_stock", "Out of Stock"
        DRAFT = "draft", "Draft"

    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )
    category = models.ForeignKey(
        "category.Category", related_name="products", on_delete=models.CASCADE
    )
    tags = TaggableManager(blank=True)
    status = models.CharField(
        max_length=20, choices=ProductStatus.choices, default=ProductStatus.AVAILABLE
    )

    creator = models.ForeignKey(
        "users.User",
        related_name="products",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
    
    @property
    def final_price(self):
        """Calculate the final price after discount."""
        if self.discount_price:
            return self.discount_price
        return self.price


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product, related_name="images", on_delete=models.CASCADE
    )
    image = models.ImageField(upload_to="products/gallery/")
    alt_text = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"Image for {self.product.name}"
