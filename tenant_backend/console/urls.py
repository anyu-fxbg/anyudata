from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.AdminLoginView.as_view(), name='admin-login'),
    path('logout/', views.AdminLogoutView.as_view(), name='admin-logout'),
    path('me/', views.AdminMeView.as_view(), name='admin-me'),
    path('config/', views.ConfigView.as_view(), name='admin-config'),
    path('packages/', views.PackageAdminView.as_view(), name='admin-packages'),
    path('packages/<int:pk>/', views.PackageDetailView.as_view(), name='admin-package-detail'),
    path('test-platform/', views.TestPlatformView.as_view(), name='admin-test-platform'),
    # 订单管理
    path('orders/', views.OrderAdminView.as_view(), name='admin-orders'),
    path('orders/<str:order_no>/', views.OrderDetailView.as_view(), name='admin-order-detail'),
    path('orders/<str:order_no>/action/', views.OrderActionView.as_view(), name='admin-order-action'),
    # 分销管理
    path('distributors/', views.DistributorAdminView.as_view(), name='admin-distributors'),
    path('distributors/<int:pk>/', views.DistributorDetailView.as_view(), name='admin-distributor-detail'),
    path('distributors/<int:pk>/settle/', views.DistributorSettleView.as_view(), name='admin-distributor-settle'),
    # 用户管理
    path('users/', views.CustUserAdminView.as_view(), name='admin-users'),
    path('users/<str:openid>/', views.CustUserDetailView.as_view(), name='admin-user-detail'),
    path('users/<str:openid>/action/', views.CustUserActionView.as_view(), name='admin-user-action'),
]
