from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from billing.views import RegisterView, custom_logout
from django.conf import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('billing.urls')),
    path('api-auth/', include('rest_framework.urls')),
    
    # Authentication URLs
    path('accounts/login/', auth_views.LoginView.as_view(template_name='billing/login.html'), name='login'),
    path('accounts/logout/', custom_logout, name='logout'),
    path('accounts/register/', RegisterView.as_view(), name='register'),
]
