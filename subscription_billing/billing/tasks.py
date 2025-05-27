from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import logging
from .models import Subscription, Invoice
from .utils import (
    send_invoice_created_email, 
    send_payment_reminder_email, 
    send_subscription_confirmation_email
)
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)

@shared_task
def generate_invoices():
    """
    Generate invoices for active subscriptions
    This task is scheduled to run daily
    """
    logger.info("Starting invoice generation task")
    today = timezone.now().date()
    # Get all active subscriptions
    active_subscriptions = Subscription.objects.filter(
        status='active',
        end_date__gte=today
    )
    
    logger.info(f"Found {active_subscriptions.count()} active subscriptions")
    
    invoices_created = 0
    emails_sent = 0
    
    for subscription in active_subscriptions:
        if subscription.start_date.day == today.day:
            due_date = today + timedelta(days=15)
            
            # Create a new invoice
            invoice = Invoice.objects.create(
                user=subscription.user,
                subscription=subscription,
                amount=subscription.plan.price,
                issue_date=today,
                due_date=due_date,
                status='pending'
            )
            invoices_created += 1
            logger.info(f"Created invoice {invoice.uuid} for subscription {subscription.id} - User: {subscription.user.username}")
            
            # Send invoice email notification
            if send_invoice_created_email(invoice):
                emails_sent += 1
    
    logger.info(f"Invoice generation complete. Created {invoices_created} invoices, sent {emails_sent} emails")
    return f"Generated {invoices_created} invoices, sent {emails_sent} emails"

@shared_task
def mark_overdue_invoices():
    """
    Mark invoices as overdue if due date has passed
    This task runs daily
    """
    logger.info("Starting mark overdue invoices task")
    today = timezone.now().date()
    
    # Get all pending invoices with due date in the past
    overdue_invoices = Invoice.objects.filter(
        status='pending',
        due_date__lt=today
    )
    
    count = overdue_invoices.count()
    logger.info(f"Found {count} overdue invoices")
    
    # Update status to overdue
    overdue_invoices.update(status='overdue')
    
    logger.info(f"Marked {count} invoices as overdue")
    return f"Marked {count} invoices as overdue"

@shared_task
def send_payment_reminders():
    """
    Send payment reminders for overdue invoices
    This task runs daily
    """
    logger.info("Starting payment reminder task")
    
    overdue_invoices = Invoice.objects.filter(status='overdue')
    reminder_count = 0
    emails_sent = 0
    
    logger.info(f"Found {overdue_invoices.count()} overdue invoices requiring reminders")
    
    for invoice in overdue_invoices:
        logger.info(f"Sending reminder for invoice {invoice.uuid} - User: {invoice.user.username}")
        reminder_count += 1
        
        # Send reminder email
        if send_payment_reminder_email(invoice):
            emails_sent += 1
    
    logger.info(f"Sent {reminder_count} payment reminders, {emails_sent} emails delivered")
    return f"Sent {reminder_count} payment reminders, {emails_sent} emails delivered"

@shared_task
def send_monthly_subscription_renewals():
    """
    Send monthly subscription renewal reminders for subscriptions ending in 7 days
    This task runs monthly (1st of each month)
    """
    logger.info("Starting monthly subscription renewal reminder task")
    today = timezone.now().date()
    seven_days_from_now = today + timedelta(days=7)
    
    expiring_subscriptions = Subscription.objects.filter(
        status='active',
        end_date__lte=seven_days_from_now,
        end_date__gte=today
    )
    
    logger.info(f"Found {expiring_subscriptions.count()} subscriptions expiring in the next 7 days")
    
    emails_sent = 0
    for subscription in expiring_subscriptions:
        try:
            # Send renewal reminder email
            send_mail(
                subject='🔔 Your Subscription is Expiring Soon!',
                message='',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[subscription.email or subscription.user.email],
                html_message=render_to_string('billing/emails/subscription_renewal_reminder.html', {
                    'subscription': subscription,
                    'user': subscription.user,
                    'plan': subscription.plan,
                    'days_remaining': (subscription.end_date - today).days
                }),
                fail_silently=False,
            )
            emails_sent += 1
            logger.info(f"Sent renewal reminder to {subscription.user.username} - expires {subscription.end_date}")
        except Exception as e:
            logger.error(f"Failed to send renewal reminder to {subscription.user.username}: {e}")
    
    logger.info(f"Monthly renewal reminders complete. Sent {emails_sent} emails")
    return f"Sent {emails_sent} subscription renewal reminders"

@shared_task
def send_monthly_billing_summary():
    """
    Send monthly billing summary to all active users
    This task runs monthly (1st of each month)
    """
    logger.info("Starting monthly billing summary task")
    today = timezone.now().date()
    first_day_last_month = today.replace(day=1) - timedelta(days=1)
    first_day_last_month = first_day_last_month.replace(day=1)
    last_day_last_month = today.replace(day=1) - timedelta(days=1)
    
    # Get all users with active subscriptions
    users_with_subscriptions = User.objects.filter(
        subscription__status='active'
    ).distinct()
    
    logger.info(f"Found {users_with_subscriptions.count()} users with active subscriptions")
    
    emails_sent = 0
    for user in users_with_subscriptions:
        try:
            last_month_invoices = Invoice.objects.filter(
                user=user,
                issue_date__gte=first_day_last_month,
                issue_date__lte=last_day_last_month
            )
            
            active_subscriptions = Subscription.objects.filter(
                user=user,
                status='active'
            )
            
            total_amount = sum(invoice.amount for invoice in last_month_invoices)
            total_paid = sum(invoice.amount for invoice in last_month_invoices.filter(status='paid'))
            total_pending = sum(invoice.amount for invoice in last_month_invoices.filter(status='pending'))
            
            user_email = user.email if user.email else None
            if user_email:
                send_mail(
                    subject=f'Monthly Billing Summary - {last_day_last_month.strftime("%B %Y")}',
                    message='',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user_email],
                    html_message=render_to_string('billing/emails/monthly_billing_summary.html', {
                        'user': user,
                        'month_year': last_day_last_month.strftime("%B %Y"),
                        'last_month_invoices': last_month_invoices,
                        'active_subscriptions': active_subscriptions,
                        'total_amount': total_amount,
                        'total_paid': total_paid,
                        'total_pending': total_pending,
                        'invoice_count': last_month_invoices.count(),
                    }),
                    fail_silently=False,
                )
                emails_sent += 1
                logger.info(f"Sent monthly summary to {user.username} - {last_month_invoices.count()} invoices, ${total_amount}")
        
        except Exception as e:
            logger.error(f"Failed to send monthly summary to {user.username}: {e}")
    
    logger.info(f"Monthly billing summary complete. Sent {emails_sent} emails")
    return f"Sent {emails_sent} monthly billing summaries"

@shared_task
def send_monthly_admin_report():
    """
    Send monthly admin report with business metrics
    This task runs monthly (1st of each month)
    """
    logger.info("Starting monthly admin report task")
    today = timezone.now().date()
    first_day_last_month = today.replace(day=1) - timedelta(days=1)
    first_day_last_month = first_day_last_month.replace(day=1)
    last_day_last_month = today.replace(day=1) - timedelta(days=1)
    
    try:
        last_month_invoices = Invoice.objects.filter(
            issue_date__gte=first_day_last_month,
            issue_date__lte=last_day_last_month
        )
        
        new_subscriptions = Subscription.objects.filter(
            start_date__gte=first_day_last_month,
            start_date__lte=last_day_last_month
        )
        
        new_users = User.objects.filter(
            date_joined__gte=first_day_last_month,
            date_joined__lte=last_day_last_month
        )
        
        total_revenue = sum(invoice.amount for invoice in last_month_invoices.filter(status='paid'))
        pending_revenue = sum(invoice.amount for invoice in last_month_invoices.filter(status='pending'))
        overdue_revenue = sum(invoice.amount for invoice in last_month_invoices.filter(status='overdue'))
        
        total_active_subscriptions = Subscription.objects.filter(status='active').count()
        
        admin_emails = [settings.DEFAULT_FROM_EMAIL]  # You can customize this
        
        send_mail(
            subject=f'Monthly Admin Report - {last_day_last_month.strftime("%B %Y")}',
            message='',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=admin_emails,
            html_message=render_to_string('billing/emails/monthly_admin_report.html', {
                'month_year': last_day_last_month.strftime("%B %Y"),
                'total_revenue': total_revenue,
                'pending_revenue': pending_revenue,
                'overdue_revenue': overdue_revenue,
                'new_subscriptions_count': new_subscriptions.count(),
                'new_users_count': new_users.count(),
                'total_active_subscriptions': total_active_subscriptions,
                'invoices_generated': last_month_invoices.count(),
                'new_subscriptions': new_subscriptions,
                'metrics_period': f"{first_day_last_month.strftime('%Y-%m-%d')} to {last_day_last_month.strftime('%Y-%m-%d')}"
            }),
            fail_silently=False,
        )
        
        logger.info(f"Sent monthly admin report - Revenue: ${total_revenue}, New subs: {new_subscriptions.count()}")
        return f"Sent monthly admin report - ${total_revenue} revenue, {new_subscriptions.count()} new subscriptions"
        
    except Exception as e:
        logger.error(f"Failed to send monthly admin report: {e}")
        return f"Failed to send monthly admin report: {e}"

@shared_task
def send_unpaid_invoice_reminders():
    """
    Send daily reminders to users with unpaid invoices (pending or overdue)
    This task runs daily
    """
    logger.info("Starting unpaid invoice reminders task")
    
    # Get all unpaid invoices (both pending and overdue)
    unpaid_invoices = Invoice.objects.filter(status__in=['pending', 'overdue'])
    
    # Group invoices by user
    users_with_unpaid = {}
    for invoice in unpaid_invoices:
        user_id = invoice.user.id
        if user_id not in users_with_unpaid:
            users_with_unpaid[user_id] = []
        users_with_unpaid[user_id].append(invoice)
    
    logger.info(f"Found {len(users_with_unpaid)} users with unpaid invoices")
    
    emails_sent = 0
    emails_failed = 0
    
    for user_id, user_invoices in users_with_unpaid.items():
        user = user_invoices[0].user
        
        # Skip if user has no email
        if not user.email:
            logger.warning(f"User {user.username} has no email address, skipping reminder")
            continue
        
        try:
            # Calculate total amount due
            total_amount = sum(invoice.amount for invoice in user_invoices)
            
            context = {
                'user': user,
                'invoices': user_invoices,
                'total_amount': total_amount,
                'invoice_count': len(user_invoices)
            }
            
            subject = f"Payment Reminder: You have {len(user_invoices)} unpaid invoice{'s' if len(user_invoices) > 1 else ''}"
            message = render_to_string('billing/emails/unpaid_invoice_reminder.html', context)
            
            send_mail(
                subject=subject,
                message='',  # Empty plain text, use html_message
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=message,
                fail_silently=False,
            )
            
            emails_sent += 1
            logger.info(f"Sent unpaid invoice reminder to {user.username} - {len(user_invoices)} invoices, ${total_amount}")
            
        except Exception as e:
            emails_failed += 1
            logger.error(f"Failed to send unpaid invoice reminder to {user.username}: {e}")
    
    logger.info(f"Unpaid invoice reminders complete. Sent {emails_sent} emails, {emails_failed} failed")
    return f"Sent reminders to {emails_sent} users with unpaid invoices. {emails_failed} failed." 