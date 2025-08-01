from django.urls import path
from apps.users.views import (
    # Public views
    RegisterView, UserMeView, PasswordChangeView,
    PasswordResetRequestView, PasswordResetConfirmView,
    # Admin views
    AdminUserListCreateAPIView, AdminUserDetailUpdateDeleteAPIView,
    admin_user_bulk_update_status, admin_user_bulk_delete,
    admin_user_statistics, admin_user_orders
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    # Public URLs
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("me/", UserMeView.as_view(), name="me"),
    path("password/change/", PasswordChangeView.as_view(), name="change_password"),
    path("password/reset/request/", PasswordResetRequestView.as_view(), name="password_reset_request"),
    path("password/reset/confirm/", PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    
    # Admin URLs
    path("admin/users/", AdminUserListCreateAPIView.as_view(), name="admin-user-list-create"),
    path("admin/users/<int:id>/", AdminUserDetailUpdateDeleteAPIView.as_view(), name="admin-user-detail"),
    path("admin/users/bulk-update-status/", admin_user_bulk_update_status, name="admin-user-bulk-status"),
    path("admin/users/bulk-delete/", admin_user_bulk_delete, name="admin-user-bulk-delete"),
    path("admin/users/statistics/", admin_user_statistics, name="admin-user-statistics"),
    path("admin/users/<int:user_id>/orders/", admin_user_orders, name="admin-user-orders"),
]
