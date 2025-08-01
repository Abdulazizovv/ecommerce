from django.db.models import Count, Sum, Q, Avg
from django.utils import timezone
from datetime import timedelta
from rest_framework import generics, status, permissions, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.core.mail import send_mail
from django.conf import settings
import random

from apps.users.models import User, VerificationCode
from apps.users.serializers import (
    RegisterSerializer, CustomUserSerializer, PasswordChangeSerializer,
    PasswordResetRequestSerializer, PasswordResetConfirmSerializer,
    # Admin serializers
    AdminUserListSerializer, AdminUserDetailSerializer,
    AdminUserCreateUpdateSerializer, AdminUserStatsSerializer
)


class UserPagination(PageNumberPagination):
    """Custom pagination for users"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]


class UserMeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = CustomUserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class PasswordChangeView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Parolni o'zgartirish",
        operation_description="""Foydalanuvchi eski parolini va yangi parolini yuboradi.
Agar eski parol to'g'ri bo'lsa, yangi parol o'rnatiladi.""",
        request_body=PasswordChangeSerializer,
        responses={200: "Parol muvaffaqiyatli o‘zgartirildi", 400: "Noto‘g‘ri so‘rov"},
    )
    def post(self, request):
        serializer = PasswordChangeSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        user = request.user
        user.set_password(serializer.validated_data["new_password"])
        user.save()

        return Response(
            {"message": "Parol muvaffaqiyatli o‘zgartirildi"}, status=status.HTTP_200_OK
        )


# Parol tiklash so'rovi
class PasswordResetRequestView(APIView):

    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="Parolni tiklashni so'rash",
        operation_description="""
Foydalanuvchi email manzilini yuboradi.
Tizim ushbu emailga tasdiqlash kodini yuboradi.
Keyingi bosqichda ushbu kod orqali yangi parol o'rnatish mumkin bo'ladi.
""",
        request_body=PasswordResetRequestSerializer,
        responses={200: "Kod yuborildi", 400: "Email noto‘g‘ri yoki mavjud emas"},
    )
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        user = User.objects.get(email=email)

        # Tasdiqlash kodi yaratish va saqlash
        code = str(random.randint(100000, 999999))
        VerificationCode.objects.update_or_create(email=email, defaults={"code": code})

        # Email yuborish
        send_mail(
            subject="Parolni tiklash tasdiqlash kodi",
            message=f"Sizning parolni tiklash tasdiqlash kodingiz: {code}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
        )

        return Response(
            {"message": "Tasdiqlash kodi yuborildi"}, status=status.HTTP_200_OK
        )


class PasswordResetConfirmView(APIView):

    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="Parolni yangilash",
        operation_description="""
Foydalanuvchi tasdiqlash kodi (`code`) yordamida yangi parolni o‘rnatadi.

Agar yuborilgan ma’lumotlar to‘g‘ri bo‘lsa, foydalanuvchining paroli yangilanadi.
""",
        request_body=PasswordResetConfirmSerializer,
        responses={
            200: "Parol muvaffaqiyatli yangilandi",
            400: "Kod yoki token noto‘g‘ri",
        },
    )
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        code = serializer.validated_data["code"]
        new_password = serializer.validated_data["new_password"]

        # Tasdiqlash kodini tekshirish
        try:
            verification = VerificationCode.objects.get(email=email, code=code)
        except VerificationCode.DoesNotExist:
            return Response(
                {"error": "Noto‘g‘ri tasdiqlash kodi"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = User.objects.get(email=email)
        user.set_password(new_password)
        user.save()

        # Tasdiqlash kodini o‘chirish
        verification.delete()

        return Response(
            {"message": "Parol muvaffaqiyatli yangilandi"}, status=status.HTTP_200_OK
        )


# ================================
# ADMIN VIEWS
# ================================

class AdminUserListCreateAPIView(generics.ListCreateAPIView):
    """Admin user list and create view"""
    queryset = User.objects.all().order_by('-last_login')
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['email', 'first_name', 'last_name', 'phone']
    ordering_fields = ['email', 'first_name', 'last_name', 'last_login']
    ordering = ['-last_login']
    pagination_class = UserPagination
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AdminUserCreateUpdateSerializer
        return AdminUserListSerializer
    
    def get_queryset(self):
        """Optimize queryset with order statistics"""
        queryset = super().get_queryset()
        
        # Add filters
        is_active = self.request.query_params.get('is_active')
        is_staff = self.request.query_params.get('is_staff')
        
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        if is_staff is not None:
            queryset = queryset.filter(is_staff=is_staff.lower() == 'true')
        
        # Annotate with order statistics
        from apps.order.models import Order
        from django.db import models
        queryset = queryset.annotate(
            orders_count=Count('orders'),
            total_spent=Sum(
                'orders__order_price',
                filter=Q(orders__status__in=['completed', 'delivered'])
            ),
            last_order_date=models.Max('orders__created_at')
        )
        
        return queryset
    
    @swagger_auto_schema(
        operation_summary="Admin: List all users",
        manual_parameters=[
            openapi.Parameter('search', openapi.IN_QUERY, description="Search in email, name, phone", type=openapi.TYPE_STRING),
            openapi.Parameter('is_active', openapi.IN_QUERY, description="Filter by active status", type=openapi.TYPE_BOOLEAN),
            openapi.Parameter('is_staff', openapi.IN_QUERY, description="Filter by staff status", type=openapi.TYPE_BOOLEAN),
            openapi.Parameter('ordering', openapi.IN_QUERY, description="Order by field", type=openapi.TYPE_STRING),
        ]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Admin: Create new user",
        request_body=AdminUserCreateUpdateSerializer,
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class AdminUserDetailUpdateDeleteAPIView(generics.RetrieveUpdateDestroyAPIView):
    """Admin user detail, update and delete view"""
    queryset = User.objects.all()
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    lookup_field = 'id'
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return AdminUserCreateUpdateSerializer
        return AdminUserDetailSerializer
    
    @swagger_auto_schema(operation_summary="Admin: Get user detail")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Admin: Update user",
        request_body=AdminUserCreateUpdateSerializer,
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Admin: Partially update user",
        request_body=AdminUserCreateUpdateSerializer,
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)
    
    @swagger_auto_schema(operation_summary="Admin: Delete user")
    def delete(self, request, *args, **kwargs):
        # Don't allow deleting superusers or self
        user = self.get_object()
        if user.is_superuser:
            return Response({
                'error': 'Super foydalanuvchini o\'chirib bo\'lmaydi'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if user == request.user:
            return Response({
                'error': 'O\'z hisobingizni o\'chirib bo\'lmaydi'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return super().delete(request, *args, **kwargs)


@swagger_auto_schema(
    method='post',
    operation_summary="Admin: Bulk update user status",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'user_ids': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_INTEGER)),
            'is_active': openapi.Schema(type=openapi.TYPE_BOOLEAN),
        },
        required=['user_ids', 'is_active']
    )
)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated, permissions.IsAdminUser])
def admin_user_bulk_update_status(request):
    """Bulk update user active status"""
    user_ids = request.data.get('user_ids', [])
    is_active = request.data.get('is_active')
    
    if not user_ids or is_active is None:
        return Response({
            'error': 'user_ids va is_active parametrlari talab qilinadi'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Don't allow deactivating superusers or self
    users_to_update = User.objects.filter(id__in=user_ids)
    
    if not is_active:
        # Check for superusers
        superusers = users_to_update.filter(is_superuser=True)
        if superusers.exists():
            return Response({
                'error': 'Super foydalanuvchilarni o\'chirib bo\'lmaydi'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if trying to deactivate self
        if request.user.id in user_ids:
            return Response({
                'error': 'O\'z hisobingizni o\'chirib bo\'lmaydi'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    updated_count = users_to_update.update(is_active=is_active)
    status_text = "faollashtirildi" if is_active else "o'chirildi"
    
    return Response({
        'message': f'{updated_count} ta foydalanuvchi {status_text}',
        'updated_count': updated_count
    })


@swagger_auto_schema(
    method='delete',
    operation_summary="Admin: Bulk delete users",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'user_ids': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_INTEGER)),
        },
        required=['user_ids']
    )
)
@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated, permissions.IsAdminUser])
def admin_user_bulk_delete(request):
    """Bulk delete users"""
    user_ids = request.data.get('user_ids', [])
    
    if not user_ids:
        return Response({
            'error': 'user_ids parametri talab qilinadi'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    users_to_delete = User.objects.filter(id__in=user_ids)
    
    # Check for superusers
    superusers = users_to_delete.filter(is_superuser=True)
    if superusers.exists():
        return Response({
            'error': 'Super foydalanuvchilarni o\'chirib bo\'lmaydi'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Check if trying to delete self
    if request.user.id in user_ids:
        return Response({
            'error': 'O\'z hisobingizni o\'chirib bo\'lmaydi'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    deleted_count, _ = users_to_delete.delete()
    
    return Response({
        'message': f'{deleted_count} ta foydalanuvchi o\'chirildi',
        'deleted_count': deleted_count
    })


@swagger_auto_schema(
    method='get',
    operation_summary="Admin: Get user statistics",
    responses={200: openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'total_users': openapi.Schema(type=openapi.TYPE_INTEGER),
            'active_users': openapi.Schema(type=openapi.TYPE_INTEGER),
            'inactive_users': openapi.Schema(type=openapi.TYPE_INTEGER),
            'staff_users': openapi.Schema(type=openapi.TYPE_INTEGER),
            'superusers': openapi.Schema(type=openapi.TYPE_INTEGER),
            'users_with_orders': openapi.Schema(type=openapi.TYPE_INTEGER),
            'new_users_last_30_days': openapi.Schema(type=openapi.TYPE_INTEGER),
            'top_customers': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT)),
        }
    )}
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated, permissions.IsAdminUser])
def admin_user_statistics(request):
    """Get user statistics for admin"""
    from apps.order.models import Order
    
    # Basic stats
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    staff_users = User.objects.filter(is_staff=True).count()
    superusers = User.objects.filter(is_superuser=True).count()
    
    # Users with orders
    users_with_orders = User.objects.filter(orders__isnull=False).distinct().count()
    
    # New users in last 30 days - count by ID creation order as proxy
    thirty_days_ago = timezone.now() - timedelta(days=30)
    # Since we don't have date_joined, we'll estimate using last_login and user ID
    recent_user_ids = User.objects.filter(
        last_login__gte=thirty_days_ago
    ).values_list('id', flat=True)
    # Get highest ID from 30 days ago as rough estimate
    estimated_start_id = User.objects.order_by('-id').first().id - 1000  # rough estimate
    new_users_last_30_days = User.objects.filter(id__gt=estimated_start_id).count()
    
    # Top customers by total spent
    top_customers = User.objects.annotate(
        total_spent=Sum(
            'orders__order_price',
            filter=Q(orders__status__in=['completed', 'delivered'])
        ),
        orders_count=Count('orders')
    ).filter(
        total_spent__isnull=False
    ).order_by('-total_spent')[:10]
    
    top_customers_data = [
        {
            'id': user.id,
            'email': user.email,
            'full_name': f"{user.first_name} {user.last_name}".strip() or user.email,
            'total_spent': user.total_spent or 0,
            'orders_count': user.orders_count,
        }
        for user in top_customers
    ]
    
    # Recent registrations - order by ID as proxy for registration order
    recent_users = User.objects.order_by('-id')[:5]
    recent_users_data = [
        {
            'id': user.id,
            'email': user.email,
            'full_name': f"{user.first_name} {user.last_name}".strip() or user.email,
            'last_login': user.last_login,
            'is_active': user.is_active,
        }
        for user in recent_users
    ]
    
    stats = {
        'total_users': total_users,
        'active_users': active_users,
        'inactive_users': total_users - active_users,
        'staff_users': staff_users,
        'superusers': superusers,
        'users_with_orders': users_with_orders,
        'new_users_last_30_days': new_users_last_30_days,
        'top_customers': top_customers_data,
        'recent_users': recent_users_data,
    }
    
    return Response(stats)


@swagger_auto_schema(
    method='get',
    operation_summary="Admin: Get user orders",
    manual_parameters=[
        openapi.Parameter('page', openapi.IN_QUERY, description="Page number", type=openapi.TYPE_INTEGER),
        openapi.Parameter('page_size', openapi.IN_QUERY, description="Items per page", type=openapi.TYPE_INTEGER),
    ]
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated, permissions.IsAdminUser])
def admin_user_orders(request, user_id):
    """Get orders for specific user (Admin only)"""
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({'error': 'Foydalanuvchi topilmadi'}, status=status.HTTP_404_NOT_FOUND)
    
    from apps.order.serializers import OrderListSerializer
    from django.core.paginator import Paginator
    
    orders = user.orders.all().select_related('user').prefetch_related('items__product').order_by('-created_at')
    
    # Pagination
    page_size = request.query_params.get('page_size', 20)
    page_number = request.query_params.get('page', 1)
    
    paginator = Paginator(orders, page_size)
    page_obj = paginator.get_page(page_number)
    
    serializer = OrderListSerializer(page_obj, many=True)
    
    return Response({
        'user': {
            'id': user.id,
            'email': user.email,
            'full_name': f"{user.first_name} {user.last_name}".strip() or user.email,
        },
        'orders': serializer.data,
        'pagination': {
            'current_page': page_obj.number,
            'total_pages': paginator.num_pages,
            'total_items': paginator.count,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
        }
    })
