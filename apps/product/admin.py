from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count
from apps.product.models import Product, ProductImage


class ProductImageInline(admin.TabularInline):
    """Inline for product images"""
    model = ProductImage
    extra = 1
    fields = ['image', 'alt_text', 'image_preview']
    readonly_fields = ['image_preview']
    
    def image_preview(self, obj):
        """Show image preview in admin"""
        if obj.image:
            return format_html(
                '<img src="{}" width="100" height="100" style="object-fit: cover; border-radius: 5px;" />',
                obj.image.url
            )
        return "Rasm yo'q"
    image_preview.short_description = 'Oldin ko\'rish'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Product admin interface"""
    inlines = [ProductImageInline]
    list_display = [
        'id', 'name', 'price', 'discount_price', 
        'status', 'category', 'creator', 'created_at'
    ]
    list_filter = ['status', 'category', 'created_at', 'creator']
    search_fields = ['name', 'description', 'category__name', 'creator__email']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    list_per_page = 25
    
    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('name', 'slug', 'description', 'category', 'tags')
        }),
        ('Narx ma\'lumotlari', {
            'fields': ('price', 'discount_price')
        }),
        ('Holat va yaratuvchi', {
            'fields': ('status', 'creator')
        }),
        ('Vaqt ma\'lumotlari', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queryset"""
        return super().get_queryset(request).select_related(
            'category', 'creator'
        ).prefetch_related('tags', 'images')
    
    actions = ['activate_products', 'deactivate_products', 'mark_out_of_stock']
    
    def activate_products(self, request, queryset):
        """Activate selected products"""
        updated = queryset.update(status='available')
        self.message_user(
            request,
            '{} ta mahsulot faollashtirildi.'.format(updated)
        )
    activate_products.short_description = 'Tanlangan mahsulotlarni faollashtirish'
    
    def deactivate_products(self, request, queryset):
        """Deactivate selected products"""
        updated = queryset.update(status='draft')
        self.message_user(
            request,
            '{} ta mahsulot qoralamasiga o\'tkazildi.'.format(updated)
        )
    deactivate_products.short_description = 'Tanlangan mahsulotlarni qoralamasiga o\'tkazish'
    
    def mark_out_of_stock(self, request, queryset):
        """Mark selected products as out of stock"""
        updated = queryset.update(status='out_of_stock')
        self.message_user(
            request,
            '{} ta mahsulot "tugagan" deb belgilandi.'.format(updated)
        )
    mark_out_of_stock.short_description = 'Tanlangan mahsulotlarni "tugagan" deb belgilash'


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    """Product Image admin"""
    list_display = ['id', 'product', 'image_preview', 'alt_text']
    list_filter = ['product__category']
    search_fields = ['product__name', 'alt_text']
    readonly_fields = ['image_preview']
    
    def image_preview(self, obj):
        """Show image preview"""
        if obj.image:
            return format_html(
                '<img src="{}" width="100" height="100" style="object-fit: cover; border-radius: 5px;" />',
                obj.image.url
            )
        return "Rasm yo'q"
    image_preview.short_description = 'Oldin ko\'rish'
    

