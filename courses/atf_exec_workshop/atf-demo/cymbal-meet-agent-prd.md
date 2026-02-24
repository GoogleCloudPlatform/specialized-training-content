# Product Requirements Document: Cymbal Meet Agentic System Demo

## Document Version History

**Version 2.0 (As Implemented)** - This document has been updated to reflect the actual implementation.

### Key Changes from Original Specification:
- **Technology Stack**: Confirmed Flask 3.0.0 as the backend framework
- **Data Storage**: Uses CSV files (`company.csv`, `contact.csv`, `activity.csv`) loaded at startup
- **Default Port**: Changed to 5001 for local development (8080 for Cloud Run)
- 
- **Application Routes**: RESTful API structure with `/api/*` endpoints instead of HTML routes
- **Email Rendering**: Dynamic generation in frontend from intervention data (not static HTML files)
- **Engagement Metrics**: Pre-generated at startup with deterministic random seed
- **Demo Date**: Standardized to February 10, 2026 throughout
- **Customer Names**: Uses actual company names from CSV (Nexus Tech, GreenLeaf, etc.)
- **Chart Library**: Implemented with Chart.js
- **Frontend Structure**: Single-page applications with shared styles
- **State Management**: Global in-memory state dictionary, managed by Flask app
- **Agent Narration**: SSE streaming with configurable 0.3s delay between messages

---

## 1. Executive Summary

### 1.1 Purpose
This document specifies requirements for a demonstration application that simulates an agentic system for Cymbal Meet, a videoconferencing solution company. The demo illustrates how AI agents can automatically identify customer engagement issues and implement interventions to improve product adoption and usage.

### 1.2 Target Audience
- **Primary Users**: Instructors demonstrating the system
- **Viewers**: Executive stakeholders evaluating agentic capabilities

### 1.3 Core Objective
Create a realistic simulation of an autonomous customer success agent that monitors engagement metrics, identifies issues, recommends interventions, and updates business systems—without requiring actual data integration or real-time processing.

---

## 2. Product Overview

### 2.1 Business Context
**Cymbal Meet** sells:
- Physical conference room devices ("boxes")
- SaaS software licenses for individual users

**Problem**: Customers often underutilize purchased products, leading to churn risk and missed expansion opportunities.

**Solution**: An autonomous agent that runs weekly to detect engagement shortfalls and execute interventions automatically or with CSM approval.

### 2.2 System Components
The demo simulates five interconnected applications:

1. **Agent System** - Core autonomous decision engine
2. **CSM Dashboard** - Customer success manager interface
3. **CRM System** - Customer relationship management
4. **Backend Admin Panel** - Configuration for in-app messaging
5. **End-User Client** - Simulated videoconferencing application

---

## 3. Technical Architecture

### 3.1 Technology Stack
- **Backend**: Python 3.11+ with Flask 3.0.0
- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **Data Storage**: In-memory data structures with CSV data loading (resets on server restart)
- **Deployment**: Docker container compatible with Google Cloud Run
- **Development**: Local server on port 5001 (configurable via PORT environment variable)
- **Dependencies**: Flask-CORS for AJAX support

### 3.2 Application Structure
```
atf-demo/
├── backend/
│   ├── app.py                 # Main Flask server
│   ├── data/
│   │   ├── company.csv        # Customer company data (24 records)
│   │   ├── contact.csv        # Contact data (72 records, 3 per company)
│   │   ├── activity.csv       # Initial activity log
│   │   ├── engagement.py      # Engagement metrics generation
│   │   └── load_data.py       # CSV data loaders
│   ├── agent/
│   │   ├── analyzer.py        # Engagement analysis logic
│   │   ├── decision_engine.py # Intervention selection
│   │   └── executor.py        # Agent workflow execution with narration
│   └── utils/                 # (Reserved for future utilities)
├── frontend/
│   ├── index.html             # Demo landing page
│   ├── shared/
│   │   └── styles.css         # Common styles across all views
│   ├── csm-dashboard/
│   │   └── index.html         # CSM Dashboard with customer list and detail
│   ├── crm/
│   │   └── index.html         # CRM system view
│   ├── backend-admin/
│   │   └── index.html         # In-app messaging campaign management
│   ├── client/
│   │   └── index.html         # Simulated video client with slideouts
│   ├── inbox/
│   │   └── index.html         # Agent-generated email viewer
│   ├── agent-narration/
│   │   └── index.html         # Real-time agent execution window
│   └── admin/
│       └── index.html         # (Additional admin view)
├── requirements.txt           # Python dependencies
├── README.md                  # Setup and usage instructions
└── Dockerfile                 # Container configuration
```

### 3.3 Deployment Modes
- **Local Development**: `python backend/app.py` → Access at `http://localhost:5001` (port configurable via PORT env var)
- **Docker**: `docker build -t cymbal-meet-demo .` → `docker run -p 8080:8080 cymbal-meet-demo`
- **Cloud Run**: Deploy container to GCP Cloud Run for shareable URL (automatically uses PORT env var)

---

## 4. Data Model

### 4.1 Data Storage

**Implementation**: Data is stored in CSV files and loaded into memory at server startup. All data structures are Python lists of dictionaries. State persists only during server runtime and resets on restart.

#### Customer Data (company.csv)
```csv
company_id,name,segment,industry,total_employees,in_office_employees,total_conf_rooms,purchased_boxes,licensed_users,annual_contract_value,contract_start_year,mdm_system
```

**Fields**:
- `company_id` (int): Unique identifier (1-24)
- `name` (str): Company name
- `segment` (str): Enterprise, Mid-Market, or SMB
- `industry` (str): Tech, Healthcare, Logistics, Manufacturing, Finance, etc.
- `total_employees` (int): Total workforce
- `in_office_employees` (int): Number of office-based employees
- `total_conf_rooms` (int): Total conference rooms
- `purchased_boxes` (int): Physical devices owned
- `licensed_users` (int): Software seats
- `annual_contract_value` (int): Total yearly revenue
- `contract_start_year` (str): Year customer started
- `mdm_system` (str): Mobile Device Management system (if any)

#### Contact Data (contact.csv)
```csv
contact_id,company_id,full_name,role,is_primary
```

**Fields**:
- `contact_id` (int): Unique identifier
- `company_id` (int): Foreign key to company
- `full_name` (str): Contact's full name
- `role` (str): Job title/role (Admin, IT Manager, Executive, etc.)
- `is_primary` (bool): Whether this is the primary contact

#### Activity Data (activity.csv)
```csv
activity_id,company_id,activity_date,type,note
```

**Fields**:
- `activity_id` (int): Unique identifier
- `company_id` (int): Foreign key to company
- `activity_date` (str): Date in YYYY-MM-DD format
- `type` (str): Activity type (Support, CSM Note, Agent Intervention, etc.)
- `note` (str): Activity description

**Note**: The agent appends new activity records to the in-memory activities list when it runs.

### 4.2 Mock Data Requirements
- **24 customers** across different segments and industries
- **2-5 contacts per customer** (at least one admin contact per customer)
- **Engagement metrics** for rolling 30-day window (generated daily data points)
- **Most customers** (70-80%) performing within 20% of targets
- **Some customers** (20-30%) with one or more metrics >20% below target

### 4.3 Engagement Metrics

#### Tracked Metrics
| Metric | Description | Target Formula | Sliding Window |
|--------|-------------|----------------|----------------|
| 7DA Users | Daily active users (7-day average) | 70% × licensed_users | 30 days |
| 7D Call Volume | Calls per week | 7 × licensed_users | 30 days |
| Device Utilization | Hours per day per device | 5 hours/device/day | 30 days |
| 7D Dial-in Sessions | Phone dial-in usage | 20% × call_volume | 30 days |
| Calendared Meetings | Meetings scheduled via extension | 70% × call_volume | 30 days |
| End-of-Call Feedback | User satisfaction ratings | N/A (sentiment analysis) | 30 days |

#### Engagement Trends
Mock data should include:
- **Growing trends**: Customers performing well (3-5 customers)
- **Flat trends**: Stable usage (10-15 customers)
- **Declining trends**: At-risk customers (5-8 customers)

---

## 5. Agent System

### 5.1 Execution Schedule
- **Real System**: Runs automatically every Monday at 6:00 AM
- **Demo System**: Manual trigger via "Run Like It's Monday" button in CSM Dashboard

### 5.2 Agent Workflow

**Demo Date**: February 10, 2026 (hardcoded in executor.py as DEMO_DATE)

#### Phase 1: Data Collection
1. Query engagement metrics for all customers
2. Calculate rolling 30-day averages:
   - For each metric, take the average of the last 30 daily data points
   - Example: 7DA Users = average of daily active user counts from Jan 11 - Feb 9 (30 days)
   - This provides a smoothed view of recent performance trends
3. Compare actuals vs. targets
4. Identify customers with metrics >20% below target

**Implementation Note**: Engagement data is pre-generated at server startup for consistency. The agent processes this pre-calculated data rather than generating it on-the-fly.

#### Phase 2: Issue Analysis
For each underperforming customer:
1. Identify which specific metrics are below threshold
2. Retrieve end-of-call feedback themes (positive and negative)
3. Analyze customer profile (segment, industry, product usage)

#### Phase 3: Intervention Design
Based on identified issues, agent selects from intervention catalog:

**Intervention Type 1: Admin Weekly Email** (Auto-executed)
- **Trigger**: Any metric >20% below target
- **Content Sections**:
  - Performance highlights (metrics exceeding peer cohorts)
  - Positive end-of-call feedback themes
  - Areas for improvement (metrics below target)
  - Negative end-of-call feedback themes
  - Feature recommendation (personalized to customer)
- **Delivery**: Simulated email to primary admin contact

**Intervention Type 2: In-App Messaging - Calendar Extension Adoption** (Requires CSM approval)
- **Trigger**: Calendared meetings >20% below target (demo will show customer at ~50% of target)
- **Root Cause Analysis**:
  - Low extension installation rate
  - Installed but not actively using
- **Demo Requirements**:
  - System must be able to display Message A to a specific simulated user without the extension
  - System must be able to display Message B to a specific simulated user with extension but no meetings scheduled
- **Actions**:
  - **Message A**: Target users without extension
    - Headline: "Schedule Meetings Faster"
    - Body: Explain benefits, link to Chrome extension, link to video tutorial
    - CTA: "Install Now"
  - **Message B**: Target users with extension but low usage
    - Headline: "Get More from Your Meeting Scheduler"
    - Body: Usage tips, link to how-to guide
    - CTA: "Watch Tutorial" + "Ask Questions"

**Intervention Type 3: Device Performance Remediation** (Auto-executed)
- **Trigger**: 25% of call sessions with frame rate <20fps OR resolution <720p in past week
- **Analysis**: Identify specific devices and their performance metrics
- **Actions**:
  - Generate HTML email to admin with:
    - List of underperforming devices (name, location, metrics)
    - Step-by-step remediation instructions:
      1. Run on-device bandwidth test
      2. Run on-device video test
      3. Switch from WiFi to wired Ethernet (if applicable)
      4. If wired, test bandwidth on laptop via same connection
      5. If bandwidth <1.5 Mbps, engage network team
      6. If device fails video test after network fixes, initiate RMA
    - Support contact information

#### Phase 4: Execution
1. **Auto-executed interventions**:
   - Generate email HTML
   - **Simulate sending email** (add to narration: "✓ Email sent to [contact name]")
   - Log activity to CRM
   - Update CSM dashboard status
2. **Approval-required interventions**:
   - Surface in CSM dashboard customer detail page
   - Show intervention details and preview
   - Update backend admin panel configuration (disabled state, pending approval)
   - Log proposed intervention to CRM
   - **When instructor approves**:
     - Intervention status changes to "Approved - Deploying"
     - Backend admin panel updated to show campaigns as "Enabled"
     - CRM activity log updated with approval entry
     - In-app messages become active/visible in end-user client
     - Toast notification confirms: "Intervention approved and deployed"

#### Phase 5: System Updates
- Create activity records in CRM for each intervention
- Update CSM dashboard with intervention status
- Prepare backend admin panel with pending configurations

### 5.3 Agent Narration Window

When instructor clicks "Run Like It's Monday":
1. Open new browser window/tab with narration interface
2. Display step-by-step progress updates (text-based, no progress bar)
3. Simulate processing 3 customers in detail:

**Example Narration Flow**:
```
Cymbal Meet Agent — Weekly Run
---

Collecting engagement data for 24 customers...
✓ Engagement data collected

Analyzing metrics against targets...
✓ Found 7 customers with engagement issues

---
Processing: Nexus Tech
---

Issue identified: 7DA Users 25% below target (1,703 actual vs 2,433 target)
Issue identified: Calendared Meetings 48% below target (8,934 actual vs 17,032 target)

Scanning internal documentation...
✓ Found relevant articles on engagement and adoption

Selecting intervention: Admin Weekly Email
Generating personalized content...
  ├─ Highlighting: Device Utilization at 94% of target
  ├─ Highlighting: Dial-in Sessions at 108% of target
  ├─ Addressing: 7DA Users below target
  ├─ Addressing: Calendared Meetings below target
  ├─ Recommending: User Onboarding Webinar Series
  ├─ Remediation for 7DA Users: Inactive User Re-engagement Drip
  ├─ Remediation for Calendared Meetings: Calendar Extension In-App Messaging Campaign
✓ Email generated and queued for delivery

Selecting intervention: Calendar Extension In-App Messaging
Root cause analysis:
  ├─ Extension installed: 42% of users
  ├─ Extension active usage: 29% of installed users
Creating two-part messaging campaign...
  ├─ Message A: Installation prompt (2,016 users)
  ├─ Message B: Usage encouragement (1,460 users)
⚠ Intervention requires CSM approval - surfacing in dashboard

Updating external systems...
  ✓ CRM activity logged (2 entries)
  ✓ CSM dashboard updated
  ✓ Backend admin panel configured

---
Processing: GreenLeaf
---

Issue identified: Device Call Sessions 26% below target
Issue identified: Dial-in Sessions 25% below target

Scanning internal documentation...
✓ Found relevant articles on engagement and adoption

Selecting intervention: Admin Weekly Email
[... content generation details ...]
✓ Email generated and queued for delivery

Selecting intervention: Device Performance Remediation Email
Analyzing device metrics...
  ├─ Found 3 devices with performance issues
  ├─ Conference Room A - Main: 18fps avg, 680p (Low FPS, Low Resolution)
  ├─ Training Room 1: 14fps avg, 720p (Low FPS)
  ├─ Executive Boardroom: 19fps avg, 480p (Low FPS, Low Resolution)
Generating remediation instructions...
✓ Email generated and queued for delivery

Updating external systems...
  ✓ CRM activity logged (2 entries)
  ✓ CSM dashboard updated

---
Processing: BlueHorizon
---

[... similar processing ...]

---

Processing remaining 4 customers with similar workflows...

Done — Agent run complete

Summary:
  • 7 customers processed with interventions
  • 5 admin emails queued for delivery
  • 2 in-app messaging campaigns pending CSM approval
  • 2 device remediation emails queued
  • 14 CRM activity records created
  • 7 CSM dashboard updates applied
```

4. Instructor dismisses window when ready
5. Demo state updated—systems now show post-agent-run state

---

## 6. User Interface Specifications

### 6.1 Demo Landing Page (`/`)

**Purpose**: Starting point for demonstrations

**Layout**:
```
┌─────────────────────────────────────────────────────────┐
│  🎥 Cymbal Meet - Agentic System Demo                   │
│                                                          │
│  Select a system to demonstrate:                        │
│                                                          │
│  ┌──────────────────┐  ┌──────────────────┐            │
│  │  CSM Dashboard   │  │   CRM System     │            │
│  │                  │  │                  │            │
│  │  Monitor customer│  │  Customer data & │            │
│  │  engagement and  │  │  activity logs   │            │
│  │  interventions   │  │                  │            │
│  │                  │  │                  │            │
│  │  [Open]          │  │  [Open]          │            │
│  └──────────────────┘  └──────────────────┘            │
│                                                          │
│  ┌──────────────────┐  ┌──────────────────┐            │
│  │  Backend Admin   │  │  End-User Client │            │
│  │                  │  │                  │            │
│  │  Configure in-app│  │  Video conference│            │
│  │  messaging       │  │  application     │            │
│  │                  │  │                  │            │
│  │  [Open]          │  │  [Open]          │            │
│  └──────────────────┘  └──────────────────┘            │
│                                                          │
│  ┌──────────────────┐                                   │
│  │  Admin Inbox     │                                   │
│  │                  │                                   │
│  │  View agent-     │                                   │
│  │  generated emails│                                   │
│  │                  │                                   │
│  │  [Open]          │                                   │
│  └──────────────────┘                                   │
│                                                          │
│  Demo Instructions:                                     │
│  1. Start with CSM Dashboard to see "before" state      │
│  2. Click "Run Like It's Monday" to trigger agent       │
│  3. Review "after" state in all systems                 │
│  4. Approve pending interventions in CSM Dashboard      │
│  5. See approved interventions in Backend Admin         │
│  6. View customer emails in Admin Inbox                 │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### 6.2 CSM Dashboard (`/csm-dashboard`)

#### 6.2.1 Dashboard Home (Customer List)

**Top Bar**:
- Cymbal Meet logo (left)
- Navigation: Customers | Reports
- User profile dropdown (right)
- **[Run Like It's Monday]** button (prominent, primary color)

**Main Content**:

**Customer List Table**
```
┌─────────────────────────────────────────────────────────┐
│ All Customers (24)                  [Search...] [Filter]│
│                                                          │
│ Name                  Segment      Health       Status  │
│ ─────────────────────────────────────────────────────── │
│ Nexus Tech           Enterprise   🟡 Needs      🔔 New  │
│                                    Attention    ⚙️ Active│
│                                                          │
│ GreenLeaf            SMB          🟢 Healthy    ⚙️ Active│
│                                                          │
│ BlueHorizon          Enterprise   🟢 Healthy    —       │
│                                                          │
│ Summit Peak          SMB          🟡 Needs      🔔 New  │
│                                    Attention             │
│                                                          │
│ Nova Retail          Enterprise   🟢 Healthy    ⚙️ Active│
│                                                          │
│ Apex Mfg             Mid-Market   🟡 Needs      🔔 New  │
│                                    Attention             │
│                                                          │
│ Swift Delivery       SMB          🟢 Healthy    —       │
│                                                          │
│ [... 17 more customers]                                 │
│                                                          │
│                                      [Load More]         │
└─────────────────────────────────────────────────────────┘

Health Status Legend:
🟢 Healthy - All metrics within acceptable range
🟡 Needs Attention - One or more metrics 20-40% below target
(Note: "At Risk" status removed - no customers should be this category)

Intervention Status Indicators:
🔔 New - New intervention requiring approval
⚙️ Active - Intervention currently underway
— - No active interventions
```

**Interaction**:
- Click on customer name → Navigate to customer detail page
- Search filters customer list
- Most customers should show "Healthy" or "Needs Attention"

#### 6.2.2 Customer Detail Page

**Layout**: Two-column layout with main content area and intervention sidebar

**Header**:
```
← Back to Customers

Nexus Tech
Enterprise • Tech • Customer since 2023
Account Owner: Sarah Chen
Primary Contact: Morgan Black (CIO)
```

**Main Content Area (Left ~70%)**:

**Engagement Metrics Dashboard (Single Comprehensive Card)**:
```
┌─────────────────────────────────────────────────────────┐
│ Engagement Performance - Last 30 Days                    │
│                                                          │
│ 7DA Users                              Target: 2,433    │
│ Actual: 1,703 (70% of target) 🟡                        │
│ ┌─────────────────────────────────────────────────────┐│
│ │ 3000│                                                ││
│ │     │ ─ ─ ─ ─ Target (2,433) ─ ─ ─ ─ ─ ─ ─ ─ ─   ││
│ │ 2500│                                                ││
│ │ 2000│     ════════════════════                       ││
│ │ 1500│ ════                        ════════           ││
│ │ 1000│                                                ││
│ │  500│                                                ││
│ │    0│──────────────────────────────────────────────││
│ │     Jan 10        Jan 25         Feb 8              ││
│ └─────────────────────────────────────────────────────┘│
│                                                          │
│ 7D Call Volume                         Target: 24,332   │
│ Actual: 22,189 (91% of target) 🟢                       │
│ [Similar chart]                                          │
│                                                          │
│ Device Utilization (hrs/day)           Target: 730 hrs  │
│ Actual: 685 hrs (94% of target) 🟢                      │
│ [Similar chart]                                          │
│                                                          │
│ 7D Dial-in Sessions                    Target: 4,866    │
│ Actual: 5,234 (108% of target) 🟢                       │
│ [Similar chart]                                          │
│                                                          │
│ Calendared Meetings                    Target: 17,032   │
│ Actual: 8,934 (52% of target) 🔴                        │
│ [Similar chart]                                          │
│                                                          │
│ End-of-Call Feedback                   Avg: 3.9 / 5.0   │
│ Sentiment: 🟡 Mixed (68% positive, 24% negative)        │
│ [Trend chart]                                            │
└─────────────────────────────────────────────────────────┘
```

**Intervention Sidebar (Right ~30%)**:

```
┌────────────────────────────────────┐
│ Interventions                      │
│                                    │
│ ⚠️ PENDING APPROVAL                │
│ ┌────────────────────────────────┐│
│ │ In-App Messaging               ││
│ │ Calendar Extension Adoption    ││
│ │                                ││
│ │ Created: Feb 10, 6:15 AM       ││
│ │ Targets: 1,244 users           ││
│ │                                ││
│ │ Issue: Calendared meetings at  ││
│ │ 52% of target                  ││
│ │                                ││
│ │ Root Cause:                    ││
│ │ • 42% extension install rate   ││
│ │ • 29% usage among installed    ││
│ │                                ││
│ │ Proposed Actions:              ││
│ │ • Message A: Install prompt    ││
│ │   (721 users no extension)     ││
│ │ • Message B: Usage tips        ││
│ │   (523 users w/ extension)     ││
│ │                                ││
│ │ [View Details]                 ││
│ │ [Approve] [Reject]             ││
│ └────────────────────────────────┘│
│                                    │
│ ✅ ACTIVE INTERVENTIONS            │
│ ┌────────────────────────────────┐│
│ │ Admin Weekly Email             ││
│ │ Sent: Feb 10, 6:15 AM          ││
│ │ To: Morgan Black               ││
│ │                                ││
│ │ • Highlighted: Device util,    ││
│ │   dial-in usage                ││
│ │ • Addressed: Low 7DA users,    ││
│ │   calendar meetings            ││
│ │ • Recommended: User Onboarding ││
│ │   Webinar Series               ││
│ │                                ││
│ │ [View Email]                   ││
│ └────────────────────────────────┘│
│                                    │
│ 📜 INTERVENTION HISTORY            │
│ ┌────────────────────────────────┐│
│ │ Feb 3: Admin Weekly Email      ││
│ │ Jan 27: Admin Weekly Email     ││
│ │ Jan 20: Admin Weekly Email     ││
│ │                                ││
│ │ [View All]                     ││
│ └────────────────────────────────┘│
└────────────────────────────────────┘
```

**Intervention Detail Modal** (when clicking "View Details"):
```
┌─────────────────────────────────────────────────────────┐
│ Intervention Details                            [Close] │
│                                                          │
│ In-App Messaging: Calendar Extension Adoption           │
│ Created: February 10, 2026 at 6:15 AM by Cymbal Agent   │
│                                                          │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                          │
│ 🎯 Issue Identified:                                    │
│ Calendared meetings at 52% of target (8,934 vs 17,032)  │
│                                                          │
│ 🔍 Root Cause Analysis:                                 │
│ Agent analyzed user behavior and found:                 │
│ • Extension installation rate: 42% (1,459 of 3,476)     │
│ • Active usage rate: 29% (423 of 1,459 installed)       │
│                                                          │
│ 📋 Proposed Solution:                                   │
│                                                          │
│ Message A: Installation Prompt                          │
│ Target: 721 users without extension installed           │
│                                                          │
│ ┌────────────────────────────────────────────────────┐ │
│ │ 📅 Schedule Meetings Faster                         │ │
│ │                                                     │ │
│ │ Save time and reduce friction! Install the Cymbal  │ │
│ │ Meet scheduler extension to add video meetings     │ │
│ │ directly from your calendar.                       │ │
│ │                                                     │ │
│ │ 🔗 Install Chrome Extension                        │ │
│ │ 🎥 Watch 2-Minute Tutorial                         │ │
│ │                                                     │ │
│ │                               [Dismiss] [Install]   │ │
│ └────────────────────────────────────────────────────┘ │
│                                                          │
│ Message B: Usage Encouragement                          │
│ Target: 523 users with extension but low usage          │
│                                                          │
│ ┌────────────────────────────────────────────────────┐ │
│ │ 🚀 Get More from Your Meeting Scheduler            │ │
│ │                                                     │ │
│ │ We noticed you have the Cymbal Meet extension      │ │
│ │ installed—great! Here are some tips to make        │ │
│ │ scheduling even easier:                            │ │
│ │                                                     │ │
│ │ • One-click meeting creation from any calendar     │ │
│ │ • Automatic dial-in number inclusion               │ │
│ │ • Smart room booking based on attendees            │ │
│ │                                                     │ │
│ │ 📖 View Full Guide                                 │ │
│ │ 💬 Ask a Question                                  │ │
│ │                                                     │ │
│ │                  [Dismiss] [Watch Tutorial]         │ │
│ └────────────────────────────────────────────────────┘ │
│                                                          │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                          │
│                                   [Approve] [Reject]     │
└─────────────────────────────────────────────────────────┘
```

**Approval Action Result**:
When instructor clicks "Approve":
1. Modal closes
2. Intervention moves from "Pending Approval" to "Active Interventions" section
3. Status badge changes to "✅ Approved - Deploying"
4. Toast notification: "Intervention approved. Backend systems updated and deployment initiated."
5. Backend admin panel shows campaigns as "Enabled"
6. CRM activity log shows new entry: "CSM approved in-app messaging intervention"
7. End-user client can now display the slideout messages

### 6.3 CRM System (`/crm`)

**Purpose**: Show customer data and activity logs updated by agent

**Note**: No actual filtering or editing functionality required - display only

**Layout**:
```
┌─────────────────────────────────────────────────────────┐
│ Cymbal CRM                                    [Search...│
│                                                          │
│ Customers | Contacts | Activities | Reports             │
│                                                          │
│ ┌─────────────────────────────────────────────────────┐│
│ │ Customer: Nexus Tech                                ││
│ │                                                      ││
│ │ Basic Information:                                   ││
│ │ • Segment: Enterprise                                ││
│ │ • Industry: Tech                                     ││
│ │ • Employees: 3,722 (2,605 in-office)                ││
│ │ • Contract Value: $709,120/year                      ││
│ │                                                      ││
│ │ Product Usage:                                       ││
│ │ • Licensed Users: 3,476                              ││
│ │ • Purchased Boxes: 146                               ││
│ │ • Conference Rooms: 173                              ││
│ │                                                      ││
│ │ Primary Contact:                                     ││
│ │ • Morgan Black - CIO                                 ││
│ │ • morgan.black@nexustech.com                        ││
│ │                                                      ││
│ │ Recent Activities:                        [View All] ││
│ │ ─────────────────────────────────────────────────── ││
│ │ Feb 10, 2026 - Agent Intervention                   ││
│ │ In-app messaging campaign proposed for CSM approval ││
│ │ Re: Calendar extension adoption                     ││
│ │                                                      ││
│ │ Feb 10, 2026 - Agent Intervention                   ││
│ │ Weekly admin email sent to Morgan Black             ││
│ │ Re: Engagement performance and recommendations      ││
│ │                                                      ││
│ │ Feb 7, 2026 - Support                               ││
│ │ Hardware health check passed. Recommended a refresh ││
│ │ for legacy units in 2027.                           ││
│ │                                                      ││
│ │ Feb 5, 2026 - Renewal Discussion                    ││
│ │ Performed scheduled firmware update on all          ││
│ │ purchased boxes.                                    ││
│ │                                                      ││
│ │ Jan 30, 2026 - Support                              ││
│ │ Performed scheduled firmware update on all          ││
│ │ purchased boxes.                                    ││
│ └─────────────────────────────────────────────────────┘│
│                                                          │
│ [Show Next Customer]                                     │
└─────────────────────────────────────────────────────────┘
```

**Key Features**:
- Display customer details from schema
- Show activity feed with new agent-generated entries after agent run
- Filter activities by type: All | Agent | CSM | Support | Sales

### 6.4 Backend Admin Panel (`/backend-admin`)

**Purpose**: Configuration interface for in-app messaging

**Layout**:
```
┌─────────────────────────────────────────────────────────┐
│ Cymbal Meet Admin                                        │
│                                                          │
│ Configuration | Users | Analytics | System               │
│                                                          │
│ In-App Messaging Campaigns                   [+ Create] │
│                                                          │
│ Customer: [Acme Corporation ▼]                          │
│                                                          │
│ ┌─────────────────────────────────────────────────────┐│
│ │ Active Campaigns                                     ││
│ │                                                      ││
│ │ Type          Name                 Start      End    ││
│ │ ──────────────────────────────────────────────────  ││
│ │ 🟢 Slideout   Calendar Ext Install Jan 13    Jan 27 ││
│ │              (No Extension)                          ││
│ │                                                      ││
│ │ 🟢 Slideout   Calendar Ext Usage   Jan 13    Jan 27 ││
│ │              (Installed Users)                       ││
│ │                                                      ││
│ │ 🔵 Banner     Welcome New Users    Jan 1     Feb 1  ││
│ │                                                      ││
│ └─────────────────────────────────────────────────────┘│
│                                                          │
│ ┌─────────────────────────────────────────────────────┐│
│ │ Pending Campaigns (Awaiting Approval)                ││
│ │                                                      ││
│ │ Type          Name                 Created By        ││
│ │ ──────────────────────────────────────────────────  ││
│ │ ⏸ Slideout   [No campaigns pending]                 ││
│ └─────────────────────────────────────────────────────┘│
│                                                          │
│ Legend:                                                  │
│ 🟢 Enabled  🔴 Disabled  ⏸ Pending Approval  🔵 Scheduled│
└─────────────────────────────────────────────────────────┘
```

**State Changes**:
- **Before agent approval**: Pending section empty OR campaigns in "Pending" state
- **After agent approval**: Campaigns move to "Active" with 🟢 Enabled status

### 6.5 End-User Client (`/client`)

**Purpose**: Simulated video conferencing application showing in-app messaging

**Layout** (based on uploaded client.html):
```
┌─────────────────────────────────────────────────────────┐
│ Cymbal Meet                                    👤 John D.│
│                                                          │
│ [Start Meeting]  [Join Meeting]  [Schedule]  [Settings] │
│                                                          │
│ ┌─────────────────────────────────────────────────────┐│
│ │                                                      ││
│ │            Your next meeting:                        ││
│ │            Team Standup                              ││
│ │            Today at 2:00 PM                          ││
│ │                                                      ││
│ │            [Join Now]                                ││
│ │                                                      ││
│ └─────────────────────────────────────────────────────┘│
│                                                          │
│ Recent Meetings:                                         │
│ • Weekly All-Hands - Jan 12, 10:00 AM                   │
│ • Product Review - Jan 11, 3:00 PM                      │
│ • Client Presentation - Jan 10, 1:00 PM                 │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

**Slideout Notification** (appears from right side after intervention approval):
```
                              ┌────────────────────────┐
                              │ 📅 Schedule Meetings   │
                              │    Faster              │
                              │                        │
                              │ Save time and reduce   │
                              │ friction! Install the  │
                              │ Cymbal Meet scheduler  │
                              │ extension to add video │
                              │ meetings directly from │
                              │ your calendar.         │
                              │                        │
                              │ 🔗 Install Chrome      │
                              │    Extension           │
                              │                        │
                              │ 🎥 Watch 2-Minute      │
                              │    Tutorial            │
                              │                        │
                              │        [Dismiss]       │
                              └────────────────────────┘
```

**Interaction**:
- Slideout slides in from right after 2-second delay
- Can be dismissed with [X] or [Dismiss]
- Demonstrates where agent-configured messages appear

### 6.6 Admin Inbox (`/inbox`)

**Purpose**: Show agent-generated emails

**Layout**:
```
┌─────────────────────────────────────────────────────────┐
│ Inbox                                      james.chen@...│
│                                                          │
│ ┌─────────┐ ┌─────────────────────────────────────────┐│
│ │ Inbox   │ │ Subject                          Date    ││
│ │ Sent    │ │                                          ││
│ │ Drafts  │ │ ✉️  Your Weekly Cymbal Meet      Jan 13 ││
│ │ Spam    │ │     Performance Report                   ││
│ │         │ │     Cymbal Meet Agent                    ││
│ │         │ │                                          ││
│ │         │ │ ✉️  Team Meeting Recap           Jan 12 ││
│ │         │ │     Sarah Johnson                        ││
│ │         │ │                                          ││
│ │         │ │ 📎 Q4 Budget Approval            Jan 10 ││
│ │         │ │     Finance Team                         ││
│ │         │ │                                          ││
│ └─────────┘ └─────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ Email Preview                                            │
│                                                          │
│ From: Cymbal Meet Agent <success@cymbalmeet.com>        │
│ To: james.chen@acmecorp.com                             │
│ Date: Monday, January 13, 2025 6:15 AM                  │
│ Subject: Your Weekly Cymbal Meet Performance Report     │
│                                                          │
│ ┌─────────────────────────────────────────────────────┐│
│ │ [Email content rendered as HTML - see section 6.6.1] ││
│ └─────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────┘
```

#### 6.6.1 Admin Email Template

**Implementation Note**: Admin emails are generated dynamically when the agent runs. The inbox view (`/inbox`) displays these emails by rendering the intervention data into HTML format. Each email includes the actual engagement metrics, feedback themes, feature recommendations, and remediations that were calculated for that specific customer.

**Email Structure**:

Emails are rendered based on intervention data with the following structure:

```html
<!DOCTYPE html>
<html>
<head>
  <style>
    /* Use brand colors from uploaded styling reference */
    body { font-family: 'Segoe UI', sans-serif; color: #333; }
    .header { background: #1976D2; color: white; padding: 20px; }
    .section { padding: 20px; border-bottom: 1px solid #eee; }
    .metric { display: inline-block; margin: 10px; padding: 15px; 
              background: #f5f5f5; border-radius: 8px; }
    .positive { color: #2E7D32; }
    .negative { color: #C62828; }
    .feature-box { background: #E3F2FD; padding: 15px; 
                   border-left: 4px solid #1976D2; margin: 10px 0; }
  </style>
</head>
<body>
  <div class="header">
    <h1>🎥 Cymbal Meet Weekly Report</h1>
    <p>Performance insights for Nexus Tech</p>
    <p>Week of February 3-9, 2026</p>
  </div>

  <div class="section">
    <h2>🌟 You're Excelling In:</h2>
    <div class="metric">
      <strong>Device Utilization</strong><br>
      <span class="positive">685 hours/day total</span><br>
      <small>94% of target, 12% above peer average</small>
    </div>
    <div class="metric">
      <strong>Dial-in Usage</strong><br>
      <span class="positive">5,234 sessions</span><br>
      <small>108% of target, 18% above peer average</small>
    </div>
    
    <h3>What your users are saying:</h3>
    <ul>
      <li>"Audio quality is excellent, even on dial-in"</li>
      <li>"Love the screen sharing - very smooth"</li>
      <li>"Easy to join meetings from any device"</li>
    </ul>
  </div>

  <div class="section">
    <h2>📊 Opportunities for Improvement:</h2>
    <div class="metric">
      <strong>Active Users (7-Day Avg)</strong><br>
      <span class="negative">1,703 of 3,476 licensed</span><br>
      <small>30% below target engagement</small>
    </div>
    <div class="metric">
      <strong>Calendared Meetings</strong><br>
      <span class="negative">8,934 vs 17,032 target</span><br>
      <small>48% below expected adoption</small>
    </div>
    
    <h3>Common feedback themes:</h3>
    <ul>
      <li>"Wish more of my team used this regularly"</li>
      <li>"Calendar integration could be better"</li>
      <li>"Some users still default to other tools"</li>
    </ul>
    
    <h3>Recommendations:</h3>
    <p>Consider hosting a <strong>User Onboarding Webinar Series</strong> 
       to drive awareness and adoption across your organization. Our 
       customer success team can help coordinate tailored sessions for 
       different user groups.</p>
    <p><a href="#">Schedule a consultation →</a></p>
  </div>

  <div class="section">
    <h2>✨ Feature Spotlight: User Onboarding Webinar Series</h2>
    <div class="feature-box">
      <p><strong>Perfect for your organization size (3,476 users)</strong></p>
      <p>Many Enterprise customers in the Tech sector have increased active 
         usage by 40%+ through structured onboarding programs. We recommend:</p>
      <ul>
        <li>Department-specific training sessions (30 min)</li>
        <li>"Power user" certification for team champions</li>
        <li>Monthly office hours for ongoing support</li>
      </ul>
      <p><a href="#" style="color: #1976D2; font-weight: bold;">
         Learn more and schedule →</a></p>
    </div>
  </div>

  <div class="section" style="text-align: center; color: #666;">
    <p>Questions? Reply to this email or contact your CSM: Sarah Chen</p>
    <p style="font-size: 12px;">
      Cymbal Meet | 123 Tech Parkway | San Francisco, CA 94107
    </p>
  </div>
</body>
</html>
```

**Personalization Logic**:
- Company name, metrics, and contact info pulled from customer data
- Positive metrics selected from those >80% of target
- Negative metrics selected from those <80% of target
- Feature recommendations based on:
  - **Enterprise segment + low active users** → Onboarding webinar series
  - **Mid-Market segment + low calendar usage** → Calendar extension training
  - **SMB segment + low dial-in** → Dial-in feature guide
  - **Any segment + device issues** → (separate device email, see 6.6.2)

#### 6.6.2 Device Performance Email Template

**Sent to**: Customers with 25%+ of sessions below quality threshold

```html
<!DOCTYPE html>
<html>
<head>
  <style>
    /* Similar styling to admin email */
    .device-table { width: 100%; border-collapse: collapse; }
    .device-table th { background: #f5f5f5; padding: 10px; text-align: left; }
    .device-table td { padding: 10px; border-bottom: 1px solid #eee; }
    .alert { background: #FFF3E0; padding: 15px; border-left: 4px solid #F57C00; }
    .steps { counter-reset: step; }
    .steps li { counter-increment: step; margin: 15px 0; }
    .steps li::before { content: counter(step); background: #1976D2; 
                        color: white; border-radius: 50%; padding: 5px 10px; 
                        margin-right: 10px; }
  </style>
</head>
<body>
  <div class="header">
    <h1>⚠️ Device Performance Alert</h1>
    <p>GreenLeaf - Action Required</p>
  </div>

  <div class="section">
    <div class="alert">
      <strong>We've detected video quality issues on some of your devices</strong>
      <p>27% of your call sessions this week experienced frame rate drops 
         or reduced resolution. This typically impacts user experience and 
         meeting effectiveness.</p>
    </div>

    <h2>Affected Devices:</h2>
    <table class="device-table">
      <thead>
        <tr>
          <th>Device Name</th>
          <th>Location</th>
          <th>Avg Frame Rate</th>
          <th>Avg Resolution</th>
          <th>Issues</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>Conference Room A</td>
          <td>Building 1, Floor 2</td>
          <td>17 fps</td>
          <td>680p</td>
          <td>Low FPS, Low Res</td>
        </tr>
        <tr>
          <td>Conference Room C</td>
          <td>Building 1, Floor 3</td>
          <td>14 fps</td>
          <td>720p</td>
          <td>Low FPS</td>
        </tr>
        <tr>
          <td>Training Room 1</td>
          <td>Building 2, Floor 1</td>
          <td>19 fps</td>
          <td>480p</td>
          <td>Low FPS, Low Res</td>
        </tr>
      </tbody>
    </table>
  </div>

  <div class="section">
    <h2>🔧 Recommended Troubleshooting Steps:</h2>
    <ol class="steps">
      <li>
        <strong>Run on-device bandwidth test</strong><br>
        Navigate to Settings → Diagnostics → Network Test on each device.
        Target: >5 Mbps upload, >10 Mbps download
      </li>
      <li>
        <strong>Run on-device video test</strong><br>
        Settings → Diagnostics → Video Test. Verify camera can capture 
        1080p @ 30fps minimum.
      </li>
      <li>
        <strong>Check network connection type</strong><br>
        If device is on WiFi, switch to wired Ethernet if available. 
        WiFi can cause inconsistent performance in conference rooms.
      </li>
      <li>
        <strong>Verify network bandwidth</strong><br>
        If device is wired, connect a laptop to the same Ethernet port 
        and run speedtest.net. Target: >1.5 Mbps per device.
      </li>
      <li>
        <strong>Engage network team if needed</strong><br>
        If bandwidth is <1.5 Mbps consistently, work with your IT/network 
        team to investigate:
        <ul>
          <li>Port configuration or VLAN settings</li>
          <li>QoS (Quality of Service) prioritization for video traffic</li>
          <li>Upstream bandwidth limitations</li>
        </ul>
      </li>
      <li>
        <strong>Consider device RMA</strong><br>
        If device passes network tests but still shows poor video 
        performance, the hardware may be faulty. Contact Cymbal Support 
        to initiate a Return Merchandise Authorization (RMA).
      </li>
    </ol>
  </div>

  <div class="section">
    <h2>📞 Need Help?</h2>
    <p>Our technical support team is here to assist:</p>
    <ul>
      <li><strong>Email:</strong> support@cymbalmeet.com</li>
      <li><strong>Phone:</strong> 1-800-CYMBAL-1 (24/7)</li>
      <li><strong>Live Chat:</strong> Available in your admin portal</li>
    </ul>
    <p>Reference ticket number: <strong>DEV-2026-0210-GL</strong></p>
  </div>

  <div class="section" style="text-align: center; color: #666;">
    <p style="font-size: 12px;">
      Cymbal Meet | 123 Tech Parkway | San Francisco, CA 94107
    </p>
  </div>
</body>
</html>
```

---

## 7. Brand Identity & Styling

### 7.1 Visual Design System

Based on uploaded reference file, create a cohesive identity for Cymbal Meet:

**Color Palette**:
- Primary: `#1976D2` (blue - professional, trustworthy)
- Secondary: `#0D47A1` (dark blue - headers, emphasis)
- Accent: `#FFA726` (orange - CTAs, highlights)
- Success: `#2E7D32` (green - positive metrics)
- Warning: `#F57C00` (orange - alerts)
- Error: `#C62828` (red - negative metrics)
- Neutral Gray: `#616161` (text)
- Light Gray: `#F5F5F5` (backgrounds)
- White: `#FFFFFF`

**Typography**:
- Headings: `Segoe UI`, fallback to system sans-serif
- Body: `Segoe UI`, fallback to system sans-serif
- Monospace: `Consolas`, `Monaco`, monospace (for metrics, IDs)

**Component Patterns**:
- **Cards**: White background, subtle shadow, 8px border radius
- **Buttons**: 
  - Primary: Blue background, white text
  - Secondary: White background, blue border
  - Danger: Red background, white text
- **Metrics Indicators**:
  - Above target: Green with ↑ arrow
  - Within 20% of target: Yellow/amber with → arrow
  - Below 20% of target: Red with ↓ arrow
- **Charts**: Line charts with blue actual line, dashed gray target line

**Logo**:
Simple text-based logo:
```
🎥 Cymbal Meet
```
Use throughout applications in top-left corner.

### 7.2 Responsive Design
- Desktop-first (demo will be presented on large screens)
- Minimum supported: 1280x720 resolution
- No mobile optimization required

---

## 8. Demo Flow & User Instructions

### 8.1 Recommended Demo Sequence

**Setup (Before Presentation)**:
1. Start server: `python backend/app.py` (runs on http://localhost:5001 by default) or `docker run -p 8080:8080 cymbal-meet-demo`
2. Open landing page: `http://localhost:5001` (or deployed URL)
3. Keep all application tabs ready in browser

**Demo Sequence (20-30 minutes)**:

**Act 1: The "Before" State (5-7 minutes)**
1. Open CSM Dashboard
   - Show customer list with health indicators
   - Click on "Nexus Tech" (company_id: 1)
   - Highlight metrics below target (red indicators)
   - Show empty or minimal intervention history
2. Open CRM
   - Show customer data
   - Show activity feed (mostly manual CSM notes)
3. Open Backend Admin
   - Show current in-app campaigns (none agent-created)

**Act 2: Agent Activation (3 minutes)**
1. Return to CSM Dashboard
2. Click **"Run Like It's Monday"** button
3. Agent narration window opens—walk through:
   - Data collection across 24 customers
   - Issue identification (7 customers with problems)
   - Detailed processing of 3 customers
   - Intervention generation and system updates
4. Dismiss narration window

**Act 3: The "After" State (10-15 minutes)**
1. **CSM Dashboard** (refresh if needed):
   - Show "Pending Approvals" section with 2 interventions
   - Show "Active Interventions" section with 5 deployed
   - Click into Nexus Tech detail page
   - Show new intervention cards
   - Click "Preview" on pending in-app messaging campaign
   - Show message preview modal
   - Click **"Approve"**
   - Toast notification confirms approval

2. **Backend Admin Panel**:
   - Refresh to show newly enabled campaigns
   - Point out campaigns now in "Active" with green status

3. **End-User Client**:
   - Show normal meeting interface
   - Slideout notification appears (simulating approved intervention)
   - Demonstrate user experience of agent-generated message

4. **Admin Inbox**:
   - Show inbox list with new emails from "Cymbal Meet Agent"
   - Open one admin weekly email
   - Walk through sections:
     - Performance highlights
     - Areas for improvement
     - Feature recommendation
   - (Optional) Open device performance email for different customer (e.g., GreenLeaf)

5. **CRM**:
   - Return to Nexus Tech record
   - Show new activity entries logged by agent
   - Highlight timestamps matching agent run

**Act 4: Q&A and Exploration (5-10 minutes)**
- Answer questions
- Navigate to other customers to show variety of interventions
- Demonstrate rejection workflow if interested

### 8.2 Landing Page Instructions

Include on landing page:
```
🎯 Demo Instructions

This demo simulates an AI agent that automatically monitors customer 
engagement and implements interventions to improve product adoption.

Recommended Demo Flow:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. BEFORE STATE (5 min)
   → Open CSM Dashboard
   → Review customer "Nexus Tech" - note red metrics
   → Check CRM - see mostly manual activity
   → Check Backend Admin - see existing campaigns only

2. ACTIVATE AGENT (3 min)
   → Return to CSM Dashboard
   → Click "Run Like It's Monday"
   → Watch agent narration window
   → Dismiss when complete

3. AFTER STATE (10 min)
   → CSM Dashboard: Approve pending interventions
   → Backend Admin: See newly enabled campaigns
   → End-User Client: See in-app message appear
   → Admin Inbox: Read agent-generated emails
   → CRM: See logged agent activities

4. EXPLORATION (5-10 min)
   → Answer questions
   → Show different customer scenarios
   → Demonstrate other interventions

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Key Points to Emphasize:
✓ Agent runs autonomously every Monday
✓ Analyzes 24 customers in minutes
✓ Creates personalized interventions
✓ Some auto-execute (emails), some need approval (in-app)
✓ Updates CRM, CSM dashboard, backend systems automatically
✓ All decisions based on internal documentation (simulated)
```

---

## 9. Data Generation Requirements

### 9.1 Customer Data

**Implementation**: Customer data is stored in CSV files in `backend/data/` directory and loaded at server startup.

**Actual Files**:
- `company.csv` - 24 customers with complete profile information
- `contact.csv` - 72 contacts (3 per customer, at least one primary per company)
- `activity.csv` - Historical activity records from January-February 2026

**Customer Distribution** (from company.csv):
- 8 Enterprise customers
- 8 Mid-Market customers  
- 8 SMB customers

**Industry Distribution**:
- Tech (5 customers)
- Healthcare (3 customers)
- Logistics (3 customers)
- Manufacturing (3 customers)
- Finance (2 customers)
- Retail (3 customers)
- Legal (2 customers)
- Energy (1 customer)
- Security (1 customer)
- Media (1 customer)
- Education (1 customer)

**Notable Features**:
- Some customers have MDM (Mobile Device Management) systems listed (Jamf Pro, Microsoft Intune, VMware Workspace ONE)
- Contract start years range from 2021-2024
- Annual contract values range from ~$15K (SMB) to ~$1.3M (Enterprise)

**Agent-Generated Activities**:
When the agent runs, it appends new activity records to the in-memory activities list with:
- `type`: "Agent Intervention"
- `activity_date`: "2026-02-10" (DEMO_DATE constant)
- `note`: Description of intervention action taken

### 9.2 Engagement Data Generation

**Implementation**: Engagement metrics are generated at server startup by `backend/data/engagement.py` using a fixed random seed (42) for reproducibility.

For each customer, the system generates:
- 30 days of daily metrics
- Target calculations based on customer profile
- Average calculations across the 30-day window
- Feedback comments (20-50 per customer)
- Trend classification (growing, flat, declining)

**Target Calculations** (from engagement.py):
```python
def calculate_targets(customer):
    return {
        "7da_users": customer["licensed_users"] * 0.70,
        "call_volume": customer["licensed_users"] * 7,  # 1 call/day/user
        "device_utilization": customer["purchased_boxes"] * 5,  # 5 hrs/device/day
        "dialin_sessions": customer["licensed_users"] * 7 * 0.20,
        "calendar_meetings": customer["licensed_users"] * 7 * 0.70,
    }
```

**Problem Customers** (hardcoded profiles in engagement.py):
- Company 1 (Nexus Tech): Low 7DA users (75%), low calendar meetings (48%)
- Company 2 (GreenLeaf): Device performance issues, low dial-in sessions
- Company 3 (BlueHorizon): Low call volume (76%)
- Company 4 (Summit Peak): Low 7DA users (76%), low calendar meetings (55%)
- Company 6 (Apex Mfg): Low calendar meetings (50%)
- Company 8 (Vanguard Health): Low dial-in sessions (76%)
- Company 17 (Velocity Motors): Low 7DA users (75%)

These suppression percentages ensure metrics fall below the 80% threshold, triggering agent interventions.

### 9.3 End-of-Call Feedback

**Implementation**: Feedback comments are randomly selected from predefined templates in `engagement.py` and assigned to each customer based on their engagement performance.

Generate 20-50 feedback comments per customer from the following pools:

**Positive Comments** (POSITIVE_COMMENTS in engagement.py):
- "Audio quality is consistently excellent"
- "Screen sharing is smooth and reliable"
- "Very easy to join meetings from any device"
- "Love the mobile app - works great on the go"
- "Connection is always stable"
- "Interface is intuitive and clean"
- "Best video quality we've seen"
- "Dial-in option is super helpful for remote folks"
- "Integration with our calendar is seamless"
- "Recording feature is fantastic for documentation"

**Negative Comments** (NEGATIVE_COMMENTS in engagement.py):
- "Wish more of our team actually used this regularly"
- "Calendar integration could be much better"
- "Some features are hard to discover"
- "We still default to a competitor for important meetings"
- "Connection drops occasionally during calls"
- "Audio echo issues in some conference rooms"
- "Mobile app drains battery quickly"
- "Too many steps to schedule a meeting"
- "Learning curve is steeper than expected"
- "Need better admin controls for user management"

**Neutral Comments** (NEUTRAL_COMMENTS in engagement.py):
- "Works fine for our needs"
- "Does what we need it to do"
- "Good enough"
- "No major complaints"
- "Pretty standard videoconferencing tool"
- "Gets the job done"
- "Meets expectations"

**Sentiment Trigger**: If negative feedback exceeds 30% of total comments, the agent flags it as an issue requiring intervention.

### 9.4 Contact Data

**Implementation**: Contact data is loaded from `backend/data/contact.csv` with 72 total contacts (3 per company).

For each customer, the CSV provides 2-5 contacts with:
- At least 1 with `is_primary=True` (typically with role containing "Admin", "IT", "Director", "CIO", etc.)
- Other contacts with varied roles: "Manager", "Executive", "Team Lead", "Specialist", "VP", "Coordinator", etc.

The agent selects the primary contact as the default recipient for admin emails and device performance alerts.

---

## 10. Agent Logic Specifications

### 10.1 Issue Detection Algorithm

**Actual Implementation** (from `backend/agent/analyzer.py`):

```python
def find_issues(company, engagement_data):
    """
    Check a company's engagement data for underperforming metrics.
    Returns a list of issue dicts, one per problem metric.
    Empty list means the company is healthy.
    """
    targets = engagement_data["targets"]
    averages = engagement_data["averages"]
    issues = []

    metric_names = [
        "7da_users", "call_volume", "device_utilization",
        "dialin_sessions", "calendar_meetings",
    ]

    for metric in metric_names:
        target = targets[metric]
        actual = averages[metric]
        if target == 0:
            continue
        ratio = actual / target
        if ratio < 0.80:  # More than 20% below target
            issues.append({
                "metric": metric,
                "actual": actual,
                "target": target,
                "ratio": round(ratio, 2),
                "gap_pct": round((1 - ratio) * 100),
            })

    # Check feedback sentiment
    feedback = engagement_data["feedback"]
    if feedback:
        negative_count = sum(
            1 for c in feedback if c in NEGATIVE_COMMENTS
        )
        negative_pct = negative_count / len(feedback)
        if negative_pct > 0.30:
            issues.append({
                "metric": "feedback_sentiment",
                "actual": round(negative_pct, 2),
                "target": 0.20,
                "ratio": round(1 - negative_pct, 2),
                "gap_pct": round((negative_pct - 0.20) * 100),
            })

    return issues
```

### 10.2 Intervention Selection Logic

**Actual Implementation** (from `backend/agent/decision_engine.py`):

The `select_interventions()` function returns a list of intervention dictionaries based on identified issues.

**INTERVENTION 1: Admin Weekly Email**
- **Trigger**: ANY issue found (always generated if customer has problems)
- **Auto-execute**: Yes
- **Content Includes**:
  - `highlights`: List of metrics performing above 80% of target (with percentile rankings)
  - `improvements`: List of metrics below 80% of target (with gap percentages)
  - `feature_rec`: Personalized feature recommendation based on segment and primary issue
  - `feedback_positive`: 2-3 themed positive feedback summaries
  - `feedback_negative`: 2-3 themed negative feedback summaries
  - `remediations`: Metric-specific remediation actions (see below)

**INTERVENTION 2: Calendar Extension In-App Messaging**
- **Trigger**: `calendar_meetings` ratio < 0.80 (below 80% of target)
- **Auto-execute**: No (requires CSM approval)
- **Root Cause Analysis**:
  - Calculates simulated extension installation rate (35-55%)
  - Calculates simulated usage rate among installed (20-40%)
- **Creates Two Messages**:
  - **Message A**: Target users without extension (installation prompt)
  - **Message B**: Target users with extension but low usage (usage tips)
- **Associated Campaigns**: Creates 2 pending backend campaign records

**INTERVENTION 3: Device Performance Email**
- **Trigger**: Device utilization issue OR company flagged in PROBLEM_PROFILES with device_issues
- **Auto-execute**: Yes
- **Content**: 
  - Lists 2-5 problem devices with specific metrics (FPS, resolution)
  - Each device shows issues: "Low FPS" and/or "Low Resolution"
  - Includes locations (Building/Floor)

**Remediation Selection**: The `select_remediations()` function chooses specific actions based on:
- **Metric type**: Different remediations for 7DA users, dial-in, call volume, calendar, etc.
- **CRM signals**: Checks activity history for keywords to tailor recommendations
- **Company attributes**: Uses segment, MDM system, and other profile data

Example remediations:
- Low 7DA users → Executive Sponsor Kit OR Inactive User Re-engagement Drip
- Low dial-in → MDM-specific deployment guide OR manual reference card
- Low call volume → Contest/gamification OR department rollout playbook
- Low calendar → In-app messaging (separate intervention) OR integration guide

### 10.3 Feature Recommendation Logic

```python
def select_feature_recommendation(customer):
    issues = customer["issues"]
    segment = customer["segment"]
    
    # Decision tree for feature recommendations
    if any(i["metric"] == "7da_users" for i in issues):
        if segment == "Enterprise":
            return {
                "name": "User Onboarding Webinar Series",
                "description": "Structured training for new and existing users",
                "relevance": "Your organization size (1,600 users) benefits from formal onboarding",
                "cta_link": "https://cymbalmeet.com/enterprise-onboarding"
            }
        elif segment == "Mid-Market":
            return {
                "name": "Team Champion Program",
                "description": "Designate and train power users in each department",
                "relevance": "Mid-sized teams see 35% higher adoption with internal champions",
                "cta_link": "https://cymbalmeet.com/champion-program"
            }
        else:  # SMB
            return {
                "name": "Quick Start Video Series",
                "description": "5-minute tutorials covering essential features",
                "relevance": "Get your team productive fast with bite-sized training",
                "cta_link": "https://cymbalmeet.com/quickstart"
            }
    
    elif any(i["metric"] == "calendar_meetings" for i in issues):
        return {
            "name": "Calendar Integration Masterclass",
            "description": "Live workshop on maximizing scheduler productivity",
            "relevance": "Customers using our calendar features save 2hrs/week per user",
            "cta_link": "https://cymbalmeet.com/calendar-workshop"
        }
    
    elif any(i["metric"] == "dialin_sessions" for i in issues):
        return {
            "name": "Global Dial-In Expansion Pack",
            "description": "50+ countries with local numbers for better accessibility",
            "relevance": "Reduce barriers for remote and international participants",
            "cta_link": "https://cymbalmeet.com/global-dialin"
        }
    
    else:
        # Default recommendation
        return {
            "name": "Meeting Analytics Dashboard",
            "description": "Track usage patterns and identify optimization opportunities",
            "relevance": "Data-driven insights to improve meeting culture",
            "cta_link": "https://cymbalmeet.com/analytics"
        }
```

---

## 11. Technical Implementation Notes

### 11.1 State Management

**Actual Implementation** (from `backend/app.py`):

**Data loaded at server start**:
```python
companies = load_companies()          # List of 24 company dicts
contacts = load_contacts()            # List of 72 contact dicts
activities = load_activities()        # List of activity dicts
engagement = generate_all_metrics(companies)  # Dict keyed by company_id

# Utility lookups
companies_by_id = {c["company_id"]: c for c in companies}

# Keep original activities for reset functionality
original_activities = list(activities)
```

**Runtime state** (mutated by agent and user actions):
```python
state = {
    "agent_has_run": False,           # Boolean flag
    "interventions": [],              # List of intervention dicts
    "backend_campaigns": [],          # List of campaign dicts
    "emails": [],                     # List of email dicts
}

# ID counters for new records
next_activity_id = max(a["activity_id"] for a in activities) + 1
next_intervention_id = 1
```

**After Agent Run**:
```python
state["agent_has_run"] = True
state["interventions"] = results["interventions"]
state["emails"] = results["emails"]
state["backend_campaigns"] = results["campaigns"]
activities.extend(results["activities"])
```

**After CSM Approval**:
```python
intervention["status"] = "approved"
intervention["approved_at"] = "2026-02-10"

# Enable associated campaigns
for campaign in state["backend_campaigns"]:
    if campaign.get("intervention_id") == intervention_id:
        campaign["status"] = "enabled"

# Log to CRM
activities.append(new_approval_activity)
```

**Reset Functionality**:
```python
@app.route("/api/reset", methods=["POST"])
def api_reset():
    state["agent_has_run"] = False
    state["interventions"] = []
    state["backend_campaigns"] = []
    state["emails"] = []
    activities.clear()
    activities.extend(original_activities)
    return jsonify({"status": "reset"})
```

### 11.2 API Endpoints

**Static Files**
- `GET /` - Landing page HTML
- `GET /<path>` - Serves static files from frontend directory

**Companies API**
- `GET /api/companies` - Returns all companies with health status and intervention counts
- `GET /api/companies/<int:company_id>` - Returns full detail for one company including engagement, contacts, activities, and interventions

**Contacts API**
- `GET /api/contacts/<int:company_id>` - Returns contacts for specific company

**Activities API**
- `GET /api/activities/<int:company_id>` - Returns activity log for specific company (sorted by date, descending)

**Engagement API**
- `GET /api/engagement/<int:company_id>` - Returns engagement metrics (targets, averages, daily data, trend, feedback)

**Interventions API**
- `GET /api/interventions` - Returns all interventions across all companies
- `GET /api/interventions/<int:company_id>` - Returns interventions for specific company
- `POST /api/interventions/<int:intervention_id>/approve` - Approves a pending intervention
- `POST /api/interventions/<int:intervention_id>/reject` - Rejects a pending intervention

**State API**
- `GET /api/state` - Returns agent run state (has_run, counts)

**Campaigns API**
- `GET /api/campaigns` - Returns all backend campaigns
- `GET /api/campaigns/<int:company_id>` - Returns campaigns for specific company

**Emails API**
- `GET /api/emails` - Returns all agent-generated emails
- `GET /api/emails/<int:email_id>` - Returns specific email detail

**Agent Execution**
- `POST /api/agent/run` - Triggers agent execution, streams narration via Server-Sent Events (SSE)

**Demo Control**
- `POST /api/reset` - Resets all state back to initial condition

### 11.3 Narration Stream

Agent narration streams updates to frontend via Server-Sent Events (SSE):

**Backend Implementation**:
```python
@app.route("/api/agent/run", methods=["POST"])
def api_agent_run():
    """
    Trigger the agent. Streams narration lines as Server-Sent Events.
    After the stream ends, state is updated with interventions/emails/etc.
    """
    if state["agent_has_run"]:
        return jsonify({"error": "Agent has already run. Restart server to reset."}), 400

    def generate():
        results = None
        for line in run_agent(companies, contacts, engagement, activities, delay=0.3):
            if isinstance(line, dict) and "__results__" in line:
                results = line["__results__"]
            else:
                yield f"data: {json.dumps({'message': line})}\n\n"

        # Apply results to global state
        if results:
            state["agent_has_run"] = True
            state["interventions"] = results["interventions"]
            state["emails"] = results["emails"]
            state["backend_campaigns"] = results["campaigns"]
            activities.extend(results["activities"])

        yield f"data: {json.dumps({'message': 'COMPLETE'})}\n\n"

    return Response(generate(), mimetype="text/event-stream")
```

**Frontend Implementation**:
```javascript
const eventSource = new EventSource('/api/agent/run', { method: 'POST' });
eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.message === 'COMPLETE') {
    eventSource.close();
    // Enable close button or refresh UI
  } else {
    appendNarrationLine(data.message);
  }
};
```

**Narration Delay**: The executor uses a configurable delay (default 0.3s) between narration lines for realistic pacing during demonstrations.

### 11.4 Docker Configuration

**Dockerfile**:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/
COPY frontend/ ./frontend/

ENV PORT=8080
ENV PYTHONUNBUFFERED=1

CMD python backend/app.py
```

**requirements.txt**:
```
flask==3.0.0
flask-cors==4.0.0
```

**Environment Variables**:
- `PORT`: Server port (default 5001 for local, 8080 for Cloud Run)
- `DEBUG`: Enable Flask debug mode for local development (default "true" for local)

---

## 12. Success Criteria

The demo is successful if:

1. **Instructor can complete full demo in 20-30 minutes**
2. **Agent narration clearly explains what's happening**
3. **Before/after states visibly different**:
   - CSM dashboard shows new interventions
   - CRM shows new activities
   - Backend admin shows new campaigns
   - Inbox shows new emails
4. **Approval workflow functions smoothly**
5. **All UI components render correctly on 1280x720+ displays**
6. **No errors or crashes during typical demo flow**
7. **Visual design is professional and cohesive**
8. **Simulated data feels realistic and varied**

---

## 13. Out of Scope

The following are explicitly NOT required:

- Real video conferencing functionality
- Actual email sending (SMTP)
- Database persistence
- User authentication
- Real-time collaboration
- Mobile responsiveness
- Accessibility (WCAG) compliance
- Internationalization
- Actual LLM integration for sentiment analysis
- Real Chrome extension
- Integration with actual CRM systems
- Production-grade error handling
- Comprehensive test coverage
- Performance optimization for scale

---

## 14. Appendix A: Data Files

### 14.1 Customer Data Files

**Implementation**: Data files are located in `backend/data/` directory:

- **company.csv** - 24 customer records with complete profiles
  - Includes: company_id, name, segment, industry, employee counts, device/license counts, ACV, contract year, MDM system
  - Loaded by `load_data.py` at server startup
  
- **contact.csv** - 72 contact records (3 per company, at least one primary per company)
  - Includes: contact_id, company_id, full_name, role, is_primary
  - Loaded by `load_data.py` at server startup

- **activity.csv** - Historical activity logs from January-February 2026
  - Includes: activity_id, company_id, activity_date, type, note
  - Loaded by `load_data.py` at server startup
  - Agent appends new activities to in-memory list during execution

**Data Loading**: The `load_data.py` module provides three functions:
- `load_companies()` - Returns list of company dictionaries
- `load_contacts()` - Returns list of contact dictionaries  
- `load_activities()` - Returns list of activity dictionaries

All functions parse CSV files and convert numeric fields to appropriate Python types (int, bool).

### 14.2 Feedback Comment Templates

**Positive**:
- "Audio quality is consistently excellent"
- "Screen sharing is smooth and reliable"
- "Very easy to join meetings from any device"
- "Love the mobile app - works great on the go"
- "Connection is always stable"
- "Interface is intuitive and clean"
- "Best video quality we've seen"
- "Dial-in option is super helpful for remote folks"
- "Integration with our calendar is seamless"
- "Recording feature is fantastic for documentation"

**Negative**:
- "Wish more of our team actually used this regularly"
- "Calendar integration could be much better"
- "Some features are hard to discover"
- "We still default to [competitor] for important meetings"
- "Connection drops occasionally during calls"
- "Audio echo issues in some conference rooms"
- "Mobile app drains battery quickly"
- "Too many steps to schedule a meeting"
- "Learning curve is steeper than expected"
- "Need better admin controls for user management"

**Neutral**:
- "Works fine for our needs"
- "Does what we need it to do"
- "Good enough"
- "No major complaints"
- "Pretty standard videoconferencing tool"
- "Gets the job done"
- "Meets expectations"

---

## 15. Appendix B: Additional Considerations

### 15.1 Error Handling

While production-grade error handling is out of scope, implement basic safety:
- If agent run fails, show error in narration window
- If approval fails, show toast notification
- Graceful degradation if data is missing

### 15.2 Performance

- Pre-generate all 30-day metric data on server start (don't calculate on-demand)
- Cache email HTML templates
- Limit chart rendering to necessary data points (30 max)

### 15.3 Browser Compatibility

- Test on Chrome/Edge (primary)
- Firefox support nice-to-have
- Safari support not required

### 15.4 Future Enhancements (Not in Scope)

Ideas for future iterations if demo is successful:
- Real-time chart animations
- Multiple agent runs (week-over-week comparison)
- CSM notes/comments on interventions
- Intervention effectiveness metrics
- Customer segmentation filters
- Export reports as PDF
- Multi-language support
- Actual AI integration for content generation

---

## 16. Implementation Decisions

**Actual Implementation Choices**:

1. **Backend Framework**: Flask 3.0.0 (with Flask-CORS for AJAX support)
2. **Data Storage**: CSV files (`company.csv`, `contact.csv`, `activity.csv`) loaded at server startup into in-memory Python lists
3. **Engagement Metrics**: Pre-generated at server startup using deterministic random seed for consistency
4. **Brand Assets**: Text-only logo with emoji (`🎥 Cymbal Meet`)
5. **Chart Library**: Chart.js for engagement metric visualizations
6. **Email Rendering**: Dynamic HTML generation in frontend based on intervention data (not static templates)
7. **Deployment**: Google Cloud Run compatible (Docker container with PORT environment variable)
8. **Demo Duration**: Designed for 20-30 minute demonstrations
9. **Default Port**: 5001 for local development, 8080 for Cloud Run
10. **Agent Narration**: Server-Sent Events (SSE) with configurable delay (0.3s default) between messages
11. **State Management**: Global in-memory state dictionary, resets on server restart
12. **Customer Count**: 24 customers across 3 segments (Enterprise, Mid-Market, SMB)
13. **Problem Customers**: 7 customers with engagement issues triggering agent interventions
14. **Intervention Types**: 3 types implemented - admin_email, inapp_calendar, device_email

---

## 17. Delivery Checklist

**Code Deliverables**:
- [ ] Python backend server (Flask/FastAPI)
- [ ] All frontend HTML/CSS/JS files
- [ ] Mock data generation scripts
- [ ] Dockerfile and deployment config
- [ ] README with setup instructions

**Documentation**:
- [ ] Demo flow guide
- [ ] API endpoint documentation
- [ ] Data schema documentation
- [ ] Troubleshooting guide

**Testing**:
- [ ] Full demo flow tested end-to-end
- [ ] All customer scenarios verified
- [ ] Different intervention types tested
- [ ] Approval/rejection workflows validated
- [ ] Docker container deployment tested

---

**End of PRD**

*Version 2.0 - As Implemented - February 2026*
*This document has been updated to reflect the actual implementation of the Cymbal Meet Agentic System Demo.*
