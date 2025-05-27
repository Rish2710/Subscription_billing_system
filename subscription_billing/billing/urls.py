from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    # API ViewSets
    PlanViewSet, SubscriptionViewSet, InvoiceViewSet,
    # JWT Authentication Views
    UserRegistrationAPIView, UserLoginAPIView, UserLogoutAPIView, UserProfileAPIView, api_endpoints,
    # Web Views
    dashboard, PlanListView, subscribe, 
    SubscriptionListView, SubscriptionDetailView, cancel_subscription,
    InvoiceListView, InvoiceDetailView, pay_invoice
)

# API Router
router = DefaultRouter()
router.register(r'plans', PlanViewSet, basename='plan')
router.register(r'subscriptions', SubscriptionViewSet, basename='subscription')
router.register(r'invoices', InvoiceViewSet, basename='invoice')

# URL Patterns
urlpatterns = [
    # API Documentation
    path('api/', api_endpoints, name='api_endpoints'),
    
    # JWT Authentication URLs
    path('api/auth/register/', UserRegistrationAPIView.as_view(), name='api_register'),
    path('api/auth/login/', UserLoginAPIView.as_view(), name='api_login'),
    path('api/auth/logout/', UserLogoutAPIView.as_view(), name='api_logout'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='api_token_refresh'),
    path('api/auth/profile/', UserProfileAPIView.as_view(), name='api_profile'),
    
    # API URLs
    path('api/', include(router.urls)),
    
    # Web URLs
    path('', dashboard, name='dashboard'),
    path('plans/', PlanListView.as_view(), name='plans'),
    path('plans/<int:plan_id>/subscribe/', subscribe, name='subscribe'),
    
    path('subscriptions/', SubscriptionListView.as_view(), name='subscriptions'),
    path('subscriptions/<int:pk>/', SubscriptionDetailView.as_view(), name='subscription_detail'),
    path('subscriptions/<int:subscription_id>/cancel/', cancel_subscription, name='cancel_subscription'),
    
    path('invoices/', InvoiceListView.as_view(), name='invoices'),
    path('invoices/<uuid:uuid>/', InvoiceDetailView.as_view(), name='invoice_detail'),
    path('invoices/<uuid:uuid>/pay/', pay_invoice, name='pay_invoice'),
    
    # Authentication URLs (handled by Django's auth system)
    path('accounts/profile/', dashboard, name='profile'),
] 