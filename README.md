# Subscription Billing System

A Django-based subscription billing backend that supports user sign-up, plan subscription, automatic invoice generation using Celery, and simple billing lifecycle tracking.

## Features

- User subscription management
- Predefined plans (Basic, Pro, Enterprise)
- Automatic invoice generation using Celery
- Invoice status tracking (pending, paid, overdue)
- Payment reminder notifications
- RESTful API for subscription and invoice management

## Running with Docker (Recommended)

The easiest way to run the application is using Docker Compose, which sets up all required services automatically.

### Prerequisites

- Docker and Docker Compose installed on your system

### Quick Start

1. Clone the repository:
   ```
   git clone https://github.com/Rish2710/Subscription_billing_system.git
   cd subscription_billing_system
   ```

2. Create a `.env` file from the example:
   ```
   python3 -m venv venv
   ```
   
3. Build and start the containers:
   ```
   docker-compose up -d
   ```
   
4. Create a superuser:
   ```
   docker-compose exec web python subscription_billing/manage.py createsuperuser
   ```
   
5. Access the application at: http://localhost:8000

### Docker Services

The Docker setup includes:
- **web**: Django web application
- **db**: PostgreSQL database
- **redis**: Redis for Celery message broker
- **celery-worker**: Celery worker for processing background tasks
- **celery-beat**: Celery beat for scheduling recurring tasks

## Manual Setup (Development)

For local development without Docker:

1. Clone the repository
2. Set up a virtual environment
   ```
   python3 -m venv venv
   ```
   Once virtual env is set up, then activate the virtual env.
   ```
   source venv/bin/activate
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Apply migrations:
   ```
   python subscription_billing/manage.py migrate
   ```
5. Seed the database with predefined plans:
   ```
   python subscription_billing/manage.py seed_plans
   ```
6. Create a superuser:
   ```
   python subscription_billing/manage.py createsuperuser
   ```
7. Start the development server:
   ```
   python subscription_billing/manage.py runserver
   ```
8. In a separate terminal, start Celery worker:
   ```
   cd subscription_billing
   celery -A subscription_billing worker -l info
   ```
9. In another terminal, start Celery beat for scheduled tasks:
   ```
   cd subscription_billing
   celery -A subscription_billing beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
   ```

## API Endpoints

- `/api/plans/` - View available subscription plans
- `/api/subscriptions/` - Manage user subscriptions
- `/api/subscriptions/{id}/cancel/` - Cancel a subscription
- `/api/invoices/` - View user invoices
- `/api/invoices/pending/` - View pending invoices

## Celery Tasks

- `generate_invoices` - Generates invoices for active subscriptions
- `mark_overdue_invoices` - Marks unpaid invoices as overdue if due date has passed
- `send_payment_reminders` - Sends reminders for overdue invoices

## Email Configuration

Currently email backend is configured to gmail. If you want to configure some other email backend then you can make changes in the `.env` file.

#### Note: The current `Password` in the `.env` file is valid for a week after that the `Password` will expire.

### Setting Up Email with Environment Variables

1. Update your `.env` file with the following settings:
   ```
   EMAIL_HOST=smtp.gmail.com
   EMAIL_PORT=587
   EMAIL_USE_TLS=True
   EMAIL_HOST_USER=your.email@gmail.com
   EMAIL_HOST_PASSWORD=your-app-password
   ```

2. The settings.py file is already configured to use these environment variables when available.

### Gmail-Specific Instructions

If using Gmail, you'll need to:

1. Enable 2-Step Verification for your Google account
2. Generate an App Password:
   - Go to this URL `https://myaccount.google.com/u/1/apppasswords`
   - Sign-in into your google account.
   - Write the App name and click on create.
   - It will generate a 16-character password.
   - Use the generated 16-character password without spaces in your `.env` file.

