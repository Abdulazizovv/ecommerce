from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timedelta
from apps.users.models import User as CustomUser, VerificationCode
from django import forms
from django.contrib.auth.forms import ReadOnlyPasswordHashField


class UserCreationForm(forms.ModelForm):
    """Yangi foydalanuvchi yaratish uchun forma"""
    password1 = forms.CharField(label='Parol', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Parolni tasdiqlang', widget=forms.PasswordInput)

    class Meta:
        model = CustomUser
        fields = ('email', 'first_name', 'last_name', 'phone')

    def clean_password2(self):
        p1 = self.cleaned_data.get("password1")
        p2 = self.cleaned_data.get("password2")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Parollar mos emas")
        return p2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class UserChangeForm(forms.ModelForm):
    """Admin panelda foydalanuvchini yangilash formasi"""
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = CustomUser
        fields = ('email', 'first_name', 'last_name', 'phone', 'password', 'is_active', 'is_staff', 'is_superuser')


class UserAdmin(BaseUserAdmin):
    """Professional User admin interface"""
    form = UserChangeForm
    add_form = UserCreationForm

    list_display = [
        'id', 'email', 'full_name_display', 'phone', 'orders_count',
        'total_spent_display', 'status_display', 'staff_status',
        'last_login_formatted'
    ]
    list_filter = ['is_staff', 'is_superuser', 'is_active', 'last_login']
    search_fields = ['email', 'first_name', 'last_name', 'phone']
    ordering = ['-id']  # Order by ID as proxy for registration order
    list_per_page = 25
    readonly_fields = ['last_login', 'user_statistics']
    
    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('email', 'password', 'first_name', 'last_name', 'phone')
        }),
        ('Ruxsatlar', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Statistika', {
            'fields': ('user_statistics',),
            'classes': ('collapse',)
        }),
        ('Vaqt ma\'lumotlari', {
            'fields': ('last_login',),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'phone', 'password1', 'password2'),
        }),
        ('Ruxsatlar', {
            'classes': ('wide',),
            'fields': ('is_active', 'is_staff', 'is_superuser'),
        }),
    )
    
    filter_horizontal = ('groups', 'user_permissions')
    
    def get_queryset(self, request):
        """Optimize queryset with order statistics"""
        return super().get_queryset(request).annotate(
            orders_count=Count('orders'),
            total_spent=Sum(
                'orders__order_price',
                filter=Q(orders__status__in=['completed', 'delivered'])
            )
        )
    
    def full_name_display(self, obj):
        """Display full name with fallback to email"""
        full_name = f"{obj.first_name} {obj.last_name}".strip()
        if full_name:
            return format_html(
                '<strong>{}</strong><br><small style="color: #666;">{}</small>',
                full_name, obj.email
            )
        return format_html('<strong>{}</strong>', obj.email)
    full_name_display.short_description = 'To\'liq ism'
    
    def orders_count(self, obj):
        """Display orders count with link"""
        count = getattr(obj, 'orders_count', 0)
        if count > 0:
            return format_html(
                '<a href="/admin/order/order/?user__id__exact={}" '
                'style="color: #0066cc; font-weight: bold;">{} ta</a>',
                obj.id, count
            )
        return format_html('<span style="color: #999;">0 ta</span>')
    orders_count.short_description = 'Buyurtmalar'
    orders_count.admin_order_field = 'orders_count'
    
    def total_spent_display(self, obj):
        """Display total spent amount"""
        total = getattr(obj, 'total_spent', 0) or 0
        if total > 0:
            return format_html(
                '<span style="color: #28a745; font-weight: bold;">{:,.0f} so\'m</span>',
                total
            )
        return format_html('<span style="color: #999;">0 so\'m</span>')
    total_spent_display.short_description = 'Jami sarflagan'
    total_spent_display.admin_order_field = 'total_spent'
    
    def status_display(self, obj):
        """Display user status with colors"""
        if obj.is_active:
            return format_html(
                '<span style="color: #28a745; font-weight: bold;">● Faol</span>'
            )
        return format_html(
            '<span style="color: #dc3545; font-weight: bold;">● Nofaol</span>'
        )
    status_display.short_description = 'Holat'
    status_display.admin_order_field = 'is_active'
    
    def staff_status(self, obj):
        """Display staff and superuser status"""
        status_parts = []
        
        if obj.is_superuser:
            status_parts.append('<span style="color: #dc3545; font-weight: bold;">SUPER</span>')
        elif obj.is_staff:
            status_parts.append('<span style="color: #0066cc; font-weight: bold;">XODIM</span>')
        else:
            status_parts.append('<span style="color: #6c757d;">Mijoz</span>')
        
        return format_html(' '.join(status_parts))
    staff_status.short_description = 'Rol'
    
    def date_joined_formatted(self, obj):
        """Format registration date - using ID as proxy"""
        # Since we don't have date_joined, we'll show user ID as registration order
        return f"ID: {obj.id}"
    date_joined_formatted.short_description = 'Ro\'yxat ID'
    date_joined_formatted.admin_order_field = 'id'
    
    def last_login_formatted(self, obj):
        """Format last login date"""
        if obj.last_login:
            return obj.last_login.strftime('%d.%m.%Y %H:%M')
        return format_html('<span style="color: #999;">Hech qachon</span>')
    last_login_formatted.short_description = 'Oxirgi kirish'
    last_login_formatted.admin_order_field = 'last_login'
    
    def user_statistics(self, obj):
        """Display detailed user statistics"""
        from apps.order.models import Order
        
        # Get orders statistics
        orders = obj.orders.all()
        completed_orders = orders.filter(status__in=['completed', 'delivered'])
        pending_orders = orders.filter(status='pending')
        cancelled_orders = orders.filter(status='cancelled')
        
        # Calculate totals
        total_orders = orders.count()
        total_spent = completed_orders.aggregate(
            total=Sum('order_price')
        )['total'] or 0
        
        # Last 30 days activity
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_orders = orders.filter(created_at__gte=thirty_days_ago)
        recent_spent = recent_orders.aggregate(
            total=Sum('order_price')
        )['total'] or 0
        
        # Account age - estimate using user ID
        account_age = f"ID raqami: {obj.id}"
        
        html = f"""
        <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; max-width: 500px;">
            <h4 style="margin-top: 0; color: #333;">Foydalanuvchi statistikasi</h4>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 10px;">
                <div>
                    <strong>Buyurtmalar:</strong><br>
                    <span style="color: #28a745;">✓ Yakunlangan: {completed_orders.count()}</span><br>
                    <span style="color: #ffc107;">⏳ Kutilmoqda: {pending_orders.count()}</span><br>
                    <span style="color: #dc3545;">✗ Bekor qilingan: {cancelled_orders.count()}</span><br>
                    <strong>Jami: {total_orders}</strong>
                </div>
                <div>
                    <strong>Moliyaviy:</strong><br>
                    <span>Jami: {total_spent:,.0f} so'm</span><br>
                    <span>Oxirgi 30 kun: {recent_spent:,.0f} so'm</span><br>
                    <span>O'rtacha: {(total_spent / max(completed_orders.count(), 1)):,.0f} so'm</span>
                </div>
            </div>
            
            <div style="border-top: 1px solid #ddd; padding-top: 10px;">
                <strong>Hisob ma'lumotlari:</strong><br>
                <span>{account_age}</span><br>
                <span>Oxirgi 30 kundagi buyurtmalar: {recent_orders.count()}</span>
            </div>
        </div>
        """
        return format_html(html)
    user_statistics.short_description = 'Tafsiliy statistika'
    
    # Actions
    actions = ['activate_users', 'deactivate_users', 'make_staff', 'remove_staff']
    
    def activate_users(self, request, queryset):
        """Activate selected users"""
        updated = queryset.update(is_active=True)
        self.message_user(
            request,
            f'{updated} ta foydalanuvchi faollashtirildi.',
            level='success'
        )
    activate_users.short_description = 'Tanlangan foydalanuvchilarni faollashtirish'
    
    def deactivate_users(self, request, queryset):
        """Deactivate selected users (except superusers and self)"""
        # Don't deactivate superusers or self
        queryset = queryset.exclude(is_superuser=True).exclude(id=request.user.id)
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            f'{updated} ta foydalanuvchi o\'chirildi.',
            level='warning'
        )
    deactivate_users.short_description = 'Tanlangan foydalanuvchilarni o\'chirish'
    
    def make_staff(self, request, queryset):
        """Make selected users staff"""
        updated = queryset.update(is_staff=True)
        self.message_user(
            request,
            f'{updated} ta foydalanuvchi xodim qilindi.',
            level='info'
        )
    make_staff.short_description = 'Tanlangan foydalanuvchilarni xodim qilish'
    
    def remove_staff(self, request, queryset):
        """Remove staff status from selected users (except superusers and self)"""
        queryset = queryset.exclude(is_superuser=True).exclude(id=request.user.id)
        updated = queryset.update(is_staff=False)
        self.message_user(
            request,
            f'{updated} ta foydalanuvchidan xodim huquqi olib tashlandi.',
            level='info'
        )
    remove_staff.short_description = 'Tanlangan foydalanuvchilardan xodim huquqini olish'


@admin.register(VerificationCode)
class VerificationCodeAdmin(admin.ModelAdmin):
    """Verification Code admin"""
    list_display = ['email', 'code', 'created_at', 'is_expired']
    list_filter = ['created_at']
    search_fields = ['email', 'code']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
    
    def is_expired(self, obj):
        """Check if verification code is expired"""
        from datetime import timedelta
        expiry_time = obj.created_at + timedelta(minutes=15)  # 15 minutes expiry
        is_expired = timezone.now() > expiry_time
        
        if is_expired:
            return format_html('<span style="color: #dc3545;">Muddati o\'tgan</span>')
        return format_html('<span style="color: #28a745;">Faol</span>')
    is_expired.short_description = 'Holat'


admin.site.register(CustomUser, UserAdmin)
