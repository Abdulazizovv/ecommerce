from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum, Count
from django.urls import reverse
from django.utils.safestring import mark_safe
from apps.order.models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    """Inline admin for OrderItem in Order admin"""
    model = OrderItem
    extra = 0
    readonly_fields = ('get_item_total',)
    fields = ('product', 'quantity', 'item_price', 'get_item_total')
    
    def get_item_total(self, obj):
        """Calculate and display item total price"""
        if obj and obj.item_price and obj.quantity:
            total = float(obj.item_price) * obj.quantity
            return format_html('<strong>{:.2f} so\'m</strong>', total)
        return '-'
    get_item_total.short_description = 'Jami narx'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Advanced admin interface for Order model"""
    
    list_display = (
        'order_id', 
        'user_link', 
        'status_colored', 
        'order_price',
        'created_at_formatted',
        'updated_at'
    )
    
    list_filter = (
        'status', 
        'created_at', 
        'updated_at',
        ('user', admin.RelatedOnlyFieldListFilter),
    )
    
    search_fields = (
        'order_id', 
        'user__email',
        'user__first_name',
        'user__last_name'
    )
    
    readonly_fields = (
        'order_id', 
        'created_at', 
        'updated_at'
    )
    
    fieldsets = (
        ('Buyurtma ma\'lumotlari', {
            'fields': ('order_id', 'user', 'status')
        }),
        ('Moliyaviy ma\'lumotlar', {
            'fields': ('order_price',),
            'classes': ('collapse',)
        }),
        ('Vaqt ma\'lumotlari', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    inlines = [OrderItemInline]
    
    actions = ['mark_as_pending', 'mark_as_completed', 'mark_as_cancelled']
    
    list_per_page = 25
    date_hierarchy = 'created_at'
    
    def user_link(self, obj):
        """Create clickable link to user admin"""
        if obj.user:
            url = reverse('admin:users_user_change', args=[obj.user.pk])
            return format_html('<a href="{}">{}</a>', url, obj.user.email)
        return '-'
    user_link.short_description = 'Foydalanuvchi'

    def status_colored(self, obj):
        """Display status with colors"""
        colors = {
            'new': '#28a745',      # Green
            'pending': '#ffc107',   # Yellow
            'completed': '#007bff', # Blue
            'cancelled': '#dc3545'  # Red
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_colored.short_description = 'Holat'
    
    def items_count(self, obj):
        """Count of items in order"""
        return obj.items.count()
    items_count.short_description = 'Mahsulotlar soni'
    
    def total_amount(self, obj):
        """Calculate total amount of order"""
        if hasattr(obj, 'order_price') and obj.order_price:
            return format_html('<strong>{:.2f} so\'m</strong>', obj.order_price)
        
        # Fallback to calculating from items
        total = 0
        for item in obj.items.all():
            if item.item_price and item.quantity:
                total += item.item_price * item.quantity
        
        return format_html('<strong>{:.2f} so\'m</strong>', total)
    total_amount.short_description = 'Jami summa'
    
    def created_at_formatted(self, obj):
        """Format created_at date"""
        return obj.created_at.strftime('%d.%m.%Y %H:%M')
    created_at_formatted.short_description = 'Yaratilgan vaqt'
    
    # Custom actions
    def mark_as_pending(self, request, queryset):
        """Mark selected orders as pending"""
        updated = queryset.update(status=Order.OrderStatus.PENDING)
        self.message_user(request, '{} ta buyurtma "Jarayonda" holatiga o\'tkazildi.'.format(updated))
    mark_as_pending.short_description = 'Tanlangan buyurtmalarni "Jarayonda" qilish'
    
    def mark_as_completed(self, request, queryset):
        """Mark selected orders as completed"""
        updated = queryset.update(status=Order.OrderStatus.COMPLETED)
        self.message_user(request, '{} ta buyurtma "Yakunlangan" holatiga o\'tkazildi.'.format(updated))
    mark_as_completed.short_description = 'Tanlangan buyurtmalarni "Yakunlangan" qilish'
    
    def mark_as_cancelled(self, request, queryset):
        """Mark selected orders as cancelled"""
        updated = queryset.update(status=Order.OrderStatus.CANCELLED)
        self.message_user(request, '{} ta buyurtma "Bekor qilingan" holatiga o\'tkazildi.'.format(updated))
    mark_as_cancelled.short_description = 'Tanlangan buyurtmalarni "Bekor qilingan" qilish'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('user').prefetch_related('items')


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    """Admin interface for OrderItem model"""
    
    list_display = (
        'order_link',
        'product_link', 
        'quantity', 
        'item_price'
    )
    
    list_filter = (
        'order__status',
        'order__created_at',
        ('product', admin.RelatedOnlyFieldListFilter),
    )
    
    search_fields = (
        'order__order_id',
        'product__name',
        'order__user__email'
    )
    
    readonly_fields = ('total_price',)
    
    fields = ('order', 'product', 'quantity', 'item_price', 'total_price')
    
    list_per_page = 50
    
    def order_link(self, obj):
        """Create clickable link to order admin"""
        url = reverse('admin:order_order_change', args=[obj.order.pk])
        return format_html('<a href="{}">{}</a>', url, obj.order.order_id)
    order_link.short_description = 'Buyurtma'
    
    def product_link(self, obj):
        """Create clickable link to product admin"""
        if obj.product:
            url = reverse('admin:product_product_change', args=[obj.product.pk])
            return format_html('<a href="{}">{}</a>', url, obj.product.name)
        return '-'
    product_link.short_description = 'Mahsulot'
    
    def total_price(self, obj):
        """Calculate total price for this item"""
        if obj and obj.item_price and obj.quantity:
            total = float(obj.item_price) * obj.quantity
            return format_html('<strong>{:.2f} so\'m</strong>', total)
        return '-'
    total_price.short_description = 'Jami narx'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('order', 'product')
