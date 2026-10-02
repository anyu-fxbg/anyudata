from django.urls import path
from . import views

urlpatterns = [
    path('brand/', views.BrandView.as_view(), name='brand'),
    path('packages/', views.PackagesView.as_view(), name='packages'),
    path('order/create/', views.OrderCreateView.as_view(), name='order-create'),
    path('order/<str:order_no>/report/', views.OrderReportView.as_view(), name='order-report'),
    path('wechat/notify/', views.WechatNotifyView.as_view(), name='wechat-notify'),
    path('wechat/oauth/start/', views.WechatOauthStartView.as_view(), name='oauth-start'),
    path('wechat/oauth/callback/', views.WechatOauthCallbackView.as_view(), name='oauth-callback'),
    path('order/<str:order_no>/mock-pay/', views.MockPayView.as_view(), name='mock-pay'),
]
