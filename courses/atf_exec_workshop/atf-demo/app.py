"""
Cymbal Meet Agentic System Demo - Main Server

Simple Flask app that:
- Serves the frontend static files
- Loads CSV data + generates engagement metrics on startup
- Exposes JSON APIs for all the frontend views
- Manages global state (in-memory, resets on restart)
"""

import json
import os

from flask import Flask, Response, abort, jsonify, request, send_from_directory
from flask_cors import CORS

from agent.executor import run_agent
from data.engagement import generate_all_metrics
from data.load_data import load_activities, load_companies, load_contacts

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = Flask(__name__, static_folder=None)
CORS(app)

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "frontend")
PRESENTATION_DIR = os.path.join(os.path.dirname(__file__), "presentation")
SCRIPT_DIR = os.path.join(os.path.dirname(__file__), "script")

# ---------------------------------------------------------------------------
# Global state — loaded once at startup, mutated by agent run / approvals
# ---------------------------------------------------------------------------

companies = load_companies()
contacts = load_contacts()
activities = load_activities()
engagement = generate_all_metrics(companies)

# Lookup helpers
companies_by_id = {c["company_id"]: c for c in companies}

state = {
    "agent_has_run": False,
    "interventions": [],          # populated by agent run
    "backend_campaigns": [],      # populated by agent run + approvals
    "emails": [],                 # agent-generated emails
}

# Keep a copy of the original activities for reset
original_activities = list(activities)

# Next IDs for new records
next_activity_id = max(a["activity_id"] for a in activities) + 1
next_intervention_id = 1

# ---------------------------------------------------------------------------
# Static file serving
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return send_from_directory(PRESENTATION_DIR, "index.html")


@app.route("/shared/<path:path>")
def shared_files(path):
    """Serve shared assets (CSS, etc.) from frontend/shared/."""
    return send_from_directory(os.path.join(FRONTEND_DIR, "shared"), path)


@app.route("/demo/")
def demo_index():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/demo/<path:path>")
def demo_files(path):
    """Serve any file from frontend/ under the /demo/ prefix."""
    full = os.path.join(FRONTEND_DIR, path)
    if os.path.isfile(full):
        return send_from_directory(FRONTEND_DIR, path)
    index_path = os.path.join(path, "index.html")
    if os.path.isfile(os.path.join(FRONTEND_DIR, index_path)):
        return send_from_directory(FRONTEND_DIR, index_path)
    abort(404)


@app.route("/script")
@app.route("/script/")
def script_index():
    return send_from_directory(SCRIPT_DIR, "index.html")


@app.route("/script/<path:path>")
def script_files(path):
    """Serve presenter script pages from script/."""
    full = os.path.join(SCRIPT_DIR, path)
    if os.path.isfile(full):
        return send_from_directory(SCRIPT_DIR, path)
    abort(404)


@app.route("/presentation/")
def presentation_index():
    return send_from_directory(PRESENTATION_DIR, "index.html")


@app.route("/presentation/<path:path>")
def presentation_files(path):
    """Serve any file from presentation/."""
    full = os.path.join(PRESENTATION_DIR, path)
    if os.path.isfile(full):
        return send_from_directory(PRESENTATION_DIR, path)
    abort(404)

# ---------------------------------------------------------------------------
# API: Companies
# ---------------------------------------------------------------------------

@app.route("/api/companies")
def api_companies():
    """Return all companies with their health status."""
    result = []
    for c in companies:
        cid = c["company_id"]
        eng = engagement[cid]

        # Determine health: check if any metric is >20% below target
        health = "Healthy"
        for metric in ["7da_users", "call_volume", "device_utilization",
                        "dialin_sessions", "calendar_meetings"]:
            actual = eng["averages"][metric]
            target = eng["targets"][metric]
            if target > 0 and actual / target < 0.80:
                health = "Needs Attention"
                break

        # Count pending interventions for this company
        pending = sum(
            1 for iv in state["interventions"]
            if iv["company_id"] == cid and iv["status"] == "pending"
        )
        active = sum(
            1 for iv in state["interventions"]
            if iv["company_id"] == cid
            and iv["status"] in ("approved", "auto_executed")
        )

        result.append({
            **c,
            "health": health,
            "pending_interventions": pending,
            "active_interventions": active,
        })
    return jsonify(result)


@app.route("/api/companies/<int:company_id>")
def api_company_detail(company_id):
    """Return full detail for one company."""
    company = companies_by_id.get(company_id)
    if not company:
        abort(404)

    eng = engagement[company_id]
    company_contacts = [
        c for c in contacts if c["company_id"] == company_id
    ]
    company_activities = sorted(
        [a for a in activities if a["company_id"] == company_id],
        key=lambda a: a["activity_date"],
        reverse=True,
    )
    company_interventions = [
        iv for iv in state["interventions"]
        if iv["company_id"] == company_id
    ]

    return jsonify({
        "company": company,
        "contacts": company_contacts,
        "activities": company_activities,
        "engagement": {
            "targets": eng["targets"],
            "averages": eng["averages"],
            "daily": eng["daily"],
            "trend": eng["trend"],
            "feedback": eng["feedback"],
        },
        "interventions": company_interventions,
    })

# ---------------------------------------------------------------------------
# API: Contacts
# ---------------------------------------------------------------------------

@app.route("/api/contacts/<int:company_id>")
def api_contacts(company_id):
    result = [c for c in contacts if c["company_id"] == company_id]
    return jsonify(result)

# ---------------------------------------------------------------------------
# API: Activities
# ---------------------------------------------------------------------------

@app.route("/api/activities/<int:company_id>")
def api_activities(company_id):
    result = sorted(
        [a for a in activities if a["company_id"] == company_id],
        key=lambda a: a["activity_date"],
        reverse=True,
    )
    return jsonify(result)

# ---------------------------------------------------------------------------
# API: Engagement
# ---------------------------------------------------------------------------

@app.route("/api/engagement/<int:company_id>")
def api_engagement(company_id):
    eng = engagement.get(company_id)
    if not eng:
        abort(404)
    return jsonify({
        "targets": eng["targets"],
        "averages": eng["averages"],
        "daily": eng["daily"],
        "trend": eng["trend"],
        "feedback": eng["feedback"],
    })

# ---------------------------------------------------------------------------
# API: Interventions
# ---------------------------------------------------------------------------

@app.route("/api/interventions")
def api_interventions():
    return jsonify(state["interventions"])


@app.route("/api/interventions/<int:company_id>")
def api_interventions_for_company(company_id):
    result = [
        iv for iv in state["interventions"]
        if iv["company_id"] == company_id
    ]
    return jsonify(result)

# ---------------------------------------------------------------------------
# API: State info
# ---------------------------------------------------------------------------

@app.route("/api/state")
def api_state():
    """Return basic state info (has agent run, counts, etc.)."""
    return jsonify({
        "agent_has_run": state["agent_has_run"],
        "total_interventions": len(state["interventions"]),
        "pending_approvals": sum(
            1 for iv in state["interventions"]
            if iv["status"] == "pending"
        ),
        "total_emails": len(state["emails"]),
        "total_campaigns": len(state["backend_campaigns"]),
    })

# ---------------------------------------------------------------------------
# API: Backend campaigns
# ---------------------------------------------------------------------------

@app.route("/api/campaigns")
def api_campaigns():
    return jsonify(state["backend_campaigns"])


@app.route("/api/campaigns/<int:company_id>")
def api_campaigns_for_company(company_id):
    result = [
        c for c in state["backend_campaigns"]
        if c["company_id"] == company_id
    ]
    return jsonify(result)

# ---------------------------------------------------------------------------
# API: Emails (inbox)
# ---------------------------------------------------------------------------

@app.route("/api/emails")
def api_emails():
    return jsonify(state["emails"])


@app.route("/api/emails/<int:email_id>")
def api_email_detail(email_id):
    for e in state["emails"]:
        if e["email_id"] == email_id:
            return jsonify(e)
    abort(404)

# ---------------------------------------------------------------------------
# API: Agent Run (SSE streaming narration)
# ---------------------------------------------------------------------------

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

# ---------------------------------------------------------------------------
# API: Approve / Reject interventions
# ---------------------------------------------------------------------------

@app.route("/api/interventions/<int:intervention_id>/approve", methods=["POST"])
def api_approve(intervention_id):
    """Approve a pending intervention."""
    iv = next(
        (i for i in state["interventions"]
         if i["intervention_id"] == intervention_id),
        None,
    )
    if not iv:
        abort(404)
    if iv["status"] != "pending":
        return jsonify({"error": "Not in pending status"}), 400

    iv["status"] = "approved"
    iv["approved_at"] = "2026-02-10"

    # Enable associated campaigns
    for campaign in state["backend_campaigns"]:
        if campaign.get("intervention_id") == intervention_id:
            campaign["status"] = "enabled"

    # Log approval to CRM
    activities.append({
        "activity_id": max(a["activity_id"] for a in activities) + 1,
        "company_id": iv["company_id"],
        "activity_date": "2026-02-10",
        "type": "Agent Intervention",
        "note": f"CSM approved in-app messaging intervention for {iv['company_name']}.",
    })

    return jsonify({"status": "approved", "intervention": iv})


@app.route("/api/interventions/<int:intervention_id>/reject", methods=["POST"])
def api_reject(intervention_id):
    """Reject a pending intervention."""
    iv = next(
        (i for i in state["interventions"]
         if i["intervention_id"] == intervention_id),
        None,
    )
    if not iv:
        abort(404)
    if iv["status"] != "pending":
        return jsonify({"error": "Not in pending status"}), 400

    iv["status"] = "rejected"

    # Remove associated campaigns
    state["backend_campaigns"] = [
        c for c in state["backend_campaigns"]
        if c.get("intervention_id") != intervention_id
    ]

    # Log rejection to CRM
    activities.append({
        "activity_id": max(a["activity_id"] for a in activities) + 1,
        "company_id": iv["company_id"],
        "activity_date": "2026-02-10",
        "type": "Agent Intervention",
        "note": f"CSM rejected in-app messaging intervention for {iv['company_name']}.",
    })

    return jsonify({"status": "rejected", "intervention": iv})

# ---------------------------------------------------------------------------
# API: Reset Demo
# ---------------------------------------------------------------------------

@app.route("/api/reset", methods=["POST"])
def api_reset():
    """Reset all state back to the starting condition."""
    state["agent_has_run"] = False
    state["interventions"] = []
    state["backend_campaigns"] = []
    state["emails"] = []

    # Restore activities to original set (remove agent-added ones)
    activities.clear()
    activities.extend(original_activities)

    return jsonify({"status": "reset"})

# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    debug = os.environ.get("DEBUG", "true").lower() == "true"
    print(f"Starting Cymbal Meet Demo on port {port}")
    print(f"  Companies loaded: {len(companies)}")
    print(f"  Contacts loaded: {len(contacts)}")
    print(f"  Activities loaded: {len(activities)}")
    print(f"  Engagement data generated for {len(engagement)} companies")
    app.run(host="0.0.0.0", port=port, debug=debug)
