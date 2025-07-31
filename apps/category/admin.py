from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count
from apps.category.models import Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Professional Category admin interface"""
    list_display = [
        'id', 'name', 'slug', 'products_count', 
        'created_at_formatted', 'updated_at_formatted'
    ]
    list_filter = ['created_at', 'updated_at']
    search_fields = ['name', 'slug']
    readonly_fields = ['slug', 'created_at', 'updated_at', 'products_count_detailed']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['name']
    
    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('name', 'slug')
        }),
        ('Statistika', {
            'fields': ('products_count_detailed',),
            'classes': ('collapse',)
        }),
        ('Vaqt ma\'lumotlari', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queryset with product count"""
        return super().get_queryset(request).annotate(
            product_count=Count('products')
        )
    
    def products_count(self, obj):
        """Display products count with link"""
        count = getattr(obj, 'product_count', obj.products.count())
        if count > 0:
            return format_html(
                '<a href="/admin/product/product/?category__id__exact={}" '
                'style="color: #0066cc; font-weight: bold;">{} ta</a>',
                obj.id, count
            )
        return format_html('<span style="color: #999;">0 ta</span>')
    products_count.short_description = 'Mahsulotlar soni'
    products_count.admin_order_field = 'product_count'
    
    def products_count_detailed(self, obj):
        """Detailed products count information"""
        from apps.product.models import Product
        
        total = obj.products.count()
        active = obj.products.filter(status='active').count()
        inactive = obj.products.filter(status='inactive').count()
        out_of_stock = obj.products.filter(status='out_of_stock').count()
        
        html = f"""
        <div style="background: #f8f9fa; padding: 10px; border-radius: 5px;">
            <strong>Mahsulotlar statistikasi:</strong><br>
            <span style="color: #28a745;">✓ Faol: {active} ta</span><br>
            <span style="color: #6c757d;">⏸ Nofaol: {inactive} ta</span><br>
            <span style="color: #dc3545;">✗ Tugagan: {out_of_stock} ta</span><br>
            <strong>Jami: {total} ta</strong>
        </div>
        """
        return format_html(html)
    products_count_detailed.short_description = 'Mahsulotlar tafsiloti'
    
    def created_at_formatted(self, obj):
        """Format created date"""
        return obj.created_at.strftime('%d.%m.%Y %H:%M')
    created_at_formatted.short_description = 'Yaratilgan vaqt'
    created_at_formatted.admin_order_field = 'created_at'
    
    def updated_at_formatted(self, obj):
        """Format updated date"""
        return obj.updated_at.strftime('%d.%m.%Y %H:%M')
    updated_at_formatted.short_description = 'Yangilangan vaqt'
    updated_at_formatted.admin_order_field = 'updated_at'
    
    # Actions
    actions = ['activate_categories', 'export_categories']
    
    def activate_categories(self, request, queryset):
        """Custom action example - could be used for future functionality"""
        count = queryset.count()
        self.message_user(
            request, 
            f'{count} ta toifa tanlandi. (Bu action misol uchun)',
            level='success'
        )
    activate_categories.short_description = 'Tanlangan toifalarni faollashtirish'
    
    def export_categories(self, request, queryset):
        """Export categories action"""
        count = queryset.count()
        self.message_user(
            request,
            f'{count} ta toifa eksport uchun tanlandi. (Bu action misol uchun)',
            level='info'
        )
    export_categories.short_description = 'Tanlangan toifalarni eksport qilish'
    list_filter = ["name"]
