from rest_framework import generics, filters
from django_filters.rest_framework import DjangoFilterBackend
from apps.product.models import Product
from apps.product.serializers import ProductSerializer
from apps.product.filters import ProductFilter
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


class ProductListAPIView(generics.ListAPIView):
    
    queryset = (
        Product.objects.all()
        .prefetch_related("images", "tags")
        .select_related("category")
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
    queryset = Product.objects.all().prefetch_related("images", "tags").select_related("category")
    serializer_class = ProductSerializer
    lookup_field = 'slug'

    @swagger_auto_schema(operation_summary="Retrieve product detail")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)