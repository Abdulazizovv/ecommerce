from rest_framework import serializers
from django.db import transaction
from django.shortcuts import get_object_or_404
from .models import Order, OrderItem
from apps.cart.models import Cart, CartItem
from apps.product.serializers import ProductSerializer
from apps.users.serializers import CustomUserSerializer as UserSerializer


class OrderItemSerializer(serializers.ModelSerializer):
    """Serializer for OrderItem model"""
    product = ProductSerializer(read_only=True)
    total_price = serializers.SerializerMethodField()
    
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'quantity', 'item_price', 'total_price']
        read_only_fields = ['id', 'item_price', 'total_price']
    
    def get_total_price(self, obj):
        """Calculate total price for this item"""
        if obj.item_price and obj.quantity:
            return float(obj.item_price * obj.quantity)
        return 0.0


class OrderListSerializer(serializers.ModelSerializer):
    """Serializer for Order list view"""
    user = UserSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    items_count = serializers.SerializerMethodField()
    total_amount = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_id', 'user', 'status', 'status_display', 
            'items_count', 'total_amount', 'order_price', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'order_id', 'order_price', 'created_at', 'updated_at']
    
    def get_items_count(self, obj):
        """Get count of items in order"""
        return obj.items.count()
    
    def get_total_amount(self, obj):
        """Calculate total amount of order"""
        return obj.total_price


class OrderDetailSerializer(serializers.ModelSerializer):
    """Serializer for Order detail view"""
    user = UserSerializer(read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    total_amount = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_id', 'user', 'status', 'status_display',
            'items', 'total_amount', 'order_price',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'order_id', 'user', 'order_price', 'created_at', 'updated_at']
    
    def get_total_amount(self, obj):
        """Calculate total amount of order"""
        return obj.total_price


class OrderCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new order from cart"""
    
    class Meta:
        model = Order
        fields = ['status']
        extra_kwargs = {
            'status': {'default': Order.OrderStatus.NEW}
        }
    
    def create(self, validated_data):
        """Create order from user's cart"""
        user = self.context['request'].user
        
        # Get user's cart
        try:
            cart = Cart.objects.get(user=user)
        except Cart.DoesNotExist:
            raise serializers.ValidationError("Savatingizda mahsulot yo'q.")
        
        # Check if cart has items
        cart_items = cart.items.all()
        if not cart_items.exists():
            raise serializers.ValidationError("Savatingizda mahsulot yo'q.")
        
        # Create order with transaction
        with transaction.atomic():
            # Create order first
            order = Order.objects.create(
                user=user,
                status=validated_data.get('status', Order.OrderStatus.NEW),
                order_price=0  # Temporarily set to 0
            )
            
            # Now create order items (order has primary key now)
            order_items = []
            total_price = 0
            
            for cart_item in cart_items:
                # Check product availability (status based)
                if cart_item.product.status != cart_item.product.ProductStatus.AVAILABLE:
                    raise serializers.ValidationError(
                        f"{cart_item.product.name} mahsuloti mavjud emas."
                    )
                
                # Create order item
                order_item = OrderItem(
                    order=order,
                    product=cart_item.product,
                    quantity=cart_item.quantity,
                    item_price=cart_item.product.final_price
                )
                order_items.append(order_item)
                total_price += order_item.item_price * order_item.quantity
            
            # Bulk create order items
            OrderItem.objects.bulk_create(order_items)
            
            # Update order total price
            order.order_price = total_price
            order.save()
            
            # Clear cart after successful order creation
            cart.items.all().delete()
        
        return order


class OrderStatusUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating order status"""
    
    class Meta:
        model = Order
        fields = ['status']
    
    def validate_status(self, value):
        """Validate status transition"""
        instance = self.instance
        
        if instance:
            current_status = instance.status
            
            # Define allowed status transitions
            allowed_transitions = {
                Order.OrderStatus.NEW: [Order.OrderStatus.PENDING, Order.OrderStatus.CANCELLED],
                Order.OrderStatus.PENDING: [Order.OrderStatus.COMPLETED, Order.OrderStatus.CANCELLED],
                Order.OrderStatus.COMPLETED: [],  # Cannot change from completed
                Order.OrderStatus.CANCELLED: []   # Cannot change from cancelled
            }
            
            if value not in allowed_transitions.get(current_status, []):
                raise serializers.ValidationError(
                    f"Status '{current_status}' dan '{value}' ga o'zgartirib bo'lmaydi."
                )
        
        return value


class OrderConfirmSerializer(serializers.Serializer):
    """Serializer for confirming order"""
    order_id = serializers.CharField()
    
    def validate_order_id(self, value):
        """Validate order exists and belongs to user"""
        user = self.context['request'].user
        
        try:
            order = Order.objects.get(order_id=value, user=user)
        except Order.DoesNotExist:
            raise serializers.ValidationError("Buyurtma topilmadi.")
        
        if order.status != Order.OrderStatus.NEW:
            raise serializers.ValidationError("Faqat 'Yangi' holatdagi buyurtmalarni tasdiqlash mumkin.")
        
        return value
    
    def save(self):
        """Confirm the order"""
        order_id = self.validated_data['order_id']
        user = self.context['request'].user
        
        order = Order.objects.get(order_id=order_id, user=user)
        order.status = Order.OrderStatus.PENDING
        order.save()
        
        return order
