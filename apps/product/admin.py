from django.contrib import admin
from apps.product.models import Product, ProductImage

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    inlines = [ProductImageInline]
    list_display = ['name', 'price', 'status', 'category']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'category__name']
    list_filter = ['status', 'category']
    ordering = ['-created_at']
    

