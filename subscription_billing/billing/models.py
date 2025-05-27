from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid

class Plan(models.Model):
    PLAN_TYPES = (
        ('basic', 'Basic'),
        ('pro', 'Pro'),
        ('enterprise', 'Enterprise'),
    )
    
    name = models.CharField(max_length=50, choices=PLAN_TYPES)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    
    def __str__(self):
        return self.get_name_display()

class Subscription(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')
    email = models.EmailField(null=True, blank=True, help_text="Email address for subscription notifications")
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE)
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        # Auto-populate email from user if not provided or empty
        if (not self.email or self.email.strip() == '') and self.user and self.user.email:
            self.email = self.user.email
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.user.username} - {self.plan.name} ({self.status})"
    
    def is_active(self):
        return self.status == 'active' and self.end_date >= timezone.now().date()

class Invoice(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    )
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='invoices')
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name='invoices')
    email = models.EmailField(null=True, blank=True, help_text="Email address for invoice notifications")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    issue_date = models.DateField(default=timezone.now)
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        # Auto-populate email from user if not provided or empty
        if (not self.email or self.email.strip() == '') and self.user and self.user.email:
            self.email = self.user.email
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Invoice {self.uuid} - {self.user.username} ({self.status})"
    
    def is_overdue(self):
        return self.status == 'pending' and self.due_date < timezone.now().date()
