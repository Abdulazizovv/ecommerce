# from django.urls import path
# from . import views

# app_name = 'order'

# urlpatterns = [
#     # Buyurtmalar CRUD
#     path('', views.OrderListCreateAPIView.as_view(), name='order-list-create'),
#     path('<str:order_id>/', views.OrderDetailAPIView.as_view(), name='order-detail'),
#     path('<str:order_id>/status/', views.OrderStatusUpdateAPIView.as_view(), name='order-status-update'),
    
#     # Buyurtma tasdiqlash
#     path('confirm/', views.confirm_order, name='order-confirm'),
    
#     # Buyurtmalar tarixi va statistika
#     path('history/', views.OrderHistoryAPIView.as_view(), name='order-history'),
#     path('statistics/', views.order_statistics, name='order-statistics'),
    
#     # Qidiruv
#     path('search/', views.OrderSearchAPIView.as_view(), name='order-search'),
# ]
