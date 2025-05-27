from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.views.generic import ListView, DetailView, View, CreateView
from django.urls import reverse, reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from datetime import timedelta
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, logout
from django.http import Http404

from .models import Plan, Subscription, Invoice
from .serializers import (
    PlanSerializer, 
    SubscriptionSerializer, 
    InvoiceSerializer,
    PayInvoiceSerializer,
    UserRegistrationSerializer,
    UserLoginSerializer,
    TokenResponseSerializer,
    UserSerializer
)
from .utils import send_subscription_confirmation_email, send_payment_confirmation_email
from .forms import CustomUserCreationForm

# REST API Views
class PlanViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint to view available subscription plans
    Public access - no authentication required
    """
    queryset = Plan.objects.all()
    serializer_class = PlanSerializer
    permission_classes = [permissions.AllowAny]

class SubscriptionViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing user subscriptions
    """
    serializer_class = SubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Users can only see their own subscriptions
        return Subscription.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        # Set the user to the current user
        subscription = serializer.save(user=self.request.user)
        
        # Create an initial invoice for the subscription
        invoice = Invoice.objects.create(
            user=subscription.user,
            subscription=subscription,
            email=subscription.user.email,
            amount=subscription.plan.price,
            issue_date=subscription.start_date,
            due_date=subscription.start_date + timedelta(days=15),
            status='pending'
        )
        
        # Send confirmation email
        send_subscription_confirmation_email(subscription)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Cancel a subscription
        """
        subscription = self.get_object()
        
        if subscription.status != 'active':
            return Response(
                {"detail": "Only active subscriptions can be cancelled."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        subscription.status = 'cancelled'
        subscription.save()
        
        return Response(
            {"detail": "Subscription cancelled successfully."},
            status=status.HTTP_200_OK
        )

class InvoiceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for viewing invoices
    """
    serializer_class = InvoiceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Users can only see their own invoices
        return Invoice.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def pending(self, request):
        """
        Get all pending invoices
        """
        pending_invoices = Invoice.objects.filter(
            user=request.user,
            status='pending'
        )
        serializer = self.get_serializer(pending_invoices, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def pay(self, request, pk=None):
        """
        Mark an invoice as paid
        """
        invoice = self.get_object()
        
        if invoice.status == 'paid':
            return Response(
                {"detail": "This invoice is already paid."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        invoice.status = 'paid'
        invoice.save()
        
        # Send payment confirmation email
        send_payment_confirmation_email(invoice)
        
        return Response(
            {"detail": "Invoice marked as paid successfully."},
            status=status.HTTP_200_OK
        )

# Web Views
@login_required
def dashboard(request):
    active_subscriptions = Subscription.objects.filter(
        user=request.user,
        status='active',
        end_date__gte=timezone.now().date()
    )
    
    pending_invoices = Invoice.objects.filter(
        user=request.user,
        status='pending'
    )
    
    overdue_invoices = Invoice.objects.filter(
        user=request.user,
        status='overdue'
    )
    
    recent_invoices = Invoice.objects.filter(
        user=request.user
    ).order_by('-issue_date')[:5]
    
    context = {
        'active_subscriptions': active_subscriptions,
        'active_subscriptions_count': active_subscriptions.count(),
        'pending_invoices_count': pending_invoices.count(),
        'overdue_invoices_count': overdue_invoices.count(),
        'recent_invoices': recent_invoices,
    }
    
    return render(request, 'billing/dashboard.html', context)

class PlanListView(ListView):
    model = Plan
    template_name = 'billing/plans.html'
    context_object_name = 'plans'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add any additional context here if needed
        return context

@login_required
def subscribe(request, plan_id):
    plan = get_object_or_404(Plan, id=plan_id)
    
    if request.method == 'POST':
        start_date = request.POST.get('start_date')
        if not start_date:
            start_date = timezone.now().date()
        else:
            start_date = timezone.datetime.strptime(start_date, '%Y-%m-%d').date()
        
        end_date = start_date + timedelta(days=30)
        
        # Create a new subscription
        subscription = Subscription.objects.create(
            user=request.user,
            email=request.user.email,
            plan=plan,
            start_date=start_date,
            end_date=end_date,
            status='active'
        )
        
        # Create an initial invoice
        invoice = Invoice.objects.create(
            user=request.user,
            subscription=subscription,
            email=request.user.email,
            amount=plan.price,
            issue_date=start_date,
            due_date=start_date + timedelta(days=15),
            status='pending'
        )
        
        # Send confirmation email
        send_subscription_confirmation_email(subscription)
        
        messages.success(request, f'You have successfully subscribed to the {plan.get_name_display()} plan. Check your email for confirmation.')
        return redirect('dashboard')
    
    context = {
        'plan': plan,
        'today': timezone.now().date()
    }
    
    return render(request, 'billing/subscribe.html', context)

class SubscriptionListView(LoginRequiredMixin, ListView):
    model = Subscription
    template_name = 'billing/subscriptions.html'
    context_object_name = 'subscriptions'
    
    def get_queryset(self):
        return Subscription.objects.filter(user=self.request.user)

class SubscriptionDetailView(LoginRequiredMixin, DetailView):
    model = Subscription
    template_name = 'billing/subscription_detail.html'
    context_object_name = 'subscription'
    
    def get_queryset(self):
        return Subscription.objects.filter(user=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['invoices'] = Invoice.objects.filter(
            subscription=self.object
        ).order_by('-issue_date')
        return context

@login_required
def cancel_subscription(request, subscription_id):
    subscription = get_object_or_404(Subscription, id=subscription_id, user=request.user)
    
    if subscription.status != 'active':
        messages.error(request, 'Only active subscriptions can be cancelled.')
        return redirect('subscription_detail', pk=subscription_id)
    
    if request.method == 'POST':
        subscription.status = 'cancelled'
        subscription.save()
        
        messages.success(request, 'Your subscription has been cancelled.')
        return redirect('subscriptions')
    
    return render(request, 'billing/cancel_subscription.html', {'subscription': subscription})

class InvoiceListView(LoginRequiredMixin, ListView):
    model = Invoice
    template_name = 'billing/invoices.html'
    context_object_name = 'invoices'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = Invoice.objects.filter(user=self.request.user)
        status = self.request.GET.get('status')
        
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset.order_by('-issue_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status'] = self.request.GET.get('status')
        return context

class InvoiceDetailView(LoginRequiredMixin, DetailView):
    model = Invoice
    template_name = 'billing/invoice_detail.html'
    context_object_name = 'invoice'
    
    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()
        
        uuid = self.kwargs.get('uuid')
        if uuid is None:
            raise AttributeError("InvoiceDetailView must be called with a uuid.")
        
        try:
            obj = queryset.get(uuid=uuid)
        except Invoice.DoesNotExist:
            raise Http404("Invoice not found.")
        
        return obj
    
    def get_queryset(self):
        return Invoice.objects.filter(user=self.request.user)

@login_required
def pay_invoice(request, uuid):
    invoice = get_object_or_404(Invoice, uuid=uuid, user=request.user)
    
    if invoice.status == 'paid':
        messages.error(request, 'This invoice is already paid.')
        return redirect('invoice_detail', uuid=uuid)
    
    if request.method == 'POST':
        # In a real application, you would process the payment here
        invoice.status = 'paid'
        invoice.save()
        
        # Send payment confirmation email
        send_payment_confirmation_email(invoice)
        
        messages.success(request, 'Your payment has been processed successfully. A confirmation email has been sent.')
        return redirect('invoice_detail', uuid=uuid)
    
    return render(request, 'billing/pay_invoice.html', {'invoice': invoice})

# Authentication Views
class RegisterView(CreateView):
    template_name = 'billing/register.html'
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('dashboard')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        # Log the user in after registration
        login(self.request, self.object)
        messages.success(self.request, 'Your account has been created successfully!')
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

def custom_logout(request):
    """
    Custom logout view to ensure proper logout behavior
    """
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('/')

# JWT Authentication API Views
class UserRegistrationAPIView(APIView):
    """
    API endpoint for user registration
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            
            response_data = {
                'user': user,
                'access': str(refresh.access_token),
                'refresh': str(refresh)
            }
            
            response_serializer = TokenResponseSerializer(response_data)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserLoginAPIView(APIView):
    """
    API endpoint for user login
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)
            
            response_data = {
                'user': user,
                'access': str(refresh.access_token),
                'refresh': str(refresh)
            }
            
            response_serializer = TokenResponseSerializer(response_data)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserLogoutAPIView(APIView):
    """
    API endpoint for user logout (blacklist refresh token)
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
                return Response({'detail': 'Successfully logged out'}, status=status.HTTP_200_OK)
            else:
                return Response({'detail': 'Refresh token required'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'detail': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)

class UserProfileAPIView(APIView):
    """
    API endpoint to get current user profile
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

@api_view(['GET'])
@permission_classes([AllowAny])
def api_endpoints(request):
    """
    API endpoint documentation
    """
    endpoints = {
        'authentication': {
            'register': '/api/auth/register/',
            'login': '/api/auth/login/',
            'logout': '/api/auth/logout/',
            'refresh': '/api/auth/token/refresh/',
            'profile': '/api/auth/profile/',
        },
        'billing': {
            'plans': '/api/plans/',
            'subscriptions': '/api/subscriptions/',
            'subscribe': '/api/subscriptions/ (POST)',
            'cancel_subscription': '/api/subscriptions/{id}/cancel/ (POST)',
            'invoices': '/api/invoices/',
            'pending_invoices': '/api/invoices/pending/',
            'pay_invoice': '/api/invoices/{id}/pay/ (POST)',
        },
        'authentication_header': 'Authorization: Bearer <access_token>',
        'example_usage': {
            'login': {
                'method': 'POST',
                'url': '/api/auth/login/',
                'data': {
                    'username': 'your_username',
                    'password': 'your_password'
                }
            },
            'access_protected_endpoint': {
                'method': 'GET',
                'url': '/api/plans/',
                'headers': {
                    'Authorization': 'Bearer <access_token_from_login>'
                }
            }
        }
    }
    return Response(endpoints)
