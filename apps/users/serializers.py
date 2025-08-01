from rest_framework import serializers
from apps.users.models import User as CustomUser
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ("first_name", "last_name", "email", "phone", "password")

    def create(self, validated_data):
        user = CustomUser.objects.create_user(**validated_data)
        return user


class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ["id", "first_name", "last_name", "email", "phone"]


# ================================
# ADMIN USER SERIALIZERS
# ================================

class AdminUserListSerializer(serializers.ModelSerializer):
    """Serializer for admin user list view"""
    full_name = serializers.SerializerMethodField()
    orders_count = serializers.SerializerMethodField()
    total_spent = serializers.SerializerMethodField()
    last_order_date = serializers.SerializerMethodField()
    is_active_display = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomUser
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name', 'phone',
            'is_active', 'is_active_display', 'is_staff', 'is_superuser',
            'last_login', 'orders_count', 'total_spent', 'last_order_date'
        ]
    
    def get_full_name(self, obj):
        """Get user's full name"""
        return f"{obj.first_name} {obj.last_name}".strip() or obj.email
    
    def get_orders_count(self, obj):
        """Get user's total orders count"""
        return getattr(obj, 'orders_count', 0)
    
    def get_total_spent(self, obj):
        """Get user's total spent amount"""
        return getattr(obj, 'total_spent', 0)
    
    def get_last_order_date(self, obj):
        """Get user's last order date"""
        return getattr(obj, 'last_order_date', None)
    
    def get_is_active_display(self, obj):
        """Get user active status display"""
        return "Faol" if obj.is_active else "Nofaol"


class AdminUserDetailSerializer(serializers.ModelSerializer):
    """Serializer for admin user detail view"""
    full_name = serializers.SerializerMethodField()
    orders_count = serializers.SerializerMethodField()
    total_spent = serializers.SerializerMethodField()
    last_order_date = serializers.SerializerMethodField()
    recent_orders = serializers.SerializerMethodField()
    account_stats = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomUser
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name', 'phone',
            'is_active', 'is_staff', 'is_superuser', 'last_login',
            'orders_count', 'total_spent', 'last_order_date', 'recent_orders',
            'account_stats'
        ]
    
    def get_full_name(self, obj):
        """Get user's full name"""
        return f"{obj.first_name} {obj.last_name}".strip() or obj.email
    
    def get_orders_count(self, obj):
        """Get user's total orders count"""
        return obj.orders.count()
    
    def get_total_spent(self, obj):
        """Get user's total spent amount"""
        from apps.order.models import Order
        total = obj.orders.filter(
            status__in=['completed', 'delivered']
        ).aggregate(
            total=models.Sum('order_price')
        )['total']
        return total or 0
    
    def get_last_order_date(self, obj):
        """Get user's last order date"""
        last_order = obj.orders.order_by('-created_at').first()
        return last_order.created_at if last_order else None
    
    def get_recent_orders(self, obj):
        """Get user's recent orders"""
        recent_orders = obj.orders.order_by('-created_at')[:5]
        return [
            {
                'id': order.id,
                'order_id': order.order_id,
                'total_amount': order.order_price,
                'status': order.status,
                'created_at': order.created_at
            }
            for order in recent_orders
        ]
    
    def get_account_stats(self, obj):
        """Get user account statistics"""
        from apps.order.models import Order
        from django.db.models import Sum, Avg
        
        orders = obj.orders.all()
        completed_orders = orders.filter(status__in=['completed', 'delivered'])
        
        # Last 30 days activity
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_orders = orders.filter(created_at__gte=thirty_days_ago)
        
        stats = {
            'total_orders': orders.count(),
            'completed_orders': completed_orders.count(),
            'pending_orders': orders.filter(status='pending').count(),
            'cancelled_orders': orders.filter(status='cancelled').count(),
            'average_order_value': completed_orders.aggregate(
                avg=Avg('order_price')
            )['avg'] or 0,
            'last_30_days_orders': recent_orders.count(),
            'last_30_days_spent': recent_orders.aggregate(
                total=Sum('order_price')
            )['total'] or 0,
            'last_login_days_ago': (timezone.now() - obj.last_login).days if obj.last_login else None
        }
        
        return stats


class AdminUserCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating users (Admin only)"""
    password = serializers.CharField(write_only=True, required=False)
    confirm_password = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = CustomUser
        fields = [
            'email', 'first_name', 'last_name', 'phone',
            'is_active', 'is_staff', 'is_superuser',
            'password', 'confirm_password'
        ]
        extra_kwargs = {
            'email': {'help_text': 'Foydalanuvchi email manzili'},
            'first_name': {'help_text': 'Ism'},
            'last_name': {'help_text': 'Familiya'},
            'phone': {'help_text': 'Telefon raqami'},
            'is_active': {'help_text': 'Foydalanuvchi faol holati'},
            'is_staff': {'help_text': 'Xodim huquqi'},
            'is_superuser': {'help_text': 'Super foydalanuvchi huquqi'},
        }
    
    def validate_email(self, value):
        """Validate email uniqueness"""
        queryset = CustomUser.objects.filter(email=value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        
        if queryset.exists():
            raise serializers.ValidationError("Bu email bilan foydalanuvchi allaqachon mavjud.")
        
        return value
    
    def validate(self, attrs):
        """Cross-field validation"""
        password = attrs.get('password')
        confirm_password = attrs.get('confirm_password')
        
        # Password validation only for create or when password is provided
        if password or (not self.instance and not password):
            if not self.instance and not password:
                raise serializers.ValidationError({
                    'password': 'Yangi foydalanuvchi uchun parol talab qilinadi.'
                })
            
            if password and not confirm_password:
                raise serializers.ValidationError({
                    'confirm_password': 'Parolni tasdiqlash talab qilinadi.'
                })
            
            if password != confirm_password:
                raise serializers.ValidationError({
                    'confirm_password': 'Parollar mos emas.'
                })
            
            # Validate password strength
            if password:
                try:
                    validate_password(password)
                except serializers.ValidationError as e:
                    raise serializers.ValidationError({'password': e.messages})
        
        # Remove confirm_password from validated data
        attrs.pop('confirm_password', None)
        return attrs
    
    def create(self, validated_data):
        """Create user with encrypted password"""
        password = validated_data.pop('password')
        user = CustomUser.objects.create_user(password=password, **validated_data)
        return user
    
    def update(self, instance, validated_data):
        """Update user, handle password separately"""
        password = validated_data.pop('password', None)
        
        # Update other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Update password if provided
        if password:
            instance.set_password(password)
        
        instance.save()
        return instance


class AdminUserStatsSerializer(serializers.Serializer):
    """Serializer for user statistics (Admin only)"""
    user_id = serializers.IntegerField()
    email = serializers.EmailField()
    full_name = serializers.CharField()
    orders_count = serializers.IntegerField()
    total_spent = serializers.DecimalField(max_digits=10, decimal_places=2)
    last_order_date = serializers.DateTimeField(allow_null=True)
    account_age_days = serializers.IntegerField()
    is_active = serializers.BooleanField()


# ================================
# EXISTING SERIALIZERS
# ================================

class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError("Yangi parollar mos emas.")
        return attrs

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Eski parol noto‘g‘ri.")
        return value


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Bu email bilan foydalanuvchi topilmadi.")
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError("Parollar mos emas.")
        return attrs
