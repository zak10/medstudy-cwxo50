# Medical Research Platform - Backend Architecture
**Version:** 1.0  
**Last Updated:** 2024-01-20  
**Status:** Living document  
**Maintainers:** Backend Team  
**Review Cycle:** Quarterly  
**Next Review:** 2024-04-20

## Table of Contents
1. [System Overview](#1-system-overview)
2. [Core Services](#2-core-services)
3. [Data Architecture](#3-data-architecture)
4. [Security Architecture](#4-security-architecture)
5. [API Architecture](#5-api-architecture)
6. [Deployment Architecture](#6-deployment-architecture)

## 1. System Overview

### 1.1 System Context

```mermaid
C4Context
    title System Context Diagram
    
    Person(participant, "Study Participant", "Participates in research protocols")
    Person(creator, "Protocol Creator", "Creates and manages protocols")
    Person(partner, "Supplement Partner", "Provides products and analytics")
    
    System(mrs, "Medical Research Platform", "Community-driven medical research system")
    
    System_Ext(lab, "Laboratory Systems", "Processes blood tests")
    System_Ext(payment, "Payment Gateway", "Handles transactions")
    System_Ext(email, "Email Service", "Manages communications")
    
    Rel(participant, mrs, "Submits data, views results")
    Rel(creator, mrs, "Creates protocols, analyzes data")
    Rel(partner, mrs, "Manages products, views analytics")
    
    Rel(mrs, lab, "Receives test results")
    Rel(mrs, payment, "Processes payments")
    Rel(mrs, email, "Sends notifications")
```

### 1.2 Container Architecture

```mermaid
C4Container
    title Container Diagram
    
    Container(web, "Web Application", "Vue.js", "User interface")
    Container(api, "API Gateway", "Kong", "API management")
    
    Container_Boundary(services, "Core Services") {
        Container(user, "User Service", "Django", "User management")
        Container(protocol, "Protocol Service", "Django", "Protocol operations")
        Container(data, "Data Service", "Django", "Data collection")
        Container(analysis, "Analysis Service", "Django", "Data analysis")
        Container(community, "Community Service", "Django", "Forums and messaging")
    }
    
    ContainerDb(db, "Primary Database", "PostgreSQL", "Stores application data")
    ContainerDb(cache, "Cache", "Redis", "Session and data caching")
    ContainerDb(queue, "Message Queue", "RabbitMQ", "Event processing")
    
    Rel(web, api, "Uses", "HTTPS")
    Rel(api, services, "Routes", "HTTP")
    Rel(services, db, "Reads/Writes", "SQL")
    Rel(services, cache, "Reads/Writes", "Redis Protocol")
    Rel(services, queue, "Publishes/Subscribes", "AMQP")
```

### 1.3 Data Flow Patterns

```mermaid
graph TD
    A[Client Request] --> B[API Gateway]
    B --> C{Authentication}
    C -->|Valid| D[Service Router]
    C -->|Invalid| E[Error Response]
    
    D --> F[User Service]
    D --> G[Protocol Service]
    D --> H[Data Service]
    D --> I[Analysis Service]
    D --> J[Community Service]
    
    F --> K[(Primary DB)]
    G --> K
    H --> K
    I --> K
    J --> K
    
    F --> L[(Cache)]
    G --> L
    H --> L
```

## 2. Core Services

### 2.1 Service Architecture Matrix

| Service | Primary Responsibility | Dependencies | Scaling Strategy |
|---------|----------------------|--------------|------------------|
| User Service | Authentication, profiles | PostgreSQL, Redis | Horizontal |
| Protocol Service | Protocol management | PostgreSQL, S3 | Horizontal |
| Data Service | Data collection | PostgreSQL, Redis | Horizontal |
| Analysis Service | Statistical processing | PostgreSQL | Vertical |
| Community Service | Forums, messaging | PostgreSQL, WebSocket | Horizontal |

### 2.2 Service Interaction Patterns

```mermaid
sequenceDiagram
    participant C as Client
    participant G as API Gateway
    participant U as User Service
    participant P as Protocol Service
    participant D as Data Service
    
    C->>G: Request
    G->>U: Authenticate
    U-->>G: Token Valid
    G->>P: Forward Request
    P->>D: Get Data
    D-->>P: Return Data
    P-->>G: Response
    G-->>C: JSON Response
```

## 3. Data Architecture

### 3.1 Database Schema

```mermaid
erDiagram
    User ||--o{ Participation : enrolls
    User {
        uuid id PK
        string email UK
        jsonb profile
        timestamp created_at
    }
    
    Protocol ||--|{ Participation : contains
    Protocol {
        uuid id PK
        string title
        jsonb requirements
        jsonb safety_params
        timestamp start_date
    }
    
    Participation ||--|{ DataPoint : generates
    Participation {
        uuid id PK
        uuid user_id FK
        uuid protocol_id FK
        enum status
    }
    
    DataPoint {
        uuid id PK
        uuid participation_id FK
        string type
        jsonb data
        timestamp recorded_at
    }
```

### 3.2 Data Storage Strategy

| Data Type | Storage Solution | Backup Strategy | Retention Policy |
|-----------|-----------------|-----------------|------------------|
| User Data | PostgreSQL | Daily snapshots | 7 years |
| Protocol Data | PostgreSQL | Daily snapshots | Indefinite |
| File Attachments | S3 | Cross-region replication | 7 years |
| Analytics Data | TimescaleDB | Daily snapshots | 2 years |
| Cache Data | Redis | None | 24 hours |

## 4. Security Architecture

### 4.1 Authentication Flow

```mermaid
sequenceDiagram
    participant C as Client
    participant G as API Gateway
    participant A as Auth Service
    participant D as Database
    
    C->>G: Login Request
    G->>A: Validate Credentials
    A->>D: Query User
    D-->>A: User Data
    A-->>G: Generate JWT
    G-->>C: Return Token
    
    C->>G: API Request + JWT
    G->>A: Validate Token
    A-->>G: Token Valid
    G->>D: Process Request
    D-->>G: Response
    G-->>C: Return Data
```

### 4.2 Security Monitoring

```mermaid
flowchart TD
    A[Security Events] --> B{Event Type}
    B -->|Authentication| C[Auth Monitor]
    B -->|Data Access| D[Access Monitor]
    B -->|System| E[System Monitor]
    
    C --> F[Auth Logs]
    D --> G[Audit Logs]
    E --> H[System Logs]
    
    F --> I[SIEM]
    G --> I
    H --> I
    
    I --> J[Alert System]
    J --> K[Security Team]
```

## 5. API Architecture

### 5.1 API Layer Structure

| Layer | Implementation | Purpose |
|-------|---------------|----------|
| Gateway | Kong | Rate limiting, authentication |
| Routing | Django Ninja | Endpoint routing, validation |
| Controllers | Service Classes | Business logic |
| Models | Django ORM | Data access |

### 5.2 API Standards

- RESTful endpoint design
- JWT authentication
- Rate limiting: 100 requests/minute
- Versioning: URI-based (v1, v2)
- Response format: JSON
- Error handling: RFC 7807

## 6. Deployment Architecture

### 6.1 Container Orchestration

```mermaid
graph TD
    A[Route 53] --> B[CloudFront]
    B --> C[ALB]
    C --> D[ECS Cluster]
    D --> E[Web Service]
    D --> F[API Services]
    D --> G[Background Workers]
    
    F --> H[(RDS Multi-AZ)]
    F --> I[(ElastiCache)]
    G --> J[SQS Queues]
    
    K[AWS WAF] --> B
    L[CloudWatch] --> D
```

### 6.2 Scaling Strategy

| Service | Scaling Trigger | Scale Out | Scale In |
|---------|----------------|-----------|-----------|
| Web | CPU > 70% | +1 instance | -1 instance |
| API | CPU > 70% | +1 instance | -1 instance |
| Workers | Queue depth > 1000 | +2 instances | -1 instance |
| Database | Storage > 80% | Storage increase | N/A |

### 6.3 Monitoring and Alerting

- Infrastructure: CloudWatch metrics
- Application: Prometheus + Grafana
- Logs: ELK Stack
- Traces: AWS X-Ray
- Alerts: PagerDuty integration

---

**Note:** This architecture document is maintained by the Backend Team and reviewed quarterly. For updates or clarifications, please contact the team leads.