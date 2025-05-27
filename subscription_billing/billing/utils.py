from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def send_email_template(subject, template, context, recipient_list, from_email=None):
    """
    Send an HTML email using a template with a text fallback
    
    Args:
        subject (str): Email subject
        template (str): Path to the HTML template
        context (dict): Context data for the template
        recipient_list (list): List of recipient email addresses
        from_email (str, optional): Sender email address. Defaults to DEFAULT_FROM_EMAIL.
    
    Returns:
        bool: True if the email was sent successfully, False otherwise
    """
    if from_email is None:
        from_email = settings.DEFAULT_FROM_EMAIL
    
    try:
        # Render HTML content
        html_content = render_to_string(template, context)
        # Create plain text version
        text_content = strip_tags(html_content)
        
        # Create email message
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=from_email,
            to=recipient_list
        )
        
        # Attach HTML content
        email.attach_alternative(html_content, "text/html")
        
        # Send email
        email.send()
        
        logger.info(f"Email sent to {', '.join(recipient_list)}: {subject}")
        return True
    
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        logger.error(f"Email configuration: Backend={settings.EMAIL_BACKEND}, Host={getattr(settings, 'EMAIL_HOST', 'Not set')}, User={getattr(settings, 'EMAIL_HOST_USER', 'Not set')}")
        return False

def send_invoice_created_email(invoice):
    """
    Send an email notification when a new invoice is created
    
    Args:
        invoice: The Invoice object
    
    Returns:
        bool: True if the email was sent successfully, False otherwise
    """
    logger.info(f"Preparing to send invoice created email for invoice {invoice.uuid} to {invoice.user.email}")
    
    subject = f"New Invoice #{invoice.uuid} - {invoice.subscription.plan.get_name_display()} Plan"
    template = 'billing/emails/invoice_created.html'
    context = {
        'invoice': invoice,
        'user': invoice.user,
    }
    recipient_list = [invoice.email]
    logger.info(f"Sending invoice created email to {recipient_list}")
    
    return send_email_template(subject, template, context, recipient_list)

def send_payment_reminder_email(invoice):
    """
    Send a payment reminder email for an overdue invoice
    
    Args:
        invoice: The Invoice object
    
    Returns:
        bool: True if the email was sent successfully, False otherwise
    """
    subject = f"Payment Reminder: Invoice #{invoice.uuid} is Overdue"
    template = 'billing/emails/payment_reminder.html'
    context = {
        'invoice': invoice,
        'user': invoice.user,
    }
    recipient_list = [invoice.email]
    
    return send_email_template(subject, template, context, recipient_list)

def send_subscription_confirmation_email(subscription):
    """
    Send a confirmation email when a user subscribes to a plan
    
    Args:
        subscription: The Subscription object
    
    Returns:
        bool: True if the email was sent successfully, False otherwise
    """
    subject = f"Subscription Confirmation - {subscription.plan.get_name_display()} Plan"
    template = 'billing/emails/subscription_confirmation.html'
    context = {
        'subscription': subscription,
        'user': subscription.user,
    }
    # Use subscription.email if available, fallback to user.email
    recipient_email = subscription.email or subscription.user.email
    recipient_list = [recipient_email]
    
    return send_email_template(subject, template, context, recipient_list)

def send_payment_confirmation_email(invoice):
    """
    Send a payment confirmation email when an invoice is paid
    
    Args:
        invoice: The Invoice object
    
    Returns:
        bool: True if the email was sent successfully, False otherwise
    """
    subject = f"Payment Confirmation: Invoice #{invoice.uuid}"
    template = 'billing/emails/payment_confirmation.html'
    context = {
        'invoice': invoice,
        'user': invoice.user,
    }
    recipient_list = [invoice.email]
    
    return send_email_template(subject, template, context, recipient_list) 