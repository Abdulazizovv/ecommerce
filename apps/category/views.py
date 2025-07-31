from django.db.models import Count, Sum, Avg
from rest_framework import generics, status, permissions, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from apps.category.models import Category
from apps.category.serializers import (
    CategoryListSerializer, CategoryDetailSerializer, 
    CategoryCreateUpdateSerializer, CategoryStatsSerializer
)


class CategoryPagination(PageNumberPagination):
    """Custom pagination for categories"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class CategoryListAPIView(generics.ListAPIView):
    """Public category list view"""
    queryset = Category.objects.all().order_by('name')
    serializer_class = CategoryListSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'created_at']
    pagination_class = CategoryPagination
    
    @swagger_auto_schema(
        operation_summary="List categories",
        manual_parameters=[
            openapi.Parameter('search', openapi.IN_QUERY, description="Search by name", type=openapi.TYPE_STRING),
            openapi.Parameter('ordering', openapi.IN_QUERY, description="Order by name or created_at", type=openapi.TYPE_STRING),
            openapi.Parameter('page', openapi.IN_QUERY, description="Page number", type=openapi.TYPE_INTEGER),
            openapi.Parameter('page_size', openapi.IN_QUERY, description="Items per page", type=openapi.TYPE_INTEGER),
        ]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class CategoryDetailAPIView(generics.RetrieveAPIView):
    """Public category detail view"""
    queryset = Category.objects.all()
    serializer_class = CategoryDetailSerializer
    lookup_field = 'slug'
    
    @swagger_auto_schema(operation_summary="Retrieve category detail")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


# ================================
# ADMIN VIEWS
# ================================

class AdminCategoryListCreateAPIView(generics.ListCreateAPIView):
    """Admin category list and create view"""
    queryset = Category.objects.all().order_by('-created_at')
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'created_at']
    pagination_class = CategoryPagination
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CategoryCreateUpdateSerializer
        return CategoryListSerializer
    
    @swagger_auto_schema(
        operation_summary="Admin: List all categories",
        manual_parameters=[
            openapi.Parameter('search', openapi.IN_QUERY, description="Search in name", type=openapi.TYPE_STRING),
            openapi.Parameter('ordering', openapi.IN_QUERY, description="Order by name or created_at", type=openapi.TYPE_STRING),
        ]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Admin: Create new category",
        request_body=CategoryCreateUpdateSerializer,
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class AdminCategoryDetailUpdateDeleteAPIView(generics.RetrieveUpdateDestroyAPIView):
    """Admin category detail, update and delete view"""
    queryset = Category.objects.all()
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    lookup_field = 'id'
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return CategoryCreateUpdateSerializer
        return CategoryDetailSerializer
    
    @swagger_auto_schema(operation_summary="Admin: Get category detail")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Admin: Update category",
        request_body=CategoryCreateUpdateSerializer,
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Admin: Partially update category",
        request_body=CategoryCreateUpdateSerializer,
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)
    
    @swagger_auto_schema(operation_summary="Admin: Delete category")
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)


@swagger_auto_schema(
    method='delete',
    operation_summary="Admin: Bulk delete categories",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'category_ids': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_INTEGER)),
        },
        required=['category_ids']
    )
)
@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated, permissions.IsAdminUser])
def admin_category_bulk_delete(request):
    """Bulk delete categories"""
    category_ids = request.data.get('category_ids', [])
    
    if not category_ids:
        return Response({
            'error': 'category_ids parametri talab qilinadi'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Check if categories have products
    categories_with_products = Category.objects.filter(
        id__in=category_ids,
        products__isnull=False
    ).distinct()
    
    if categories_with_products.exists():
        category_names = [cat.name for cat in categories_with_products]
        return Response({
            'error': f'Quyidagi toifalar mahsulotlarga ega va o\'chirib bo\'lmaydi: {", ".join(category_names)}'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    deleted_count, _ = Category.objects.filter(id__in=category_ids).delete()
    
    return Response({
        'message': f'{deleted_count} ta toifa o\'chirildi',
        'deleted_count': deleted_count
    })


@swagger_auto_schema(
    method='get',
    operation_summary="Admin: Get category statistics",
    responses={200: CategoryStatsSerializer(many=True)}
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated, permissions.IsAdminUser])
def admin_category_statistics(request):
    """Get category statistics for admin"""
    categories = Category.objects.all()
    serializer = CategoryStatsSerializer(categories, many=True)
    
    # Overall stats
    overall_stats = {
        'total_categories': categories.count(),
        'categories_with_products': categories.annotate(
            products_count=Count('products')
        ).filter(products_count__gt=0).count(),
        'empty_categories': categories.annotate(
            products_count=Count('products')
        ).filter(products_count=0).count(),
        'total_products_in_categories': sum(
            cat.products.count() for cat in categories
        ),
    }
    
    return Response({
        'overall_stats': overall_stats,
        'category_details': serializer.data
    })


@swagger_auto_schema(
    method='get',
    operation_summary="Admin: Get products by category",
    manual_parameters=[
        openapi.Parameter('page', openapi.IN_QUERY, description="Page number", type=openapi.TYPE_INTEGER),
        openapi.Parameter('page_size', openapi.IN_QUERY, description="Items per page", type=openapi.TYPE_INTEGER),
    ]
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated, permissions.IsAdminUser])
def admin_category_products(request, category_id):
    """Get products in specific category (Admin only)"""
    try:
        category = Category.objects.get(id=category_id)
    except Category.DoesNotExist:
        return Response({'error': 'Toifa topilmadi'}, status=status.HTTP_404_NOT_FOUND)
    
    from apps.product.serializers import ProductListSerializer
    from django.core.paginator import Paginator
    
    products = category.products.all().select_related('creator').prefetch_related('tags', 'images')
    
    # Pagination
    page_size = request.query_params.get('page_size', 20)
    page_number = request.query_params.get('page', 1)
    
    paginator = Paginator(products, page_size)
    page_obj = paginator.get_page(page_number)
    
    serializer = ProductListSerializer(page_obj, many=True)
    
    return Response({
        'category': {
            'id': category.id,
            'name': category.name,
            'slug': category.slug,
        },
        'products': serializer.data,
        'pagination': {
            'current_page': page_obj.number,
            'total_pages': paginator.num_pages,
            'total_items': paginator.count,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
        }
    })
