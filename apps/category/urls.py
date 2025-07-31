from django.urls import path
from apps.category.views import (
    # Public views
    CategoryListAPIView, CategoryDetailAPIView,
    # Admin views
    AdminCategoryListCreateAPIView, AdminCategoryDetailUpdateDeleteAPIView,
    admin_category_bulk_delete, admin_category_statistics, admin_category_products
)

app_name = 'category'

urlpatterns = [
    # Public URLs
    path('', CategoryListAPIView.as_view(), name='category-list'),
    path('<slug:slug>/', CategoryDetailAPIView.as_view(), name='category-detail'),
    
    # Admin URLs
    path('admin/categories/', AdminCategoryListCreateAPIView.as_view(), name='admin-category-list-create'),
    path('admin/categories/<int:id>/', AdminCategoryDetailUpdateDeleteAPIView.as_view(), name='admin-category-detail'),
    path('admin/categories/bulk-delete/', admin_category_bulk_delete, name='admin-category-bulk-delete'),
    path('admin/categories/statistics/', admin_category_statistics, name='admin-category-statistics'),
    path('admin/categories/<int:category_id>/products/', admin_category_products, name='admin-category-products'),
]
