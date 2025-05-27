from django.test import TestCase
from rest_framework.test import APIClient
from billing.models import Plan
from django.utils import timezone

class APIFunctionalTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.register_url = "/api/auth/register/"
        self.login_url = "/api/auth/login/"
        self.plans_url = "/api/plans/"
        self.subscriptions_url = "/api/subscriptions/"
        self.invoices_url = "/api/invoices/"
        self.pending_invoices_url = "/api/invoices/pending/"

        # Create a plan
        self.plan = Plan.objects.create(name='basic', price=9.99, description='Basic plan with standard features')

        # User data
        self.user_data = {
            "username": "testuser",
            "email": "rishabhrastogi185@gmail.com",
            "first_name": "Test",
            "last_name": "User",
            "password": "securepassword123",
            "password_confirm": "securepassword123"
        }

    def test_full_subscription_flow(self):
        # Register user
        register_response = self.client.post(self.register_url, self.user_data, format='json')
        print("Register Response:", register_response.status_code, register_response.data)
        self.assertEqual(register_response.status_code, 201)

        # Login user
        login_data = {
            "username": self.user_data["username"],
            "password": self.user_data["password"]
        }
        login_response = self.client.post(self.login_url, login_data, format='json')
        print("Login Response:", login_response.status_code, login_response.data)
        self.assertEqual(login_response.status_code, 200, f"Login failed: {login_response.data}")
        self.assertIn('access', login_response.data, f"Token not found in response: {login_response.data}")

        token = login_response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        # Get available plans
        plans_response = self.client.get(self.plans_url)
        self.assertEqual(plans_response.status_code, 200)

        # Create a subscription
        start_date = timezone.now().date()
        subscription_data = {
            "plan": self.plan.id,
            "start_date": str(start_date)
        }
        subscription_response = self.client.post(self.subscriptions_url, subscription_data, format='json')
        print("Subscription Response:", subscription_response.status_code, subscription_response.data)
        self.assertEqual(subscription_response.status_code, 201)

        subscription_id = subscription_response.data['id']

        # Fetch pending invoices again (after subscription creation)
        pending_response = self.client.get(self.pending_invoices_url)
        print("Pending Invoices Response:", pending_response.status_code, pending_response.data)
        self.assertEqual(pending_response.status_code, 200)

        if not pending_response.data:
            self.fail("No pending invoices found after subscription creation.")

        # Cancel subscription
        cancel_url = f"/api/subscriptions/{subscription_id}/cancel/"
        cancel_response = self.client.post(cancel_url)
        print("Cancel Subscription Response:", cancel_response.status_code, cancel_response.data)
        self.assertEqual(cancel_response.status_code, 200)
