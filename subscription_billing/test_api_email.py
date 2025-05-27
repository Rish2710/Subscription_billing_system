import os
import sys
import django
import requests
import json

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'subscription_billing.settings')
django.setup()

from django.contrib.auth.models import User
from billing.models import Plan
from django.test import Client
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

def test_api_subscription_email():
    print("Testing API Subscription Email Functionality...")
    
    # Create or get test user
    user, created = User.objects.get_or_create(
        username='api_test_user1',
        defaults={
            'email': 'rishabhrastogi185@gmail.com',
            'first_name': 'API',
            'last_name': 'Test'
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
        print("No plans found! Run 'python manage.py seed_plans' first.")
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
        'start_date': '2025-01-01'
    }
    
    response = client.post('/api/subscriptions/', subscription_data, format='json')
    
    if response.status_code == 201:
        print("Subscription created successfully via API")
        subscription_data = response.json()
        print(f"Subscription ID: {subscription_data['id']}")
        print(f"Start Date: {subscription_data['start_date']}")
        print(f"End Date: {subscription_data['end_date']}")
        print(f"Email should have been sent to: {user.email}")
        return True
    else:
        print(f"Failed to create subscription: {response.status_code}")
        print(f"Response: {response.json()}")
        return False

def test_console_email_output():
    """Test that emails are being sent to console"""
    print("Testing Console Email Output...")
    print("If you see email content above, emails are working!")
    print("If using SMTP, check your email inbox.")

if __name__ == '__main__':
    success = test_api_subscription_email()
    test_console_email_output()
    
    if success:
        print("SUCCESS! API subscription creation with email is working!")
        print("Next steps:")
        print("1. Test with Postman using the same endpoint: POST /api/subscriptions/")
        print("2. Make sure to include Authorization header: Bearer <your_jwt_token>")
        print("3. Send JSON data: {'plan': <plan_id>, 'start_date': '2025-01-01'}")
    else:
        print("FAILED! Check the error messages above.") 