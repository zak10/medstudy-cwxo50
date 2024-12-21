# Medical Research Platform API Documentation

Version: 1.0.0

## Introduction

The Medical Research Platform API provides secure, RESTful endpoints for managing community-driven medical research protocols. This documentation covers authentication, endpoints, data models, and security requirements.

### Base URL
```
/api/v1
```

### Content Type
All requests and responses use:
```
Content-Type: application/json
```

## Authentication

### JWT Authentication
The API uses JWT (JSON Web Token) with RSA-256 signing for secure authentication.

#### Token Details
- Access Token Lifetime: 1 hour
- Refresh Token Lifetime: 1 week
- Algorithm: RS256

#### Authentication Header
```
Authorization: Bearer <access_token>
```

### Rate Limiting
| Endpoint Type | Limit |
|--------------|-------|
| Default | 100 requests/hour |
| Authentication | 5 requests/minute |
| Sensitive Operations | 20 requests/minute |

## Core Services

### 1. User Management

#### Register User
```http
POST /auth/register
```

Request Body:
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "password_confirm": "SecurePass123!",
  "first_name": "John",
  "last_name": "Doe",
  "profile": {
    "bio": "Research enthusiast"
  }
}
```

Response:
```json
{
  "success": true,
  "message": "Registration successful",
  "data": {
    "user": {
      "id": "uuid",
      "email": "user@example.com",
      "role": "participant"
    },
    "access_token": "string",
    "refresh_token": "string",
    "token_type": "Bearer",
    "expires_in": 3600
  }
}
```

#### Refresh Token
```http
POST /auth/refresh
```

Request Body:
```json
{
  "refresh_token": "string"
}
```

### 2. Protocol Management

#### List Protocols
```http
GET /protocols
```

Query Parameters:
| Parameter | Type | Description |
|-----------|------|-------------|
| page | integer | Page number (default: 1) |
| page_size | integer | Items per page (default: 20, max: 100) |
| sort | string | Sort direction (asc/desc) |

#### Create Protocol
```http
POST /protocols
```

Request Body:
```json
{
  "title": "Vitamin D Study",
  "description": "Investigation of vitamin D supplementation",
  "requirements": {
    "data_collection_frequency": "weekly",
    "measurements": {
      "vitamin_d": {
        "min": 20,
        "max": 80,
        "unit": "ng/mL"
      }
    }
  },
  "safety_params": {
    "markers": {
      "vitamin_d": {
        "critical_ranges": {
          "min": 10,
          "max": 100,
          "unit": "ng/mL"
        },
        "alert_ranges": {
          "min": 20,
          "max": 80,
          "unit": "ng/mL"
        }
      }
    }
  },
  "duration_weeks": 12
}
```

### 3. Data Collection

#### Submit Data Point
```http
POST /data-points
```

Request Body:
```json
{
  "protocol_id": "uuid",
  "type": "blood_work",
  "data": {
    "test_date": "2023-09-20T10:00:00Z",
    "lab_name": "Example Lab",
    "lab_certification": "ABC123",
    "markers": {
      "vitamin_d": {
        "value": 45.5,
        "unit": "ng/mL"
      }
    }
  }
}
```

## Data Models

### User Schema
```json
{
  "email": "string",
  "first_name": "string",
  "last_name": "string",
  "role": "string",
  "profile": {
    "additional_properties": {}
  }
}
```

### Protocol Schema
```json
{
  "id": "uuid",
  "title": "string",
  "description": "string",
  "requirements": {
    "data_collection_frequency": "string",
    "measurements": {}
  },
  "safety_params": {
    "markers": {},
    "intervention_triggers": []
  },
  "start_date": "string",
  "duration_weeks": "integer"
}
```

## Security

### Password Requirements
- Minimum length: 12 characters
- Must contain:
  - Uppercase letter
  - Lowercase letter
  - Number
  - Special character (@$!%*#?&)

### Data Classification
| Level | Description | Controls |
|-------|-------------|----------|
| Public | Protocol descriptions | Basic access controls |
| Confidential | User profiles | Role-based access, encryption |
| Restricted | Health records | Field-level encryption, audit logging |
| Critical | Authentication credentials | Hash+salt, secure storage |

### Error Handling

All errors follow this format:
```json
{
  "success": false,
  "message": "string",
  "error_code": "string",
  "details": {
    "fields": {}
  }
}
```

HTTP Status Codes:
| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 400 | Validation Error |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 429 | Rate Limit Exceeded |
| 500 | Server Error |

## HIPAA Compliance

The API implements required HIPAA security measures:
- Encryption at rest (AES-256)
- TLS 1.3 for data in transit
- Audit logging of all PHI access
- Role-based access control
- Automatic session termination
- Secure key management

## Rate Limiting Headers

Response Headers:
```
X-RateLimit-Limit: <requests_per_period>
X-RateLimit-Remaining: <requests_remaining>
X-RateLimit-Reset: <reset_timestamp>
```

## Versioning

The API uses URI versioning:
- Current version: v1
- Version format: /api/v{version_number}
- Breaking changes trigger version increment

## Support

For API support:
- Email: api-support@example.com
- Documentation: https://docs.example.com/api
- Status page: https://status.example.com