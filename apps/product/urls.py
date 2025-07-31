from django.urls import path
from apps.product.views import (
    # Public views
    ProductListAPIView, ProductDetailAPIView,
    # Admin views
    AdminProductListCreateAPIView, AdminProductDetailUpdateDeleteAPIView,
    AdminProductImagesAPIView, admin_product_bulk_update_status,
    admin_product_bulk_delete, admin_product_statistics
)

app_name = 'product'

urlpatterns = [
    # Public URLs
    path('', ProductListAPIView.as_view(), name='product-list'),
    path('<slug:slug>/', ProductDetailAPIView.as_view(), name='product-detail'),
    
    # Admin URLs
    path('admin/products/', AdminProductListCreateAPIView.as_view(), name='admin-product-list-create'),
    path('admin/products/<int:id>/', AdminProductDetailUpdateDeleteAPIView.as_view(), name='admin-product-detail'),
    path('admin/products/<int:product_id>/images/', AdminProductImagesAPIView.as_view(), name='admin-product-images'),
    path('admin/products/<int:product_id>/images/<int:image_id>/', AdminProductImagesAPIView.as_view(), name='admin-product-image-delete'),
    path('admin/products/bulk-update-status/', admin_product_bulk_update_status, name='admin-product-bulk-status'),
    path('admin/products/bulk-delete/', admin_product_bulk_delete, name='admin-product-bulk-delete'),
    path('admin/products/statistics/', admin_product_statistics, name='admin-product-statistics'),
]
