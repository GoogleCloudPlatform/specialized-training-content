## Project
Cymbal Meet Agentic System Demo — simulated AI agent for customer success. Monitors engagement metrics, identifies issues, and deploys interventions automatically. Built for 20-30 minute instructor-led demos.

## Architecture decisions
- **Backend**: Flask 3.0.0 (app.py) on port 5001 locally, 8080 on Cloud Run
- **Frontend**: Vanilla JS + HTML + CSS, served as static files
- **Data**: CSV files (company, contact, activity) loaded into memory at startup
- **Engagement**: Pre-generated metrics with deterministic seed (42)
- **Agent narration**: SSE streaming with 0.3s delay between lines
- **State**: In-memory dict, resets on server restart or POST /api/reset
- Flat project structure (app.py at root, not inside backend/)
- 7 problem customers trigger interventions (companies 1, 2, 3, 4, 6, 8, 17)
- 3 intervention types: admin_email (auto), inapp_calendar (needs approval), device_email (auto)
- Demo date hardcoded: February 10, 2026
- Chart.js for metric visualizations

## Tasks to complete


## Current state

| Component              | Status |
| ---------------------- | ------ |
| Flask backend + APIs   | done   |
| CSV data files         | done   |
| Engagement metrics     | done   |
| Agent analyzer         | done   |
| Agent decision engine  | done   |
| Agent executor + SSE   | done   |
| Landing page           | done   |
| CSM Dashboard          | done   |
| CRM system view        | done   |
| Backend Admin panel    | done   |
| End-user client        | done   |
| Admin Inbox            | done   |
| Agent narration window | done   |
| Approval workflow      | done   |
| Reset endpoint         | done   |
| Dockerfile + Cloud Run | done   |
| Docker container test  | done   |
| Full end-to-end QA     | done   |

## File structure

```
app.py                          # Flask server + all API routes
agent/
  analyzer.py                   # Issue detection (metrics >20% below target)
  decision_engine.py            # Intervention selection logic
  executor.py                   # Agent workflow + narration generation
data/
  company.csv                   # 24 customers (8 Enterprise, 8 Mid-Market, 8 SMB)
  contact.csv                   # 72 contacts (3 per company)
  activity.csv                  # Historical activity log
  engagement.py                 # Metric generation with trend profiles
  load_data.py                  # CSV parsing utilities
frontend/
  index.html                    # Landing page
  shared/styles.css             # Common styles
  csm-dashboard/index.html      # Customer list + detail + interventions
  crm/index.html                # Customer records + activity feed
  backend-admin/index.html      # In-app messaging campaigns
  client/index.html             # Simulated video app + slideout messages
  inbox/index.html              # Agent-generated email viewer
  agent-narration/index.html    # Real-time agent execution log
  admin/index.html              # Additional admin view
Dockerfile                      # Cloud Run deployment
requirements.txt                # flask==3.0.0, flask-cors==4.0.0
cymbal-meet-agent-prd.md        # Full PRD (reference)
```

## How to run

```bash
python app.py                    # http://localhost:5001
# or
docker build -t cymbal-meet . && docker run -p 8080:8080 cymbal-meet
```
