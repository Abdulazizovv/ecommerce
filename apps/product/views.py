from django.db.models import Q, Count, Avg, Sum
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status, permissions, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from apps.product.models import Product, ProductImage
from apps.product.serializers import (
    ProductListSerializer, ProductDetailSerializer, ProductCreateUpdateSerializer,
    ProductImageCreateSerializer, ProductImageSerializer, ProductSerializer
)
from apps.product.filters import ProductFilter
from apps.category.models import Category


class ProductPagination(PageNumberPagination):
    """Custom pagination for products"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class ProductListAPIView(generics.ListAPIView):
    """Public product list view"""
    queryset = (
        Product.objects.filter(status='active')
        .prefetch_related("images", "tags")
        .select_related("category", "creator")
    )
    serializer_class = ProductSerializer
    filter_backends = [
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    ]
    filterset_class = ProductFilter
    ordering_fields = ["price", "name", "created_at"]
    search_fields = ["name", "description"]
    pagination_class = ProductPagination
    
    @swagger_auto_schema(
        operation_summary="List products",
        manual_parameters=[
            openapi.Parameter('price_min', openapi.IN_QUERY, description="Minimum price", type=openapi.TYPE_NUMBER),
            openapi.Parameter('price_max', openapi.IN_QUERY, description="Maximum price", type=openapi.TYPE_NUMBER),
            openapi.Parameter('category', openapi.IN_QUERY, description="Category slug", type=openapi.TYPE_STRING),
            openapi.Parameter('tags', openapi.IN_QUERY, description="Tag name (partial match)", type=openapi.TYPE_STRING),
            openapi.Parameter('search', openapi.IN_QUERY, description="Search by name or description", type=openapi.TYPE_STRING),
            openapi.Parameter('ordering', openapi.IN_QUERY, description="Order by price, name, or created_at", type=openapi.TYPE_STRING),
            openapi.Parameter('page', openapi.IN_QUERY, description="Page number", type=openapi.TYPE_INTEGER),
            openapi.Parameter('page_size', openapi.IN_QUERY, description="Items per page", type=openapi.TYPE_INTEGER),
        ]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class ProductDetailAPIView(generics.RetrieveAPIView):
    """Public product detail view"""
    queryset = Product.objects.filter(status='active').prefetch_related("images", "tags").select_related("category", "creator")
    serializer_class = ProductDetailSerializer
    lookup_field = 'slug'

    @swagger_auto_schema(operation_summary="Retrieve product detail")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


# ================================
# ADMIN VIEWS
# ================================

class AdminProductListCreateAPIView(generics.ListCreateAPIView):
    """Admin product list and create view"""
    queryset = Product.objects.all().select_related('category', 'creator').prefetch_related('tags', 'images')
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ['name', 'description', 'creator__email']
    ordering_fields = ['name', 'price', 'status', 'created_at']
    ordering = ['-created_at']
    pagination_class = ProductPagination
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ProductCreateUpdateSerializer
        return ProductListSerializer
    
    @swagger_auto_schema(
        operation_summary="Admin: List all products",
        manual_parameters=[
            openapi.Parameter('search', openapi.IN_QUERY, description="Search in name, description, creator email", type=openapi.TYPE_STRING),
            openapi.Parameter('status', openapi.IN_QUERY, description="Filter by status", type=openapi.TYPE_STRING),
            openapi.Parameter('category', openapi.IN_QUERY, description="Filter by category", type=openapi.TYPE_STRING),
        ]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Admin: Create new product",
        request_body=ProductCreateUpdateSerializer,
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class AdminProductDetailUpdateDeleteAPIView(generics.RetrieveUpdateDestroyAPIView):
    """Admin product detail, update and delete view"""
    queryset = Product.objects.all().select_related('category', 'creator').prefetch_related('tags', 'images')
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    lookup_field = 'id'
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return ProductCreateUpdateSerializer
        return ProductDetailSerializer
    
    @swagger_auto_schema(operation_summary="Admin: Get product detail")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Admin: Update product",
        request_body=ProductCreateUpdateSerializer,
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="Admin: Partially update product",
        request_body=ProductCreateUpdateSerializer,
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)
    
    @swagger_auto_schema(operation_summary="Admin: Delete product")
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)


class AdminProductImagesAPIView(APIView):
    """Admin product images management"""
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    parser_classes = [MultiPartParser, FormParser]
    
    @swagger_auto_schema(
        operation_summary="Admin: Get product images",
        responses={200: ProductImageSerializer(many=True)}
    )
    def get(self, request, product_id):
        """Get all images for product"""
        try:
            product = Product.objects.get(id=product_id)
            images = product.images.all()
            serializer = ProductImageSerializer(images, many=True)
            return Response(serializer.data)
        except Product.DoesNotExist:
            return Response({'error': 'Mahsulot topilmadi'}, status=status.HTTP_404_NOT_FOUND)
    
    @swagger_auto_schema(
        operation_summary="Admin: Add image to product",
        request_body=ProductImageCreateSerializer,
        responses={201: ProductImageSerializer}
    )
    def post(self, request, product_id):
        """Add new image to product"""
        try:
            product = Product.objects.get(id=product_id)
            serializer = ProductImageCreateSerializer(
                data=request.data, 
                context={'product_id': product_id}
            )
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Product.DoesNotExist:
            return Response({'error': 'Mahsulot topilmadi'}, status=status.HTTP_404_NOT_FOUND)
    
    @swagger_auto_schema(
        operation_summary="Admin: Delete product image(s)",
        manual_parameters=[
            openapi.Parameter('image_id', openapi.IN_PATH, description="Specific image ID to delete (optional)", type=openapi.TYPE_INTEGER),
        ]
    )
    def delete(self, request, product_id, image_id=None):
        """Delete product image"""
        try:
            product = Product.objects.get(id=product_id)
            if image_id:
                # Delete specific image
                try:
                    image = product.images.get(id=image_id)
                    image.delete()
                    return Response({'message': 'Rasm o\'chirildi'}, status=status.HTTP_200_OK)
                except ProductImage.DoesNotExist:
                    return Response({'error': 'Rasm topilmadi'}, status=status.HTTP_404_NOT_FOUND)
            else:
                # Delete all images
                product.images.all().delete()
                return Response({'message': 'Barcha rasmlar o\'chirildi'}, status=status.HTTP_200_OK)
        except Product.DoesNotExist:
            return Response({'error': 'Mahsulot topilmadi'}, status=status.HTTP_404_NOT_FOUND)


@swagger_auto_schema(
    method='post',
    operation_summary="Admin: Bulk update product status",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'product_ids': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_INTEGER)),
            'status': openapi.Schema(type=openapi.TYPE_STRING, enum=['active', 'inactive', 'out_of_stock']),
        },
        required=['product_ids', 'status']
    )
)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated, permissions.IsAdminUser])
def admin_product_bulk_update_status(request):
    """Bulk update product status"""
    product_ids = request.data.get('product_ids', [])
    new_status = request.data.get('status')
    
    if not product_ids or not new_status:
        return Response({
            'error': 'product_ids va status parametrlari talab qilinadi'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if new_status not in ['active', 'inactive', 'out_of_stock']:
        return Response({
            'error': 'Noto\'g\'ri status. Faqat active, inactive, out_of_stock qabul qilinadi'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    updated_count = Product.objects.filter(id__in=product_ids).update(status=new_status)
    
    return Response({
        'message': f'{updated_count} ta mahsulot statusi yangilandi',
        'updated_count': updated_count
    })


@swagger_auto_schema(
    method='delete',
    operation_summary="Admin: Bulk delete products",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'product_ids': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_INTEGER)),
        },
        required=['product_ids']
    )
)
@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated, permissions.IsAdminUser])
def admin_product_bulk_delete(request):
    """Bulk delete products"""
    product_ids = request.data.get('product_ids', [])
    
    if not product_ids:
        return Response({
            'error': 'product_ids parametri talab qilinadi'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    deleted_count, _ = Product.objects.filter(id__in=product_ids).delete()
    
    return Response({
        'message': f'{deleted_count} ta mahsulot o\'chirildi',
        'deleted_count': deleted_count
    })


@swagger_auto_schema(
    method='get',
    operation_summary="Admin: Get product statistics",
    responses={200: openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'total_products': openapi.Schema(type=openapi.TYPE_INTEGER),
            'active_products': openapi.Schema(type=openapi.TYPE_INTEGER),
            'inactive_products': openapi.Schema(type=openapi.TYPE_INTEGER),
            'out_of_stock_products': openapi.Schema(type=openapi.TYPE_INTEGER),
            'average_product_price': openapi.Schema(type=openapi.TYPE_NUMBER),
            'total_products_value': openapi.Schema(type=openapi.TYPE_NUMBER),
            'top_categories': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT)),
            'recent_products': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT)),
        }
    )}
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated, permissions.IsAdminUser])
def admin_product_statistics(request):
    """Get product statistics for admin"""
    stats = {
        'total_products': Product.objects.count(),
        'active_products': Product.objects.filter(status='active').count(),
        'inactive_products': Product.objects.filter(status='inactive').count(),
        'out_of_stock_products': Product.objects.filter(status='out_of_stock').count(),
        'categories_with_products': Category.objects.annotate(
            products_count=Count('products')
        ).filter(products_count__gt=0).count(),
        'total_categories': Category.objects.count(),
        'average_product_price': Product.objects.aggregate(
            avg_price=Avg('price')
        )['avg_price'] or 0,
        'total_products_value': Product.objects.aggregate(
            total_value=Sum('price')
        )['total_value'] or 0,
    }
    
    # Top categories by products count
    top_categories = Category.objects.annotate(
        products_count=Count('products')
    ).order_by('-products_count')[:5]
    
    stats['top_categories'] = [
        {
            'id': cat.id,
            'name': cat.name,
            'products_count': cat.products_count
        }
        for cat in top_categories
    ]
    
    # Recent products
    recent_products = Product.objects.select_related('category', 'creator').order_by('-created_at')[:5]
    stats['recent_products'] = [
        {
            'id': prod.id,
            'name': prod.name,
            'price': prod.price,
            'status': prod.status,
            'category': prod.category.name if prod.category else None,
            'creator': prod.creator.email if prod.creator else None,
            'created_at': prod.created_at
        }
        for prod in recent_products
    ]
    
    return Response(stats)