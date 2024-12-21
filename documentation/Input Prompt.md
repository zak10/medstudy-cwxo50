```
# Medical Research Platform PRD

## Executive Summary

### Vision
To democratize medical research by creating a transparent, community-driven platform that enables structured observation and investigation of health interventions, starting with community-led "unstudies" and evolving into formal crowdfunded research.

### Mission
Build a platform that empowers individuals to participate in and contribute to health research through:
- Phase 1: Community-driven observational studies ("unstudies")
- Phase 2: Crowdfunded, IRB-approved formal studies

### Core Value Proposition

#### For Participants:
- Access to structured protocols
- Reduced costs through partnerships
- Community knowledge sharing
- Direct involvement in research
- Access to aggregated results

#### For Supplement Companies:
- Real-world data on products
- Direct access to engaged users
- Marketing opportunities
- Brand credibility
- Product validation

#### For Future Researchers (Phase 2):
- Alternative funding source
- Direct connection to participants
- Reduced administrative overhead
- Streamlined protocols

## Product Overview

### Phase 1: Unstudies Platform

#### 1. Protocol Creation System
- Standardized templates
- Required bloodwork specifications
- Intervention guidelines
- Safety parameters
- Data collection requirements

#### 2. Participant Experience
- Protocol access
- Data submission
- Progress tracking
- Community interaction
- Results access

#### 3. Data Collection
- Quantitative Data:
  - Blood test results
  - Optional biometrics
  - Adherence tracking
  
- Qualitative Data:
  - Weekly check-ins
  - Experience reports
  - Side effect tracking
  - Community discussion

#### 4. Results Classification
- Preliminary Signal (10-25 participants)
- Emerging Pattern (26-50 participants)
- Strong Signal (50+ participants)

### Partnership Integration
- Supplement company verification
- Discount code management
- Quality control requirements
- Data sharing agreements

## Technical Architecture

### System Components

#### 1. Frontend Architecture
```

Web Application (React.js)
├── Public Portal
│   ├── Protocol Discovery
│   ├── User Registration
│   └── Data Submission
├── Participant Dashboard
│   ├── Protocol Progress
│   ├── Data Entry
│   └── Community Features
└── Admin Dashboard
├── Protocol Management
├── Data Analysis
└── Partnership Management

```

#### 2. Backend Services
```

Microservices Architecture
├── User Service
│   ├── Authentication
│   └── Profile Management
├── Protocol Service
│   ├── Template Management
│   └── Data Collection
├── Analysis Service
│   ├── Statistics
│   └── Visualization
└── Community Service
├── Forums
└── Messaging

```

### Data Model

#### 1. Core Entities
```

User
├── Profile
│   ├── Health Data
│   ├── Participation History
│   └── Community Activity
└── Data Submissions
├── Blood Work
├── Check-ins
└── Reports

Protocol
├── Requirements
│   ├── Blood Tests
│   ├── Interventions
│   └── Timeline
├── Participants
│   ├── Active
│   ├── Completed
│   └── Dropped
└── Results
├── Quantitative
├── Qualitative
└── Analysis

```

## Launch Strategy

### MVP Features
- Basic protocol creation
- Data submission system
- Results visualization
- Community forums
- One supplement partnership

### Future Phases
#### Phase 2: Formal Studies
- IRB integration
- Crowdfunding system
- Researcher tools
- Advanced analytics

### Success Metrics
- Number of active protocols
- Participant completion rates
- Data quality metrics
- Community engagement
- Partnership success
- Result reproducibility

### Risk Mitigation
- Clear disclaimers
- Quality control
- Data privacy
- Safety monitoring
- Content moderation
```