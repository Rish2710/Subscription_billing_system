# Subscription Billing System API Documentation

This document provides comprehensive information about the Subscription Billing System API, including JWT authentication and billing endpoints for third-party integration.

## Base URL
```
http://localhost:8000
```

## Authentication

The API uses JWT (JSON Web Token) authentication. To access protected endpoints, you need to:

1. Register a user account or login with existing credentials
2. Use the access token in the Authorization header for subsequent requests

### Authentication Flow

#### 1. Register a New User
```http
POST /api/auth/register/
Content-Type: application/json

{
    "username": "testuser",
    "email": "test@example.com",
    "first_name": "Test",
    "last_name": "User",
    "password": "securepassword123",
    "password_confirm": "securepassword123"
}
```

**Response:**
```json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "user": {
        "id": 1,
        "username": "testuser",
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User"
    }
}
```

#### 2. Login with Existing User
```http
POST /api/auth/login/
Content-Type: application/json

{
    "username": "testuser",
    "password": "securepassword123"
}
```

**Response:**
```json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "user": {
        "id": 1,
        "username": "testuser",
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User"
    }
}
```

## Billing API Endpoints

### Plans

#### Get All Available Plans (Public)
```http
GET /api/plans/
```

**Response:**
```json
[
    {
        "id": 1,
        "name": "basic",
        "price": "9.99",
        "description": "Basic plan with essential features"
    },
    {
        "id": 2,
        "name": "pro",
        "price": "19.99",
        "description": "Pro plan with advanced features"
    },
    {
        "id": 3,
        "name": "enterprise",
        "price": "49.99",
        "description": "Enterprise plan with all features"
    }
]
```

#### Get Specific Plan (Public)
```http
GET /api/plans/{id}/
```

### Subscriptions

#### Get User Subscriptions
```http
GET /api/subscriptions/
Authorization: Bearer {{token}}
```

#### Create New Subscription
```http
POST /api/subscriptions/
Authorization: Bearer {{token}}
Content-Type: application/json

{
    "plan": 1,
    "start_date": "2024-01-01"
}
```

**Response:**
```json
{
    "id": 1,
    "user": 1,
    "plan": 1,
    "plan_details": {
        "id": 1,
        "name": "basic",
        "price": "9.99",
        "description": "Basic plan with essential features"
    },
    "start_date": "2024-01-01",
    "end_date": "2024-01-31",
    "status": "active",
    "created_at": "2024-01-01T10:00:00Z",
    "updated_at": "2024-01-01T10:00:00Z"
}
```

#### Cancel Subscription
```http
POST /api/subscriptions/{{id}}/cancel/
Authorization: Bearer {{token}}
```

### Invoices

#### Get User Invoices
```http
GET /api/invoices/
Authorization: Bearer {{token}}
```

#### Get Pending Invoices
```http
GET /api/invoices/pending/
Authorization: Bearer {{token}}
```