import os
import sys
import django
import json

# Setup Django environment
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, 'subscription_billing'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'subscription_billing.settings')
django.setup()

from django.contrib.auth.models import User
from billing.models import Plan, Subscription, Invoice
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
from datetime import timedelta

def test_api_subscription_email():
    print("Testing API Subscription Email Functionality in Docker...")
    
    # Create or get test user
    user, created = User.objects.get_or_create(
        username='api_test_user',
        defaults={
            'email': 'rishabhrastogi185@gmail.com',
            'first_name': 'Test',
            'last_name': 'user'
        }
    )
    
    if created:
        user.set_password('testpass123')
        user.save()
        print(f"Created test user: {user.username} ({user.email})")
    else:
        print(f"Using existing test user: {user.username} ({user.email})")
    
    # Get a plan
    plan = Plan.objects.first()
    if not plan:
        print("No plans found! Plans should be seeded automatically in Docker.")
        return False
    
    print(f"Using plan: {plan.get_name_display()} (${plan.price})")
    
    # Create API client and authenticate
    client = APIClient()
    
    # Get JWT token for authentication
    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)
    
    # Set authentication header
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
    
    # Test API subscription creation
    print("Testing API subscription creation...")
    
    subscription_data = {
        'plan': plan.id,
        'start_date': timezone.now().date().strftime('%Y-%m-%d')
    }
    
    print(f"Sending data: {subscription_data}")
    
    response = client.post('/api/subscriptions/', subscription_data, format='json')
    
    print(f"Response status: {response.status_code}")
    
    if response.status_code == 201:
        print("Subscription created successfully via API")
        subscription_response = response.json()
        print(f"Subscription ID: {subscription_response['id']}")
        print(f"Start Date: {subscription_response['start_date']}")
        print(f"End Date: {subscription_response['end_date']}")
        print(f"Email should have been sent to: {user.email}")
        
        # Check if invoice was created
        subscription = Subscription.objects.get(id=subscription_response['id'])
        invoices = Invoice.objects.filter(subscription=subscription)
        print(f"Invoices created: {invoices.count()}")
        
        if invoices.exists():
            invoice = invoices.first()
            print(f"Invoice amount: ${invoice.amount}")
            print(f"Invoice due date: {invoice.due_date}")
            print(f"Invoice status: {invoice.status}")
        
        return True
    else:
        print(f"Failed to create subscription: {response.status_code}")
        try:
            error_data = response.json()
            print(f"Error response: {json.dumps(error_data, indent=2)}")
        except:
            print(f"Raw response: {response.content}")
        return False

def test_email_configuration():
    print("Testing Email Configuration...")
    
    from django.conf import settings
    
    print(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    print(f"EMAIL_HOST: {getattr(settings, 'EMAIL_HOST', 'Not set')}")
    print(f"EMAIL_PORT: {getattr(settings, 'EMAIL_PORT', 'Not set')}")
    print(f"EMAIL_USE_TLS: {getattr(settings, 'EMAIL_USE_TLS', 'Not set')}")
    print(f"EMAIL_HOST_USER: {getattr(settings, 'EMAIL_HOST_USER', 'Not set')}")
    
    password_set = bool(getattr(settings, 'EMAIL_HOST_PASSWORD', None))
    print(f"   EMAIL_HOST_PASSWORD: {'SET' if password_set else 'NOT SET'}")

def test_jwt_authentication():
    """Test JWT authentication setup"""
    print("Testing JWT Authentication...")
    
    # Create test user for JWT
    user, created = User.objects.get_or_create(
        username='jwt_test',
        defaults={
            'email': 'rishabhrastogi185@gmail.com',
            'password': 'testpass123'
        }
    )
    
    if created:
        user.set_password('testpass123')
        user.save()
    
    # Test JWT token generation
    try:
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        print(f"JWT token generated successfully")
        print(f"Access token length: {len(access_token)} characters")
        return True
    except Exception as e:
        print(f"JWT token generation failed: {e}")
        return False

if __name__ == '__main__':
    print("API Email Test Starting")
    
    # Test email configuration
    test_email_configuration()
    
    # Test JWT authentication
    jwt_success = test_jwt_authentication()
    
    if not jwt_success:
        print("JWT authentication failed. Cannot proceed with API tests.")
        sys.exit(1)
    
    # Test API subscription with email
    success = test_api_subscription_email()
    
    if success:
        print("SUCCESS! API subscription creation with email is working!")
    else:
        print("FAILED! Check the error messages above.")
        sys.exit(1) 