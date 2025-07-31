from rest_framework import generics, status, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Sum, Count
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import Order, OrderItem
from .serializers import (
    OrderListSerializer, 
    OrderDetailSerializer, 
    OrderCreateSerializer, 
    OrderStatusUpdateSerializer,
    OrderConfirmSerializer
)
from .filters import OrderFilter
from core.pagination import CustomPageNumberPagination


class OrderListCreateAPIView(generics.ListCreateAPIView):
    """
    GET: Foydalanuvchining buyurtmalar ro'yxatini olish
    POST: Yangi buyurtma yaratish (cartdan)
    """
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPageNumberPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_class = OrderFilter
    ordering_fields = ['created_at', 'updated_at', 'order_price', 'order_id']
    ordering = ['-created_at']
    search_fields = ['order_id', 'items__product__name']
    
    def get_queryset(self):
        """Faqat foydalanuvchining buyurtmalarini qaytarish"""
        return Order.objects.filter(
            user=self.request.user
        ).select_related('user').prefetch_related(
            'items__product__images',
            'items__product__category'
        )
    
    def get_serializer_class(self):
        """POST uchun create serializer, GET uchun list serializer"""
        if self.request.method == 'POST':
            return OrderCreateSerializer
        return OrderListSerializer
    
    @swagger_auto_schema(
        operation_summary="Buyurtmalar ro'yxati",
        operation_description="Foydalanuvchining buyurtmalari ro'yxati. Filtrlash va qidiruv imkoniyatlari bilan.",
        manual_parameters=[
            openapi.Parameter('status', openapi.IN_QUERY, description="Buyurtma holati (new, pending, completed, cancelled)", type=openapi.TYPE_STRING),
            openapi.Parameter('created_date_from', openapi.IN_QUERY, description="Boshlanish sanasi (YYYY-MM-DD)", type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE),
            openapi.Parameter('created_date_to', openapi.IN_QUERY, description="Tugash sanasi (YYYY-MM-DD)", type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE),
            openapi.Parameter('price_min', openapi.IN_QUERY, description="Minimal narx", type=openapi.TYPE_NUMBER),
            openapi.Parameter('price_max', openapi.IN_QUERY, description="Maksimal narx", type=openapi.TYPE_NUMBER),
            openapi.Parameter('order_id', openapi.IN_QUERY, description="Order ID bo'yicha qidirish", type=openapi.TYPE_STRING),
            openapi.Parameter('product_name', openapi.IN_QUERY, description="Mahsulot nomi bo'yicha qidirish", type=openapi.TYPE_STRING),
            openapi.Parameter('ordering', openapi.IN_QUERY, description="Tartiblash (-created_at, order_price, etc.)", type=openapi.TYPE_STRING),
            openapi.Parameter('search', openapi.IN_QUERY, description="Umumiy qidiruv", type=openapi.TYPE_STRING),
        ]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Yangi buyurtma yaratish",
        operation_description="Foydalanuvchining cartidan yangi buyurtma yaratish",
        request_body=OrderCreateSerializer,
        responses={
            201: openapi.Response(
                description="Buyurtma muvaffaqiyatli yaratildi",
                examples={
                    "application/json": {
                        "success": True,
                        "message": "Buyurtma muvaffaqiyatli yaratildi.",
                        "order_id": "20250731-000001",
                        "order_detail_url": "/api/orders/20250731-000001/",
                        "status": "Yangi"
                    }
                }
            ),
            400: "Xatolik yuz berdi"
        }
    )
    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)
    
    def create(self, request, *args, **kwargs):
        """Custom create method to return proper response"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            # Create the order
            order = serializer.save()
            
            return Response({
                'success': True,
                'message': 'Buyurtma muvaffaqiyatli yaratildi.',
                'order_id': order.order_id,
                'order_detail_url': f'/api/orders/{order.order_id}/',
                'status': order.get_status_display(),
                'total_amount': float(order.order_price)
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Buyurtma yaratishda xatolik: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)


class OrderDetailAPIView(generics.RetrieveAPIView):
    """Buyurtma tafsilotlarini ko'rish"""
    permission_classes = [IsAuthenticated]
    serializer_class = OrderDetailSerializer
    lookup_field = 'order_id'
    
    def get_queryset(self):
        """Faqat foydalanuvchining buyurtmalarini qaytarish"""
        return Order.objects.filter(
            user=self.request.user
        ).select_related('user').prefetch_related(
            'items__product__images',
            'items__product__category'
        )
    
    @swagger_auto_schema(
        operation_summary="Buyurtma tafsilotlari",
        operation_description="Buyurtmaning to'liq ma'lumotlarini ko'rish (foydalanuvchi uchun)"
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class AdminOrderListAPIView(generics.ListAPIView):
    """
    Admin uchun barcha buyurtmalar ro'yxati
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    serializer_class = OrderListSerializer
    pagination_class = CustomPageNumberPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_class = OrderFilter
    ordering_fields = ['created_at', 'updated_at', 'order_price', 'order_id']
    ordering = ['-created_at']
    search_fields = ['order_id', 'user__username', 'user__email', 'items__product__name']
    
    def get_queryset(self):
        """Barcha buyurtmalar (admin uchun)"""
        return Order.objects.select_related('user').prefetch_related(
            'items__product__images',
            'items__product__category'
        )
    
    @swagger_auto_schema(
        operation_summary="Barcha buyurtmalar (Admin)",
        operation_description="Admin uchun barcha buyurtmalar ro'yxati. Filtrlash va qidiruv imkoniyatlari bilan.",
        manual_parameters=[
            openapi.Parameter('status', openapi.IN_QUERY, description="Buyurtma holati", type=openapi.TYPE_STRING),
            openapi.Parameter('created_date_from', openapi.IN_QUERY, description="Boshlanish sanasi", type=openapi.TYPE_STRING),
            openapi.Parameter('created_date_to', openapi.IN_QUERY, description="Tugash sanasi", type=openapi.TYPE_STRING),
            openapi.Parameter('price_min', openapi.IN_QUERY, description="Minimal narx", type=openapi.TYPE_NUMBER),
            openapi.Parameter('price_max', openapi.IN_QUERY, description="Maksimal narx", type=openapi.TYPE_NUMBER),
            openapi.Parameter('search', openapi.IN_QUERY, description="User, order ID yoki mahsulot bo'yicha qidirish", type=openapi.TYPE_STRING),
        ]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class AdminOrderDetailAPIView(generics.RetrieveAPIView):
    """Admin uchun buyurtma tafsilotlari"""
    permission_classes = [IsAuthenticated, IsAdminUser]
    serializer_class = OrderDetailSerializer
    lookup_field = 'order_id'
    
    def get_queryset(self):
        """Barcha buyurtmalar (admin uchun)"""
        return Order.objects.select_related('user').prefetch_related(
            'items__product__images',
            'items__product__category'
        )
    
    @swagger_auto_schema(
        operation_summary="Buyurtma tafsilotlari (Admin)",
        operation_description="Admin uchun buyurtmaning to'liq ma'lumotlarini ko'rish"
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class OrderStatusUpdateAPIView(generics.UpdateAPIView):
    """Buyurtma holatini o'zgartirish (faqat admin)"""
    permission_classes = [IsAuthenticated, IsAdminUser]
    serializer_class = OrderStatusUpdateSerializer
    lookup_field = 'order_id'
    http_method_names = ['patch', 'put']
    
    def get_queryset(self):
        """Barcha buyurtmalar (admin uchun)"""
        return Order.objects.select_related('user').prefetch_related('items__product')
    
    @swagger_auto_schema(
        operation_summary="Buyurtma holatini o'zgartirish",
        operation_description="Admin foydalanuvchilari uchun buyurtma holatini o'zgartirish",
        request_body=OrderStatusUpdateSerializer,
        responses={
            200: openapi.Response(
                description="Holat muvaffaqiyatli o'zgartirildi",
                examples={
                    "application/json": {
                        "success": True,
                        "message": "Buyurtma holati muvaffaqiyatli o'zgartirildi.",
                        "order_id": "20250731-000001",
                        "old_status": "Yangi",
                        "new_status": "Jarayonda"
                    }
                }
            )
        }
    )
    def patch(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        """Custom update method"""
        instance = self.get_object()
        old_status = instance.get_status_display()
        
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        try:
            updated_order = serializer.save()
            
            return Response({
                'success': True,
                'message': 'Buyurtma holati muvaffaqiyatli o\'zgartirildi.',
                'order_id': updated_order.order_id,
                'old_status': old_status,
                'new_status': updated_order.get_status_display(),
                'updated_at': updated_order.updated_at
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Holat o\'zgartirishda xatolik: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    method='post',
    operation_summary="Buyurtmani tasdiqlash",
    operation_description="Buyurtmani 'new' holatdan 'pending' holatiga o'tkazish",
    request_body=OrderConfirmSerializer,
    responses={
        200: openapi.Response(
            description="Buyurtma tasdiqlandi",
            examples={
                "application/json": {
                    "success": True,
                    "message": "Buyurtma muvaffaqiyatli tasdiqlandi.",
                    "order_id": "20250731-000001",
                    "status": "Jarayonda"
                }
            }
        ),
        400: "Xatolik yuz berdi"
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def confirm_order(request):
    """
    Buyurtmani tasdiqlash
    POST /api/orders/confirm/
    Body: {"order_id": "20250731-000001"}
    """
    serializer = OrderConfirmSerializer(data=request.data, context={'request': request})
    
    if serializer.is_valid():
        try:
            order = serializer.save()
            
            return Response({
                'success': True,
                'message': 'Buyurtma muvaffaqiyatli tasdiqlandi.',
                'order_id': order.order_id,
                'status': order.get_status_display(),
                'updated_at': order.updated_at
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Buyurtmani tasdiqlashda xatolik: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    return Response({
        'success': False,
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


class OrderHistoryAPIView(generics.ListAPIView):
    """
    Foydalanuvchining buyurtmalar tarixi
    GET /api/orders/history/
    """
    permission_classes = [IsAuthenticated]
    serializer_class = OrderListSerializer
    pagination_class = CustomPageNumberPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = OrderFilter
    ordering_fields = ['created_at', 'updated_at', 'order_price']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Foydalanuvchining buyurtmalar tarixi"""
        return Order.objects.filter(
            user=self.request.user
        ).select_related('user').prefetch_related(
            'items__product__images'
        )
    
    @swagger_auto_schema(
        operation_summary="Buyurtmalar tarixi",
        operation_description="Foydalanuvchining barcha buyurtmalar tarixi",
        manual_parameters=[
            openapi.Parameter('status', openapi.IN_QUERY, description="Holat bo'yicha filtrlash", type=openapi.TYPE_STRING),
            openapi.Parameter('created_date_from', openapi.IN_QUERY, description="Boshlanish sanasi", type=openapi.TYPE_STRING),
            openapi.Parameter('created_date_to', openapi.IN_QUERY, description="Tugash sanasi", type=openapi.TYPE_STRING),
        ]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


@swagger_auto_schema(
    method='get',
    operation_summary="Buyurtma statistikasi",
    operation_description="Foydalanuvchining buyurtma statistikalari",
    responses={
        200: openapi.Response(
            description="Statistika ma'lumotlari",
            examples={
                "application/json": {
                    "success": True,
                    "statistics": {
                        "total_orders": 10,
                        "new_orders": 2,
                        "pending_orders": 3,
                        "completed_orders": 4,
                        "cancelled_orders": 1,
                        "total_spent": 1250.00,
                        "average_order_value": 125.00
                    }
                }
            }
        )
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def order_statistics(request):
    """
    Foydalanuvchining buyurtma statistikasi
    GET /api/orders/statistics/
    """
    user_orders = Order.objects.filter(user=request.user)
    
    # Aggregate statistics
    total_orders = user_orders.count()
    total_spent = user_orders.aggregate(
        total=Sum('order_price')
    )['total'] or 0
    
    stats = {
        'total_orders': total_orders,
        'new_orders': user_orders.filter(status=Order.OrderStatus.NEW).count(),
        'pending_orders': user_orders.filter(status=Order.OrderStatus.PENDING).count(),
        'completed_orders': user_orders.filter(status=Order.OrderStatus.COMPLETED).count(),
        'cancelled_orders': user_orders.filter(status=Order.OrderStatus.CANCELLED).count(),
        'total_spent': float(total_spent),
        'average_order_value': float(total_spent / total_orders) if total_orders > 0 else 0,
    }
    
    return Response({
        'success': True,
        'statistics': stats
    })


@swagger_auto_schema(
    method='get',
    operation_summary="Admin statistika",
    operation_description="Admin uchun umumiy buyurtma statistikalari",
    responses={
        200: openapi.Response(
            description="Admin statistika ma'lumotlari",
            examples={
                "application/json": {
                    "success": True,
                    "statistics": {
                        "total_orders": 150,
                        "total_users": 50,
                        "total_revenue": 25000.00,
                        "orders_by_status": {
                            "new": 20,
                            "pending": 30,
                            "completed": 80,
                            "cancelled": 20
                        }
                    }
                }
            }
        )
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def admin_statistics(request):
    """
    Admin uchun umumiy statistika
    GET /api/orders/admin/statistics/
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    all_orders = Order.objects.all()
    total_revenue = all_orders.aggregate(
        total=Sum('order_price')
    )['total'] or 0
    
    stats = {
        'total_orders': all_orders.count(),
        'total_users': User.objects.count(),
        'total_revenue': float(total_revenue),
        'orders_by_status': {
            'new': all_orders.filter(status=Order.OrderStatus.NEW).count(),
            'pending': all_orders.filter(status=Order.OrderStatus.PENDING).count(),
            'completed': all_orders.filter(status=Order.OrderStatus.COMPLETED).count(),
            'cancelled': all_orders.filter(status=Order.OrderStatus.CANCELLED).count(),
        },
        'average_order_value': float(total_revenue / all_orders.count()) if all_orders.count() > 0 else 0,
    }
    
    return Response({
        'success': True,
        'statistics': stats
    })


class OrderSearchAPIView(generics.ListAPIView):
    """
    Buyurtmalarni qidirish
    GET /api/orders/search/
    """
    permission_classes = [IsAuthenticated]
    serializer_class = OrderListSerializer
    pagination_class = CustomPageNumberPagination
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['order_id', 'items__product__name', 'status']
    filterset_class = OrderFilter
    
    def get_queryset(self):
        """Qidiruv uchun queryset"""
        return Order.objects.filter(
            user=self.request.user
        ).select_related('user').prefetch_related(
            'items__product'
        )
    
    @swagger_auto_schema(
        operation_summary="Buyurtmalarni qidirish",
        operation_description="Buyurtmalarni order_id, mahsulot nomi yoki holat bo'yicha qidirish",
        manual_parameters=[
            openapi.Parameter('search', openapi.IN_QUERY, description="Qidiruv so'zi", type=openapi.TYPE_STRING, required=True),
            openapi.Parameter('status', openapi.IN_QUERY, description="Holat bo'yicha filtrlash", type=openapi.TYPE_STRING),
        ]
    )
    def get(self, request, *args, **kwargs):
        search_query = request.GET.get('search', '').strip()
        
        if not search_query:
            return Response({
                'success': False,
                'message': 'Qidiruv so\'zi kiritilmagan.',
                'results': []
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return super().get(request, *args, **kwargs)
