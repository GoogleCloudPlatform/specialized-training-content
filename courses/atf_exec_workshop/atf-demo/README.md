# Cymbal Meet — Agentic Innovation Demo

This project serves two purposes:

1. **Presentation**: Slide-style pages that walk an audience through how an organization identifies, evaluates, and pursues agentic innovation opportunities.
2. **Live demo**: A working simulation of an autonomous AI agent for customer success — showing what the end result of that process looks like in practice.

Together they tell a complete story: from "we have a business problem" to "here's an agent solving it."

## Running locally (setting up the server to run on your personal machine)

```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the server
python app.py
```

Open `http://localhost:5001` — this loads the home page with the sidebar and presentation content.

## Deploying to Google Cloud Run

```bash
gcloud run deploy cymbal-meet-demo \
  --source . \
  --region us-central1 \
  --allow-unauthenticated
```

## How it works

The home page (`/`) loads a shell with a **sidebar nav on the left** and a **content pane on the right**. The sidebar steps through the presentation slides and then launches the live demo — all without leaving the page.

Sidebar sections:

| Nav item                | What it loads                                                 |
| ----------------------- | ------------------------------------------------------------- |
| Intro to Cymbal Meet    | Company overview                                              |
| Big Business Problems   | The three problems driving this initiative                    |
| As-Is Process           | Current-state workflow                                        |
| Reimagined Process      | Agentic target-state workflow                                 |
| Agentic Solution Design | How the agent is designed                                     |
| Build Agents            | Implementation approach                                       |
| **Launch Demo**         | Opens the demo app (CSM Dashboard, CRM, Inbox, Client, Admin) |
| Takeaways               | Summary and next steps                                        |

## Presenting

Open `/script` in a separate window or device to follow along with the presenter script.

The contents present here are drawn from [SCRIPT.md](SCRIPT.md). In short: 

1. Open the home page at `/` — the sidebar and first slide load automatically
2. Walk through each section using the sidebar nav
3. Click **Launch Demo** to open the demo app
4. Run the agent, show before/after state, approve interventions
5. Return to the sidebar and finish with Takeaways

## Key endpoints

| URL                    | Purpose                                                |
| ---------------------- | ------------------------------------------------------ |
| `/`                    | Home page — sidebar nav + content pane                 |
| `/demo/`               | Demo landing page (app module cards)                   |
| `/demo/csm-dashboard/` | CSM Dashboard with engagement charts and interventions |
| `/demo/crm/`           | CRM system (contacts, activity history)                |
| `/demo/inbox/`         | Agent-generated emails                                 |
| `/demo/client/`        | End-user client simulation                             |
| `/demo/backend-admin/` | Demo reset and admin controls                          |
| `/script`              | Live presenter script (mirrors SCRIPT.md content)      |

## Disclaimer

**NO WARRANTIES:** This software is provided "as is" without warranty of any kind. Use at your own risk.
