from django.core.management.base import BaseCommand
from billing.models import Plan

class Command(BaseCommand):
    help = 'Seeds the database with predefined subscription plans'

    def handle(self, *args, **options):
        plans = [
            {
                'name': 'basic',
                'price': 9.99,
                'description': 'Basic plan with limited features'
            },
            {
                'name': 'pro',
                'price': 19.99,
                'description': 'Professional plan with more features'
            },
            {
                'name': 'enterprise',
                'price': 49.99,
                'description': 'Enterprise plan with all features and priority support'
            }
        ]
        
        for plan_data in plans:
            plan, created = Plan.objects.get_or_create(
                name=plan_data['name'],
                defaults={
                    'price': plan_data['price'],
                    'description': plan_data['description']
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created plan: {plan.get_name_display()}'))
            else:
                self.stdout.write(f'Plan already exists: {plan.get_name_display()}')
        
        self.stdout.write(self.style.SUCCESS('Successfully seeded subscription plans')) 