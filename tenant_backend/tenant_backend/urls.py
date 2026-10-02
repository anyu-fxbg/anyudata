from django.urls import path, include

urlpatterns = [
    path('api/', include('core.urls')),
    path('api/admin/', include('console.urls')),
]
