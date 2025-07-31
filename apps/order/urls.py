from django.urls import path
from . import views

app_name = 'order'

urlpatterns = [
    # User buyurtmalar API'lari
    path('', views.OrderListCreateAPIView.as_view(), name='order-list-create'),
    path('<str:order_id>/', views.OrderDetailAPIView.as_view(), name='order-detail'),
    path('confirm/', views.confirm_order, name='order-confirm'),
    path('history/', views.OrderHistoryAPIView.as_view(), name='order-history'),
    path('statistics/', views.order_statistics, name='order-statistics'),
    path('search/', views.OrderSearchAPIView.as_view(), name='order-search'),
    
    # Admin buyurtmalar API'lari
    path('admin/all/', views.AdminOrderListAPIView.as_view(), name='admin-order-list'),
    path('admin/<str:order_id>/', views.AdminOrderDetailAPIView.as_view(), name='admin-order-detail'),
    path('admin/<str:order_id>/status/', views.OrderStatusUpdateAPIView.as_view(), name='admin-order-status-update'),
    path('admin/statistics/', views.admin_statistics, name='admin-statistics'),
]
