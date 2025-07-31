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
    """Professional Product admin interface"""
    inlines = [ProductImageInline]
    list_display = [
        'id', 'name', 'price_formatted', 'discount_price_formatted', 
        'status_colored', 'category', 'creator', 'images_count',
        'tags_list', 'created_at_formatted'
    ]
    list_filter = ['status', 'category', 'created_at', 'creator']
    search_fields = ['name', 'description', 'category__name', 'creator__email', 'tags__name']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['slug', 'created_at', 'updated_at', 'final_price_display']
    ordering = ['-created_at']
    list_per_page = 25
    
    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('name', 'slug', 'description', 'category', 'tags')
        }),
        ('Narx ma\'lumotlari', {
            'fields': ('price', 'discount_price', 'final_price_display')
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
    
    def price_formatted(self, obj):
        """Format price display"""
        return format_html(
            '<span style="font-weight: bold; color: #0066cc;">{:,.0f} so\'m</span>',
            obj.price
        )
    price_formatted.short_description = 'Narx'
    price_formatted.admin_order_field = 'price'
    
    def discount_price_formatted(self, obj):
        """Format discount price display"""
        if obj.discount_price:
            return format_html(
                '<span style="font-weight: bold; color: #28a745;">{:,.0f} so\'m</span>',
                obj.discount_price
            )
        return format_html('<span style="color: #999;">—</span>')
    discount_price_formatted.short_description = 'Chegirma narxi'
    discount_price_formatted.admin_order_field = 'discount_price'
    
    def final_price_display(self, obj):
        """Display final price calculation"""
        final = obj.final_price
        html = f'<strong style="color: #0066cc; font-size: 14px;">{final:,.0f} so\'m</strong>'
        
        if obj.discount_price:
            savings = obj.price - obj.discount_price
            percentage = (savings / obj.price) * 100
            html += f'<br><small style="color: #28a745;">({percentage:.0f}% chegirma)</small>'
        
        return format_html(html)
    final_price_display.short_description = 'Yakuniy narx'
    
    def status_colored(self, obj):
        """Display colored status"""
        colors = {
            'active': '#28a745',
            'inactive': '#6c757d', 
            'out_of_stock': '#dc3545'
        }
        status_names = {
            'active': 'Faol',
            'inactive': 'Nofaol',
            'out_of_stock': 'Tugagan'
        }
        
        color = colors.get(obj.status, '#6c757d')
        name = status_names.get(obj.status, obj.status)
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">● {}</span>',
            color, name
        )
    status_colored.short_description = 'Holat'
    status_colored.admin_order_field = 'status'
    
    def images_count(self, obj):
        """Display images count"""
        count = obj.images.count()
        if count > 0:
            return format_html(
                '<span style="color: #0066cc; font-weight: bold;">{} ta</span>',
                count
            )
        return format_html('<span style="color: #dc3545;">0 ta</span>')
    images_count.short_description = 'Rasmlar'
    
    def tags_list(self, obj):
        """Display tags list"""
        tags = obj.tags.all()[:3]  # Show first 3 tags
        if tags:
            tag_html = ', '.join([
                f'<span style="background: #e9ecef; padding: 2px 6px; border-radius: 3px; font-size: 11px;">{tag.name}</span>'
                for tag in tags
            ])
            if obj.tags.count() > 3:
                tag_html += f' <span style="color: #6c757d;">+{obj.tags.count() - 3}</span>'
            return format_html(tag_html)
        return format_html('<span style="color: #999;">—</span>')
    tags_list.short_description = 'Teglar'
    
    def created_at_formatted(self, obj):
        """Format created date"""
        return obj.created_at.strftime('%d.%m.%Y %H:%M')
    created_at_formatted.short_description = 'Yaratilgan'
    created_at_formatted.admin_order_field = 'created_at'
    
    # Actions
    actions = ['activate_products', 'deactivate_products', 'mark_out_of_stock']
    
    def activate_products(self, request, queryset):
        """Activate selected products"""
        updated = queryset.update(status='active')
        self.message_user(
            request,
            f'{updated} ta mahsulot faollashtirildi.',
            level='success'
        )
    activate_products.short_description = 'Tanlangan mahsulotlarni faollashtirish'
    
    def deactivate_products(self, request, queryset):
        """Deactivate selected products"""
        updated = queryset.update(status='inactive')
        self.message_user(
            request,
            f'{updated} ta mahsulot o\'chirildi.',
            level='warning'
        )
    deactivate_products.short_description = 'Tanlangan mahsulotlarni o\'chirish'
    
    def mark_out_of_stock(self, request, queryset):
        """Mark selected products as out of stock"""
        updated = queryset.update(status='out_of_stock')
        self.message_user(
            request,
            f'{updated} ta mahsulot "tugagan" deb belgilandi.',
            level='info'
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
    

