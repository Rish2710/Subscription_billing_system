FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Add psycopg2 for PostgreSQL connection
RUN pip install psycopg2-binary dj-database-url

# Copy project code
COPY . .

# Create directories for logs
RUN mkdir -p subscription_billing/logs

# Set proper permissions
RUN chmod -R 755 .

# Expose port 8000 for Django
EXPOSE 8000

# Set Python path to include subscription_billing directory
ENV PYTHONPATH="${PYTHONPATH}:/app" 