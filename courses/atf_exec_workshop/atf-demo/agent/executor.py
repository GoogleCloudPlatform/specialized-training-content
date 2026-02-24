"""
Execute the agent workflow and yield narration lines.

This is the heart of the demo. When the instructor clicks
"Run Like It's Monday", this module:
  1. Analyzes all companies
  2. Selects interventions for problem companies
  3. Yields narration text line-by-line (for SSE streaming)
  4. Returns the full list of interventions + activities + emails
"""

import time
from datetime import date

from agent.analyzer import find_all_issues
from agent.decision_engine import select_interventions

# The demo date (matches the PRD)
DEMO_DATE = "2026-02-10"

# Metric display names for narration
METRIC_LABELS = {
    "7da_users": "7DA Users",
    "call_volume": "7D Call Volume",
    "device_utilization": "Device Call Sessions",
    "dialin_sessions": "7D Dial-in Sessions",
    "calendar_meetings": "Calendared Meetings",
    "feedback_sentiment": "Feedback Sentiment",
}


def run_agent(companies, contacts, engagement, activities=None, delay=0.3):
    """
    Generator that yields (narration_line, is_final) tuples.

    After the generator is exhausted, call get_results() to get
    the interventions, activities, emails, and campaigns produced.

    delay: seconds between narration lines (for realistic pacing)
    """
    crm_activities = activities or []
    # We'll collect results as we go
    all_interventions = []
    new_activities = []
    new_emails = []
    new_campaigns = []
    intervention_id = 1
    email_id = 1
    activity_id_start = 1000  # offset to avoid colliding with CSV data

    # --- Header ---
    yield "Cymbal Meet Agent — Weekly Run"
    yield "---"
    yield ""
    time.sleep(delay)

    # --- Phase 1: Data Collection ---
    yield f"Collecting engagement data for {len(companies)} customers..."
    time.sleep(delay * 2)
    yield "✓ Engagement data collected"
    yield ""
    time.sleep(delay)

    # --- Phase 2: Issue Analysis ---
    yield "Analyzing metrics against targets..."
    time.sleep(delay * 2)

    issues_by_company = find_all_issues(companies, engagement)
    num_issues = len(issues_by_company)
    yield f"✓ Found {num_issues} customers with engagement issues"
    yield ""
    time.sleep(delay)

    # Build lookup for companies and contacts
    companies_by_id = {c["company_id"]: c for c in companies}

    # Pick up to 3 companies to narrate in detail
    detailed_ids = list(issues_by_company.keys())[:3]
    remaining_ids = list(issues_by_company.keys())[3:]

    # --- Phase 3 & 4: Process each company ---
    for cid in detailed_ids:
        company = companies_by_id[cid]
        issues = issues_by_company[cid]
        eng = engagement[cid]
        company_contacts = [
            c for c in contacts if c["company_id"] == cid
        ]

        yield "---"
        yield f"Processing: {company['name']}"
        yield "---"
        yield ""
        time.sleep(delay)

        # Show issues
        for issue in issues:
            label = METRIC_LABELS.get(issue["metric"], issue["metric"])
            yield (
                f"Issue identified: {label} "
                f"{issue['gap_pct']}% below target "
                f"({issue['actual']:,} actual vs "
                f"{issue['target']:,} target)"
            )
            time.sleep(delay)

        yield ""
        yield "Scanning internal documentation..."
        time.sleep(delay * 2)
        yield "✓ Found relevant articles on engagement and adoption"
        yield ""
        time.sleep(delay)

        # Select interventions
        ivs = select_interventions(
            company, issues, eng, company_contacts, crm_activities
        )

        for iv in ivs:
            iv["intervention_id"] = intervention_id
            iv["company_id"] = cid
            iv["company_name"] = company["name"]
            iv["created_at"] = DEMO_DATE

            if iv["type"] == "admin_email":
                iv["status"] = "auto_executed"
                yield f"Selecting intervention: Admin Weekly Email"
                yield "Generating personalized content..."
                time.sleep(delay)

                # Narrate highlights
                for h in iv.get("highlights", [])[:2]:
                    label = METRIC_LABELS.get(h["metric"], h["metric"])
                    pct = round(h["ratio"] * 100)
                    yield f"  ├─ Highlighting: {label} at {pct}% of target"

                for imp in iv.get("improvements", [])[:2]:
                    label = METRIC_LABELS.get(
                        imp["metric"], imp["metric"]
                    )
                    yield f"  ├─ Addressing: {label} below target"

                rec = iv.get("feature_rec", {})
                yield f"  ├─ Recommending: {rec.get('name', 'N/A')}"

                # Narrate remediations
                for rem in iv.get("remediations", []):
                    label = METRIC_LABELS.get(rem["metric"], rem["metric"])
                    yield f"  ├─ Remediation for {label}: {rem['name']}"
                time.sleep(delay)
                yield f"✓ Email generated and queued for delivery"
                yield ""

                # Create an email record
                new_emails.append({
                    "email_id": email_id,
                    "company_id": cid,
                    "company_name": company["name"],
                    "type": "admin_weekly",
                    "recipient": iv["recipient"],
                    "recipient_role": iv["recipient_role"],
                    "subject": "Your Weekly Cymbal Meet Performance Report",
                    "date": DEMO_DATE,
                    "intervention": iv,
                })
                email_id += 1

                # CRM activity
                new_activities.append({
                    "activity_id": activity_id_start,
                    "company_id": cid,
                    "activity_date": DEMO_DATE,
                    "type": "Agent Intervention",
                    "note": (
                        f"Weekly admin email sent to "
                        f"{iv['recipient']} ({iv['recipient_role']}). "
                        f"Re: Engagement performance and recommendations."
                    ),
                })
                activity_id_start += 1

            elif iv["type"] == "inapp_calendar":
                iv["status"] = "pending"
                yield "Selecting intervention: Calendar Extension In-App Messaging"
                yield "Root cause analysis:"
                yield (
                    f"  ├─ Extension installed: "
                    f"{round(iv['install_rate'] * 100)}% of users"
                )
                yield (
                    f"  ├─ Extension active usage: "
                    f"{round(iv['usage_rate'] * 100)}% of installed users"
                )
                yield "Creating two-part messaging campaign..."
                time.sleep(delay)
                yield (
                    f"  ├─ Message A: Installation prompt "
                    f"({iv['message_a']['user_count']:,} users)"
                )
                yield (
                    f"  ├─ Message B: Usage encouragement "
                    f"({iv['message_b']['user_count']:,} users)"
                )
                yield "⚠ Intervention requires CSM approval - surfacing in dashboard"
                yield ""
                time.sleep(delay)

                # CRM activity
                new_activities.append({
                    "activity_id": activity_id_start,
                    "company_id": cid,
                    "activity_date": DEMO_DATE,
                    "type": "Agent Intervention",
                    "note": (
                        f"In-app messaging campaign proposed for CSM "
                        f"approval. Re: Calendar extension adoption."
                    ),
                })
                activity_id_start += 1

                # Pending campaign records
                new_campaigns.append({
                    "campaign_id": len(new_campaigns) + 1,
                    "company_id": cid,
                    "company_name": company["name"],
                    "type": "Slideout",
                    "name": "Calendar Ext Install (No Extension)",
                    "status": "pending",
                    "created_by": "Cymbal Agent",
                    "intervention_id": intervention_id,
                })
                new_campaigns.append({
                    "campaign_id": len(new_campaigns) + 1,
                    "company_id": cid,
                    "company_name": company["name"],
                    "type": "Slideout",
                    "name": "Calendar Ext Usage (Installed Users)",
                    "status": "pending",
                    "created_by": "Cymbal Agent",
                    "intervention_id": intervention_id,
                })

            elif iv["type"] == "device_email":
                iv["status"] = "auto_executed"
                num_devices = len(iv["devices"])
                yield "Selecting intervention: Device Performance Remediation Email"
                yield "Analyzing device metrics..."
                yield f"  ├─ Found {num_devices} devices with performance issues"
                for dev in iv["devices"]:
                    issues_str = ", ".join(dev["issues"])
                    yield (
                        f"  ├─ {dev['name']}: "
                        f"{dev['avg_fps']}fps avg, "
                        f"{dev['avg_resolution']} "
                        f"({issues_str})"
                    )
                time.sleep(delay)
                yield "Generating remediation instructions..."
                yield "✓ Email generated and queued for delivery"
                yield ""

                new_emails.append({
                    "email_id": email_id,
                    "company_id": cid,
                    "company_name": company["name"],
                    "type": "device_performance",
                    "recipient": iv["recipient"],
                    "recipient_role": iv["recipient_role"],
                    "subject": "Device Performance Alert - Action Required",
                    "date": DEMO_DATE,
                    "intervention": iv,
                })
                email_id += 1

                new_activities.append({
                    "activity_id": activity_id_start,
                    "company_id": cid,
                    "activity_date": DEMO_DATE,
                    "type": "Agent Intervention",
                    "note": (
                        f"Device performance remediation email sent to "
                        f"{iv['recipient']}. "
                        f"{num_devices} devices flagged."
                    ),
                })
                activity_id_start += 1

            intervention_id += 1
            all_interventions.append(iv)

        # System updates narration
        yield "Updating external systems..."
        num_acts = sum(
            1 for a in new_activities if a["company_id"] == cid
        )
        yield f"  ✓ CRM activity logged ({num_acts} entries)"
        yield "  ✓ CSM dashboard updated"
        if any(iv["type"] == "inapp_calendar" for iv in ivs):
            yield "  ✓ Backend admin panel configured"
        yield ""
        time.sleep(delay)

    # --- Process remaining companies (brief) ---
    for cid in remaining_ids:
        company = companies_by_id[cid]
        issues = issues_by_company[cid]
        eng = engagement[cid]
        company_contacts = [
            c for c in contacts if c["company_id"] == cid
        ]
        ivs = select_interventions(
            company, issues, eng, company_contacts, crm_activities
        )
        for iv in ivs:
            iv["intervention_id"] = intervention_id
            iv["company_id"] = cid
            iv["company_name"] = company["name"]
            iv["created_at"] = DEMO_DATE

            if iv["type"] == "admin_email":
                iv["status"] = "auto_executed"
                new_emails.append({
                    "email_id": email_id,
                    "company_id": cid,
                    "company_name": company["name"],
                    "type": "admin_weekly",
                    "recipient": iv["recipient"],
                    "recipient_role": iv["recipient_role"],
                    "subject": "Your Weekly Cymbal Meet Performance Report",
                    "date": DEMO_DATE,
                    "intervention": iv,
                })
                email_id += 1
            elif iv["type"] == "inapp_calendar":
                iv["status"] = "pending"
                new_campaigns.append({
                    "campaign_id": len(new_campaigns) + 1,
                    "company_id": cid,
                    "company_name": company["name"],
                    "type": "Slideout",
                    "name": "Calendar Ext Install (No Extension)",
                    "status": "pending",
                    "created_by": "Cymbal Agent",
                    "intervention_id": intervention_id,
                })
                new_campaigns.append({
                    "campaign_id": len(new_campaigns) + 1,
                    "company_id": cid,
                    "company_name": company["name"],
                    "type": "Slideout",
                    "name": "Calendar Ext Usage (Installed Users)",
                    "status": "pending",
                    "created_by": "Cymbal Agent",
                    "intervention_id": intervention_id,
                })
            elif iv["type"] == "device_email":
                iv["status"] = "auto_executed"
                new_emails.append({
                    "email_id": email_id,
                    "company_id": cid,
                    "company_name": company["name"],
                    "type": "device_performance",
                    "recipient": iv["recipient"],
                    "recipient_role": iv["recipient_role"],
                    "subject": "Device Performance Alert - Action Required",
                    "date": DEMO_DATE,
                    "intervention": iv,
                })
                email_id += 1

            new_activities.append({
                "activity_id": activity_id_start,
                "company_id": cid,
                "activity_date": DEMO_DATE,
                "type": "Agent Intervention",
                "note": f"Agent intervention: {iv['type']} for {company['name']}",
            })
            activity_id_start += 1
            intervention_id += 1
            all_interventions.append(iv)

    if remaining_ids:
        yield "---"
        yield ""
        yield (
            f"Processing remaining {len(remaining_ids)} customers "
            f"with similar workflows..."
        )
        time.sleep(delay)
        yield ""

    # --- Summary ---
    num_emails = sum(
        1 for e in new_emails if e["type"] == "admin_weekly"
    )
    num_device_emails = sum(
        1 for e in new_emails if e["type"] == "device_performance"
    )
    num_pending = sum(
        1 for iv in all_interventions if iv["status"] == "pending"
    )

    yield "Done — Agent run complete"
    yield ""
    yield "Summary:"
    yield f"  • {num_issues} customers processed with interventions"
    yield f"  • {num_emails} admin emails queued for delivery"
    yield f"  • {num_pending} in-app messaging campaigns pending CSM approval"
    yield f"  • {num_device_emails} device remediation emails queued"
    yield f"  • {len(new_activities)} CRM activity records created"
    yield f"  • {num_issues} CSM dashboard updates applied"

    # Stash results so the caller can grab them
    yield {"__results__": {
        "interventions": all_interventions,
        "activities": new_activities,
        "emails": new_emails,
        "campaigns": new_campaigns,
    }}
