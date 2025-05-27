from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Test email configuration by sending a test email'

    def add_arguments(self, parser):
        parser.add_argument(
            '--to',
            dest='to_email',
            help='Recipient email address',
            required=True
        )

    def handle(self, *args, **options):
        to_email = options['to_email']
        from_email = settings.DEFAULT_FROM_EMAIL

        self.stdout.write(self.style.WARNING(f"Attempting to send test email from {from_email} to {to_email}..."))
        
        try:
            send_mail(
                subject='Test Email from Subscription Billing System',
                message='This is a test email from your Django application to verify email configuration.',
                from_email=from_email,
                recipient_list=[to_email],
                fail_silently=False,
                html_message='<h1>Test Email</h1><p>This is a test email from your <strong>Django application</strong> to verify email configuration.</p>'
            )
            self.stdout.write(self.style.SUCCESS('Test email sent successfully!'))
            
            if settings.EMAIL_BACKEND == 'django.core.mail.backends.console.EmailBackend':
                self.stdout.write(self.style.WARNING(
                    'NOTE: You are using the console email backend. '
                    'The email was not actually sent but printed above.'
                ))
                self.stdout.write(self.style.WARNING(
                    'To send real emails, configure SMTP settings in your .env file.'
                ))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to send email: {str(e)}'))
            logger.error(f'Failed to send test email: {str(e)}') 