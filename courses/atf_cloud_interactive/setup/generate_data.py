#!/usr/bin/env python3
"""Generates synthetic Cymbal Meet data and loads it into BigQuery.

Deterministic output via seeded numpy RNG. See PRD section 3.4 for full spec.

Usage:
    python generate_data.py              # generate + load into BigQuery
    python generate_data.py --dry-run    # generate + print row counts only

Requires $PROJECT_ID env var or active gcloud config.
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import date, datetime, timedelta
from io import BytesIO

import numpy as np
from google.cloud import bigquery

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DATASET_ID = "cymbal_meet"

# Per-table seeds (PRD 3.4 — Reproducibility)
SEED_CUSTOMERS = 1000
SEED_LOGINS = 2000
SEED_CALENDAR = 3000
SEED_TELEMETRY = 4000
SEED_CALLS = 5000

# Segment baselines — healthy per-user monthly metrics (PRD 3.4)
SEGMENT_BASELINES = {
    "Enterprise": {
        "logins_per_user_month": 18,
        "events_per_user_month": 14,
        "calls_per_user_month": 12,
        "adhoc_ratio": 0.35,
        "avg_participants": 4,
    },
    "Mid-Market": {
        "logins_per_user_month": 15,
        "events_per_user_month": 10,
        "calls_per_user_month": 9,
        "adhoc_ratio": 0.30,
        "avg_participants": 3.5,
    },
    "SMB": {
        "logins_per_user_month": 12,
        "events_per_user_month": 7,
        "calls_per_user_month": 6,
        "adhoc_ratio": 0.25,
        "avg_participants": 3,
    },
}

# Platform distributions (PRD 3.4)
LOGIN_PLATFORMS = {
    "Enterprise": {"desktop": 0.60, "web": 0.25, "mobile": 0.15},
    "Mid-Market": {"desktop": 0.55, "web": 0.30, "mobile": 0.15},
    "SMB": {"desktop": 0.45, "web": 0.40, "mobile": 0.15},
}

CAL_PLATFORMS = {
    "Enterprise": {"google_calendar": 0.30, "outlook": 0.65, "other": 0.05},
    "Mid-Market": {"google_calendar": 0.50, "outlook": 0.45, "other": 0.05},
    "SMB": {"google_calendar": 0.70, "outlook": 0.25, "other": 0.05},
}

# Call duration by segment (PRD 3.4)
CALL_DURATION = {
    "Enterprise": {"mean": 38, "std": 15, "min": 5, "max": 90},
    "Mid-Market": {"mean": 30, "std": 12, "min": 5, "max": 75},
    "SMB": {"mean": 25, "std": 10, "min": 5, "max": 60},
}

# Day-of-week weights within weekdays (PRD 3.4)
WEEKDAY_WEIGHTS = [0.21, 0.22, 0.21, 0.20, 0.16]  # Mon-Fri

# Time-of-day cumulative blocks for random timestamp generation
# Each tuple: (hour_start, hour_end, weight)
TIME_BLOCKS = [
    (8, 9, 0.08),
    (9, 10, 0.15),
    (10, 12, 0.25),
    (12, 13, 0.07),
    (13, 15, 0.22),
    (15, 17, 0.15),
    (17, 19, 0.06),
    (19, 8, 0.02),  # overnight (wraps; we map to 19-24 + 0-8)
]

# Weekday vs weekend split (PRD 3.4)
WEEKDAY_SHARE = {"logins": 0.92, "calendar_events": 0.95, "calls": 0.93}

# Telemetry baselines (PRD 3.4)
TELEMETRY_HEALTHY = {
    "cpu_usage_pct": (35.0, 8.0),
    "memory_usage_pct": (45.0, 10.0),
    "network_latency_ms": (25.0, 8.0),
    "packet_loss_pct": (0.3, 0.2),
    "video_quality_score": (4.2, 0.3),
}

# Call quality baselines (PRD 3.4)
CALL_QUALITY_HEALTHY = {"avg_quality_score": (4.1, 0.4), "drop_count": (0.2, 0.4)}

# CRM interaction config (PRD 3.4)
INTERACTION_CONFIG = {
    "Enterprise": {
        "count": (6, 8),
        "types": ["Health Check", "Executive Review", "Support", "Maintenance", "CSM", "Renewal Discussion"],
        "weights": [0.30, 0.20, 0.20, 0.15, 0.10, 0.05],
    },
    "Mid-Market": {
        "count": (4, 6),
        "types": ["CSM", "Support", "Health Check", "Maintenance", "Renewal Discussion"],
        "weights": [0.30, 0.25, 0.20, 0.15, 0.10],
    },
    "SMB": {
        "count": (3, 5),
        "types": ["CSM", "Support", "Health Check", "Maintenance", "Renewal Discussion"],
        "weights": [0.35, 0.30, 0.20, 0.10, 0.05],
    },
}

# Healthy interaction notes — generic positive/neutral
HEALTHY_NOTES = {
    "Health Check": [
        "Quarterly health check — all metrics within normal range",
        "Usage trending positively across departments",
        "Strong adoption in engineering and sales teams",
        "Platform health good; no open support issues",
        "Reviewed usage dashboard — steady growth in meeting volume",
    ],
    "Executive Review": [
        "QBR with CIO — satisfaction high, considering seat expansion",
        "Executive sponsor engaged and supportive of broader rollout",
        "Leadership team pleased with video quality improvements",
        "Discussed roadmap features; customer excited about upcoming releases",
    ],
    "Support": [
        "Minor UI question resolved — user found answer in help docs",
        "Password reset request handled",
        "Assisted with SSO configuration — completed successfully",
        "Helped configure room display settings",
        "Resolved calendar sync delay — cleared cache",
    ],
    "Maintenance": [
        "Firmware update completed on conference room devices",
        "Scheduled maintenance window — no user impact",
        "Updated client software to latest version across organization",
        "Device health check — all units operating normally",
    ],
    "CSM": [
        "Monthly check-in — customer satisfied with service",
        "Discussed upcoming training session for new hires",
        "Shared best practices guide for meeting room setup",
        "Reviewed adoption metrics — all above segment benchmarks",
        "Customer interested in advanced analytics features",
    ],
    "Renewal Discussion": [
        "Early renewal discussion — customer likely to renew at current terms",
        "Discussed potential seat expansion for next contract period",
        "Renewal sentiment positive; no concerns raised",
    ],
}

# Problem-specific interaction notes (PRD 3.4)
PROBLEM_NOTES = {
    "pinnacle": [
        ("Support", "Acquired workforce onboarding stalled — former Apex employees not migrated"),
        ("Health Check", "Only 25% of licensed users actively logging in; legacy tool still in use in former Apex offices"),
        ("CSM", "Discussed migration plan for acquired workforce — 1,200 users still on legacy platform"),
        ("Executive Review", "CIO concerned about low adoption in acquired business unit; requested accelerated migration plan"),
        ("Support", "Multiple tickets from former Apex users unable to access Cymbal Meet — SSO not configured for acquired domain"),
        ("Health Check", "Adoption gap widening — acquired users defaulting to legacy tool for daily standups"),
    ],
    "quantum": [
        ("Support", "IT security team requires all video traffic through corporate proxy — investigating quality impact"),
        ("Support", "Users report inability to initiate quick calls — ad-hoc calling appears disabled by policy"),
        ("Health Check", "Call quality scores significantly below baseline — average 2.8 vs expected 4.1"),
        ("Maintenance", "Investigated proxy routing configuration — video packets being re-encrypted causing latency"),
        ("Executive Review", "CISO insists on proxy routing for compliance; engineering exploring QoS exceptions for video traffic"),
        ("CSM", "Multiple departments reporting frozen video and audio drops during large meetings"),
    ],
    "verdant": [
        ("Support", "Calendar integration support ticket open since November — Outlook connector failing"),
        ("Support", "Users report difficulty connecting Outlook calendars — sync errors persist"),
        ("Health Check", "Login rates normal but calendar events severely underutilized — users scheduling meetings outside Cymbal Meet"),
        ("CSM", "Recommended calendar integration troubleshooting session — customer agreed to schedule"),
        ("Maintenance", "Attempted Outlook calendar connector repair — requires admin consent refresh"),
    ],
    "coastal": [
        ("Support", "Multiple complaints about video freezing since January office relocation"),
        ("Support", "Network team says bandwidth is sufficient but QoS not configured for video traffic"),
        ("Health Check", "Device telemetry showing packet loss 4% and latency 95ms across ALL conference rooms"),
        ("Maintenance", "Inspected devices post-relocation — hardware functioning normally; issue is network-side"),
        ("CSM", "Escalated network QoS issue to customer IT leadership — awaiting infrastructure changes"),
    ],
    "brightpath": [
        ("CSM", "VP of Operations Sarah Kim has departed — she was the primary Cymbal Meet champion"),
        ("CSM", "Difficulty reaching new point of contact — usage declining without executive sponsorship"),
        ("Health Check", "Login and call volume dropping week over week — down 40% from initial levels"),
        ("Renewal Discussion", "Renewal at risk — usage erosion continuing; need to identify new internal champion"),
        ("Support", "Fewer support tickets being filed — may indicate disengagement rather than satisfaction"),
    ],
}

# Contact names for CRM interactions
CSM_CONTACTS = {
    "Sarah Chen": "Sarah Chen",
    "Michael Torres": "Michael Torres",
    "James Rodriguez": "James Rodriguez",
    "Maria Santos": "Maria Santos",
    "David Park": "David Park",
    "Lisa Wang": "Lisa Wang",
}


# ---------------------------------------------------------------------------
# Customer roster (PRD 3.4)
# ---------------------------------------------------------------------------

def _domain(name: str) -> str:
    """Convert company name to email domain."""
    return name.lower().replace(" ", "").replace(".", "").replace(",", "") + ".com"


CUSTOMERS = [
    # Enterprise
    {"customer_id": "CUST-E001", "company_name": "Pinnacle Financial Group", "segment": "Enterprise",
     "licensed_users": 1800, "conference_rooms": 120, "annual_contract_value": 540000.0, "csm_name": "Sarah Chen",
     "problem": "pinnacle"},
    {"customer_id": "CUST-E002", "company_name": "Quantum Dynamics Corp", "segment": "Enterprise",
     "licensed_users": 2200, "conference_rooms": 140, "annual_contract_value": 660000.0, "csm_name": "Sarah Chen",
     "problem": "quantum"},
    {"customer_id": "CUST-E003", "company_name": "Atlas Manufacturing", "segment": "Enterprise",
     "licensed_users": 800, "conference_rooms": 65, "annual_contract_value": 240000.0, "csm_name": "Michael Torres",
     "problem": None},
    {"customer_id": "CUST-E004", "company_name": "Meridian Partners", "segment": "Enterprise",
     "licensed_users": 1500, "conference_rooms": 95, "annual_contract_value": 450000.0, "csm_name": "Michael Torres",
     "problem": None},
    {"customer_id": "CUST-E005", "company_name": "Crestview Holdings", "segment": "Enterprise",
     "licensed_users": 2500, "conference_rooms": 150, "annual_contract_value": 750000.0, "csm_name": "Sarah Chen",
     "problem": None},
    # Mid-Market
    {"customer_id": "CUST-M001", "company_name": "Verdant Health Systems", "segment": "Mid-Market",
     "licensed_users": 320, "conference_rooms": 28, "annual_contract_value": 64000.0, "csm_name": "James Rodriguez",
     "problem": "verdant"},
    {"customer_id": "CUST-M002", "company_name": "Coastal Logistics Inc.", "segment": "Mid-Market",
     "licensed_users": 250, "conference_rooms": 35, "annual_contract_value": 50000.0, "csm_name": "Maria Santos",
     "problem": "coastal"},
    {"customer_id": "CUST-M003", "company_name": "Northstar Analytics", "segment": "Mid-Market",
     "licensed_users": 180, "conference_rooms": 15, "annual_contract_value": 36000.0, "csm_name": "James Rodriguez",
     "problem": None},
    {"customer_id": "CUST-M004", "company_name": "BlueSky Innovations", "segment": "Mid-Market",
     "licensed_users": 400, "conference_rooms": 40, "annual_contract_value": 80000.0, "csm_name": "Maria Santos",
     "problem": None},
    {"customer_id": "CUST-M005", "company_name": "Redwood Consulting", "segment": "Mid-Market",
     "licensed_users": 150, "conference_rooms": 12, "annual_contract_value": 30000.0, "csm_name": "James Rodriguez",
     "problem": None},
    {"customer_id": "CUST-M006", "company_name": "Summit Financial", "segment": "Mid-Market",
     "licensed_users": 280, "conference_rooms": 22, "annual_contract_value": 56000.0, "csm_name": "Maria Santos",
     "problem": None},
    {"customer_id": "CUST-M007", "company_name": "Ironbridge Solutions", "segment": "Mid-Market",
     "licensed_users": 200, "conference_rooms": 18, "annual_contract_value": 40000.0, "csm_name": "James Rodriguez",
     "problem": None},
    {"customer_id": "CUST-M008", "company_name": "Clearwater Tech", "segment": "Mid-Market",
     "licensed_users": 350, "conference_rooms": 30, "annual_contract_value": 70000.0, "csm_name": "Maria Santos",
     "problem": None},
    {"customer_id": "CUST-M009", "company_name": "Hawthorne Media", "segment": "Mid-Market",
     "licensed_users": 120, "conference_rooms": 10, "annual_contract_value": 24000.0, "csm_name": "James Rodriguez",
     "problem": None},
    {"customer_id": "CUST-M010", "company_name": "Pacific Ridge Partners", "segment": "Mid-Market",
     "licensed_users": 300, "conference_rooms": 25, "annual_contract_value": 60000.0, "csm_name": "Maria Santos",
     "problem": None},
    # SMB
    {"customer_id": "CUST-S001", "company_name": "BrightPath Education", "segment": "SMB",
     "licensed_users": 55, "conference_rooms": 5, "annual_contract_value": 8250.0, "csm_name": "David Park",
     "problem": "brightpath"},
    {"customer_id": "CUST-S002", "company_name": "Ember Creative", "segment": "SMB",
     "licensed_users": 30, "conference_rooms": 3, "annual_contract_value": 4500.0, "csm_name": "David Park",
     "problem": None},
    {"customer_id": "CUST-S003", "company_name": "Foxglove Design", "segment": "SMB",
     "licensed_users": 45, "conference_rooms": 4, "annual_contract_value": 6750.0, "csm_name": "Lisa Wang",
     "problem": None},
    {"customer_id": "CUST-S004", "company_name": "Garnet Legal", "segment": "SMB",
     "licensed_users": 25, "conference_rooms": 2, "annual_contract_value": 3750.0, "csm_name": "David Park",
     "problem": None},
    {"customer_id": "CUST-S005", "company_name": "Horizon Wellness", "segment": "SMB",
     "licensed_users": 70, "conference_rooms": 7, "annual_contract_value": 10500.0, "csm_name": "Lisa Wang",
     "problem": None},
    {"customer_id": "CUST-S006", "company_name": "Jade Architects", "segment": "SMB",
     "licensed_users": 20, "conference_rooms": 2, "annual_contract_value": 3000.0, "csm_name": "David Park",
     "problem": None},
    {"customer_id": "CUST-S007", "company_name": "Keystone Plumbing", "segment": "SMB",
     "licensed_users": 15, "conference_rooms": 2, "annual_contract_value": 2250.0, "csm_name": "Lisa Wang",
     "problem": None},
    {"customer_id": "CUST-S008", "company_name": "Lumen Analytics", "segment": "SMB",
     "licensed_users": 60, "conference_rooms": 5, "annual_contract_value": 9000.0, "csm_name": "David Park",
     "problem": None},
    {"customer_id": "CUST-S009", "company_name": "Mosaic Interiors", "segment": "SMB",
     "licensed_users": 35, "conference_rooms": 3, "annual_contract_value": 5250.0, "csm_name": "Lisa Wang",
     "problem": None},
    {"customer_id": "CUST-S010", "company_name": "Nimbus Software", "segment": "SMB",
     "licensed_users": 80, "conference_rooms": 8, "annual_contract_value": 12000.0, "csm_name": "Lisa Wang",
     "problem": None},
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_project_id() -> str:
    project = os.environ.get("PROJECT_ID")
    if project:
        return project
    result = subprocess.run(
        ["gcloud", "config", "get-value", "project"],
        capture_output=True, text=True, check=True,
    )
    project = result.stdout.strip()
    if not project:
        raise RuntimeError("No PROJECT_ID env var and no gcloud project configured")
    return project


def compute_date_range() -> tuple[date, date]:
    """Return (start_monday, end_sunday) for a 7-week window ending on the
    most recent Sunday at or before today."""
    today = date.today()
    # Sunday = 6 in weekday() (Monday=0)
    days_since_sunday = (today.weekday() + 1) % 7
    end_date = today - timedelta(days=days_since_sunday)
    start_date = end_date - timedelta(days=48)  # 49 days total (0-indexed)
    return start_date, end_date


def get_weekdays(start: date, end: date) -> list[date]:
    """Return all weekday dates in [start, end] inclusive."""
    days = []
    d = start
    while d <= end:
        if d.weekday() < 5:
            days.append(d)
        d += timedelta(days=1)
    return days


def get_weekends(start: date, end: date) -> list[date]:
    """Return all weekend dates in [start, end] inclusive."""
    days = []
    d = start
    while d <= end:
        if d.weekday() >= 5:
            days.append(d)
        d += timedelta(days=1)
    return days


def pick_time_of_day(rng: np.random.Generator) -> tuple[int, int, int]:
    """Pick a random (hour, minute, second) using the PRD time-of-day weights."""
    block_weights = [b[2] for b in TIME_BLOCKS]
    block_weights = np.array(block_weights) / sum(block_weights)
    idx = rng.choice(len(TIME_BLOCKS), p=block_weights)
    start_h, end_h, _ = TIME_BLOCKS[idx]
    if start_h > end_h:  # overnight block (19-8)
        # map to 19-24
        hour = rng.integers(19, 24)
    else:
        hour = rng.integers(start_h, end_h)
    minute = int(rng.integers(0, 60))
    second = int(rng.integers(0, 60))
    return int(hour), minute, second


def pick_weekday(rng: np.random.Generator, weekdays: list[date]) -> date:
    """Pick a weekday date using the day-of-week weights."""
    # Group weekdays by day-of-week, then pick
    weights = np.array(WEEKDAY_WEIGHTS)
    weights = weights / weights.sum()
    dow = rng.choice(5, p=weights)  # 0=Mon, 4=Fri
    candidates = [d for d in weekdays if d.weekday() == dow]
    if not candidates:
        return rng.choice(weekdays)
    return candidates[int(rng.integers(0, len(candidates)))]


def make_timestamp(d: date, h: int, m: int, s: int) -> str:
    """Format as ISO timestamp string for BigQuery."""
    return datetime(d.year, d.month, d.day, h, m, s).isoformat()


def week_number(d: date, start: date) -> int:
    """Return 0-indexed week number within the date range."""
    return (d - start).days // 7


# ---------------------------------------------------------------------------
# Data generators
# ---------------------------------------------------------------------------

def generate_customers(rng: np.random.Generator, start: date, end: date) -> list[dict]:
    """Generate customer rows with CRM interactions."""
    weekdays = get_weekdays(start, end)
    rows = []
    for cust in CUSTOMERS:
        # Contract start: 6-24 months before the data window start
        months_back = int(rng.integers(6, 25))
        csd = start - timedelta(days=months_back * 30)

        # Generate interactions
        seg = cust["segment"]
        cfg = INTERACTION_CONFIG[seg]
        n_interactions = int(rng.integers(cfg["count"][0], cfg["count"][1] + 1))
        interactions = []

        problem = cust["problem"]
        if problem and problem in PROBLEM_NOTES:
            # Use problem-specific notes first, then fill with healthy notes
            problem_notes = list(PROBLEM_NOTES[problem])
            rng.shuffle(problem_notes)
            used_problem = problem_notes[:min(n_interactions, len(problem_notes))]
            remaining = n_interactions - len(used_problem)

            for itype, note in used_problem:
                idate = weekdays[int(rng.integers(0, len(weekdays)))]
                interactions.append({
                    "interaction_date": idate.isoformat(),
                    "type": itype,
                    "contact_name": cust["csm_name"],
                    "note": note,
                })

            # Fill remaining with healthy notes
            for _ in range(remaining):
                type_weights = np.array(cfg["weights"])
                type_weights = type_weights / type_weights.sum()
                itype = rng.choice(cfg["types"], p=type_weights)
                notes = HEALTHY_NOTES.get(itype, ["Routine check-in — no issues"])
                note = notes[int(rng.integers(0, len(notes)))]
                idate = weekdays[int(rng.integers(0, len(weekdays)))]
                interactions.append({
                    "interaction_date": idate.isoformat(),
                    "type": itype,
                    "contact_name": cust["csm_name"],
                    "note": note,
                })
        else:
            # All healthy notes
            for _ in range(n_interactions):
                type_weights = np.array(cfg["weights"])
                type_weights = type_weights / type_weights.sum()
                itype = rng.choice(cfg["types"], p=type_weights)
                notes = HEALTHY_NOTES.get(itype, ["Routine check-in — no issues"])
                note = notes[int(rng.integers(0, len(notes)))]
                idate = weekdays[int(rng.integers(0, len(weekdays)))]
                interactions.append({
                    "interaction_date": idate.isoformat(),
                    "type": itype,
                    "contact_name": cust["csm_name"],
                    "note": note,
                })

        # Sort interactions by date
        interactions.sort(key=lambda x: x["interaction_date"])

        rows.append({
            "customer_id": cust["customer_id"],
            "company_name": cust["company_name"],
            "segment": cust["segment"],
            "licensed_users": cust["licensed_users"],
            "conference_rooms": cust["conference_rooms"],
            "annual_contract_value": cust["annual_contract_value"],
            "contract_start_date": csd.isoformat(),
            "csm_name": cust["csm_name"],
            "interactions": interactions,
        })

    return rows


def generate_logins(rng: np.random.Generator, start: date, end: date) -> list[dict]:
    """Generate login rows for all customers."""
    weekdays = get_weekdays(start, end)
    weekends = get_weekends(start, end)
    total_days = (end - start).days + 1
    months = total_days / 30.0

    rows = []
    counter = 0

    for cust in CUSTOMERS:
        seg = cust["segment"]
        baselines = SEGMENT_BASELINES[seg]
        n_users = cust["licensed_users"]
        problem = cust["problem"]

        # Per-customer rate variation: +/- 15% for healthy
        rate_factor = 1.0 + rng.uniform(-0.15, 0.15)

        # Effective login rate per user per month
        base_rate = baselines["logins_per_user_month"] * rate_factor

        # Problem adjustments
        if problem == "pinnacle":
            # Only ~25% of users log in; rate per active user is ~5/month
            active_users = int(n_users * 0.25)
            logins_per_active = 5.0 * rate_factor
            total_logins = int(active_users * logins_per_active * months)
        elif problem == "brightpath":
            # Healthy first 3 weeks, then declining. We compute per-week.
            total_logins = 0  # handled in the weekly loop below
        else:
            total_logins = int(n_users * base_rate * months)

        domain = _domain(cust["company_name"])
        platform_dist = LOGIN_PLATFORMS[seg]
        platforms = list(platform_dist.keys())
        platform_weights = np.array(list(platform_dist.values()))

        if problem == "pinnacle":
            # Generate emails for active subset only
            active_emails = [f"user_{i}@{domain}" for i in range(active_users)]
        else:
            active_emails = [f"user_{i}@{domain}" for i in range(n_users)]

        if problem == "brightpath":
            # Week-by-week declining: weeks 0-2 healthy, weeks 3-6 declining
            # Weeks 0-2 at full rate, then scale: 0.85, 0.65, 0.45, 0.35
            week_scales = [1.0, 1.0, 1.0, 0.85, 0.65, 0.45, 0.35]
            weekly_base = n_users * base_rate / 4.33  # monthly to weekly

            for week_idx in range(7):
                week_start = start + timedelta(days=week_idx * 7)
                week_end = week_start + timedelta(days=6)
                wk_weekdays = [d for d in weekdays if week_start <= d <= week_end]
                wk_weekends = [d for d in weekends if week_start <= d <= week_end]
                n_logins = max(1, int(weekly_base * week_scales[week_idx]))

                n_weekday = int(n_logins * WEEKDAY_SHARE["logins"])
                n_weekend = n_logins - n_weekday

                for _ in range(n_weekday):
                    if not wk_weekdays:
                        continue
                    d = pick_weekday(rng, wk_weekdays)
                    h, m, s = pick_time_of_day(rng)
                    email = active_emails[int(rng.integers(0, len(active_emails)))]
                    plat = rng.choice(platforms, p=platform_weights)
                    counter += 1
                    rows.append({
                        "login_id": f"LOGIN-{counter:07d}",
                        "customer_id": cust["customer_id"],
                        "user_email": email,
                        "login_timestamp": make_timestamp(d, h, m, s),
                        "platform": plat,
                    })

                for _ in range(n_weekend):
                    if not wk_weekends:
                        continue
                    d = wk_weekends[int(rng.integers(0, len(wk_weekends)))]
                    h, m, s = pick_time_of_day(rng)
                    email = active_emails[int(rng.integers(0, len(active_emails)))]
                    plat = rng.choice(platforms, p=platform_weights)
                    counter += 1
                    rows.append({
                        "login_id": f"LOGIN-{counter:07d}",
                        "customer_id": cust["customer_id"],
                        "user_email": email,
                        "login_timestamp": make_timestamp(d, h, m, s),
                        "platform": plat,
                    })
        else:
            # Standard distribution across weekdays/weekends
            n_weekday = int(total_logins * WEEKDAY_SHARE["logins"])
            n_weekend = total_logins - n_weekday

            for _ in range(n_weekday):
                d = pick_weekday(rng, weekdays)
                h, m, s = pick_time_of_day(rng)
                email = active_emails[int(rng.integers(0, len(active_emails)))]
                plat = rng.choice(platforms, p=platform_weights)
                counter += 1
                rows.append({
                    "login_id": f"LOGIN-{counter:07d}",
                    "customer_id": cust["customer_id"],
                    "user_email": email,
                    "login_timestamp": make_timestamp(d, h, m, s),
                    "platform": plat,
                })

            for _ in range(n_weekend):
                if not weekends:
                    continue
                d = weekends[int(rng.integers(0, len(weekends)))]
                h, m, s = pick_time_of_day(rng)
                email = active_emails[int(rng.integers(0, len(active_emails)))]
                plat = rng.choice(platforms, p=platform_weights)
                counter += 1
                rows.append({
                    "login_id": f"LOGIN-{counter:07d}",
                    "customer_id": cust["customer_id"],
                    "user_email": email,
                    "login_timestamp": make_timestamp(d, h, m, s),
                    "platform": plat,
                })

    return rows


def generate_calendar_events(rng: np.random.Generator, start: date, end: date) -> list[dict]:
    """Generate calendar event rows. ~20% of users are organizers."""
    weekdays = get_weekdays(start, end)
    weekends = get_weekends(start, end)
    total_days = (end - start).days + 1
    months = total_days / 30.0

    rows = []
    counter = 0

    for cust in CUSTOMERS:
        seg = cust["segment"]
        baselines = SEGMENT_BASELINES[seg]
        n_users = cust["licensed_users"]
        problem = cust["problem"]
        domain = _domain(cust["company_name"])

        # ~20% of users are meeting organizers
        n_organizers = max(1, int(n_users * 0.20))
        organizer_emails = [f"user_{i}@{domain}" for i in range(n_organizers)]

        rate_factor = 1.0 + rng.uniform(-0.15, 0.15)
        base_rate = baselines["events_per_user_month"] * rate_factor

        cal_dist = CAL_PLATFORMS[seg]
        cal_platforms = list(cal_dist.keys())
        cal_weights = np.array(list(cal_dist.values()))

        if problem == "verdant":
            # Very few events: 3/user/month vs baseline 10
            effective_rate = 3.0 * rate_factor
        elif problem == "brightpath":
            effective_rate = base_rate  # handled per-week below
        else:
            effective_rate = base_rate

        # Total events = organizers * rate * months
        if problem == "brightpath":
            total_events = 0  # per-week
        else:
            total_events = int(n_organizers * effective_rate * months)

        if problem == "brightpath":
            week_scales = [1.0, 1.0, 1.0, 0.85, 0.65, 0.45, 0.35]
            weekly_base = n_organizers * base_rate / 4.33

            for week_idx in range(7):
                week_start = start + timedelta(days=week_idx * 7)
                week_end = week_start + timedelta(days=6)
                wk_weekdays = [d for d in weekdays if week_start <= d <= week_end]
                wk_weekends = [d for d in weekends if week_start <= d <= week_end]
                n_events = max(1, int(weekly_base * week_scales[week_idx]))
                n_wd = int(n_events * WEEKDAY_SHARE["calendar_events"])
                n_we = n_events - n_wd

                for _ in range(n_wd):
                    if not wk_weekdays:
                        continue
                    d = pick_weekday(rng, wk_weekdays)
                    h, m, s = pick_time_of_day(rng)
                    dur = max(15, int(rng.normal(45, 15)))
                    dur = min(dur, 120)
                    end_dt = datetime(d.year, d.month, d.day, h, m, s) + timedelta(minutes=dur)
                    org = organizer_emails[int(rng.integers(0, len(organizer_emails)))]
                    invited = max(2, int(rng.normal(6, 3)))
                    counter += 1
                    rows.append({
                        "event_id": f"EVT-{counter:07d}",
                        "customer_id": cust["customer_id"],
                        "organizer_email": org,
                        "event_date": d.isoformat(),
                        "start_time": make_timestamp(d, h, m, s),
                        "end_time": end_dt.isoformat(),
                        "invited_count": invited,
                        "cal_platform": rng.choice(cal_platforms, p=cal_weights),
                    })

                for _ in range(n_we):
                    if not wk_weekends:
                        continue
                    d = wk_weekends[int(rng.integers(0, len(wk_weekends)))]
                    h, m, s = pick_time_of_day(rng)
                    dur = max(15, int(rng.normal(45, 15)))
                    dur = min(dur, 120)
                    end_dt = datetime(d.year, d.month, d.day, h, m, s) + timedelta(minutes=dur)
                    org = organizer_emails[int(rng.integers(0, len(organizer_emails)))]
                    invited = max(2, int(rng.normal(6, 3)))
                    counter += 1
                    rows.append({
                        "event_id": f"EVT-{counter:07d}",
                        "customer_id": cust["customer_id"],
                        "organizer_email": org,
                        "event_date": d.isoformat(),
                        "start_time": make_timestamp(d, h, m, s),
                        "end_time": end_dt.isoformat(),
                        "invited_count": invited,
                        "cal_platform": rng.choice(cal_platforms, p=cal_weights),
                    })
        else:
            n_wd = int(total_events * WEEKDAY_SHARE["calendar_events"])
            n_we = total_events - n_wd

            for _ in range(n_wd):
                d = pick_weekday(rng, weekdays)
                h, m, s = pick_time_of_day(rng)
                dur = max(15, int(rng.normal(45, 15)))
                dur = min(dur, 120)
                end_dt = datetime(d.year, d.month, d.day, h, m, s) + timedelta(minutes=dur)
                org = organizer_emails[int(rng.integers(0, len(organizer_emails)))]
                invited = max(2, int(rng.normal(6, 3)))
                counter += 1
                rows.append({
                    "event_id": f"EVT-{counter:07d}",
                    "customer_id": cust["customer_id"],
                    "organizer_email": org,
                    "event_date": d.isoformat(),
                    "start_time": make_timestamp(d, h, m, s),
                    "end_time": end_dt.isoformat(),
                    "invited_count": invited,
                    "cal_platform": rng.choice(cal_platforms, p=cal_weights),
                })

            for _ in range(n_we):
                if not weekends:
                    continue
                d = weekends[int(rng.integers(0, len(weekends)))]
                h, m, s = pick_time_of_day(rng)
                dur = max(15, int(rng.normal(45, 15)))
                dur = min(dur, 120)
                end_dt = datetime(d.year, d.month, d.day, h, m, s) + timedelta(minutes=dur)
                org = organizer_emails[int(rng.integers(0, len(organizer_emails)))]
                invited = max(2, int(rng.normal(6, 3)))
                counter += 1
                rows.append({
                    "event_id": f"EVT-{counter:07d}",
                    "customer_id": cust["customer_id"],
                    "organizer_email": org,
                    "event_date": d.isoformat(),
                    "start_time": make_timestamp(d, h, m, s),
                    "end_time": end_dt.isoformat(),
                    "invited_count": invited,
                    "cal_platform": rng.choice(cal_platforms, p=cal_weights),
                })

    return rows


def generate_device_telemetry(rng: np.random.Generator, start: date, end: date) -> list[dict]:
    """Generate device telemetry — 1 reading per device every 5 min, 8am-6pm weekdays."""
    weekdays = get_weekdays(start, end)
    # 8:00 to 17:55 = 120 readings per device per day
    time_slots = []
    for h in range(8, 18):
        for m in range(0, 60, 5):
            time_slots.append((h, m))

    rows = []
    counter = 0

    for cust in CUSTOMERS:
        problem = cust["problem"]
        n_rooms = cust["conference_rooms"]
        cid_prefix = cust["customer_id"].split("-")[1]  # e.g. "E001"

        for room_idx in range(n_rooms):
            device_id = f"DEV-{cid_prefix}-{room_idx:03d}"
            room_name = f"Room {room_idx + 1}"

            for d in weekdays:
                for h, m in time_slots:
                    # Generate telemetry values
                    if problem == "coastal":
                        # Bad telemetry: high latency, high packet loss, low quality
                        cpu = max(0, min(100, rng.normal(40.0, 10.0)))
                        mem = max(0, min(100, rng.normal(55.0, 12.0)))
                        latency = max(5, rng.normal(95.0, 20.0))
                        pkt_loss = max(0, rng.normal(4.0, 1.0))
                        vid_quality = max(1.0, min(5.0, rng.normal(2.2, 0.4)))
                    else:
                        cpu = max(0, min(100, rng.normal(*TELEMETRY_HEALTHY["cpu_usage_pct"])))
                        mem = max(0, min(100, rng.normal(*TELEMETRY_HEALTHY["memory_usage_pct"])))
                        latency = max(1, rng.normal(*TELEMETRY_HEALTHY["network_latency_ms"]))
                        pkt_loss = max(0, rng.normal(*TELEMETRY_HEALTHY["packet_loss_pct"]))
                        vid_quality = max(1.0, min(5.0, rng.normal(*TELEMETRY_HEALTHY["video_quality_score"])))

                    counter += 1
                    rows.append({
                        "telemetry_id": f"TEL-{counter:08d}",
                        "customer_id": cust["customer_id"],
                        "device_id": device_id,
                        "room_name": room_name,
                        "timestamp": make_timestamp(d, h, m, 0),
                        "cpu_usage_pct": round(cpu, 2),
                        "memory_usage_pct": round(mem, 2),
                        "network_latency_ms": round(latency, 2),
                        "packet_loss_pct": round(pkt_loss, 4),
                        "video_quality_score": round(vid_quality, 2),
                    })

    return rows


def generate_calls(rng: np.random.Generator, start: date, end: date) -> list[dict]:
    """Generate call rows for all customers."""
    weekdays = get_weekdays(start, end)
    weekends = get_weekends(start, end)
    total_days = (end - start).days + 1
    months = total_days / 30.0

    rows = []
    counter = 0

    for cust in CUSTOMERS:
        seg = cust["segment"]
        baselines = SEGMENT_BASELINES[seg]
        n_users = cust["licensed_users"]
        problem = cust["problem"]
        domain = _domain(cust["company_name"])

        rate_factor = 1.0 + rng.uniform(-0.15, 0.15)
        base_rate = baselines["calls_per_user_month"] * rate_factor
        avg_parts = baselines["avg_participants"]

        # calls = user_participation_events / avg_participants
        dur_cfg = CALL_DURATION[seg]

        if problem == "brightpath":
            total_calls = 0  # per-week
        else:
            total_calls = int(n_users * base_rate * months / avg_parts)

        # Determine ad-hoc ratio
        if problem == "quantum":
            adhoc_ratio = 0.03  # nearly zero ad-hoc
        else:
            adhoc_ratio = baselines["adhoc_ratio"]

        user_emails = [f"user_{i}@{domain}" for i in range(n_users)]

        def _make_call(d, is_adhoc):
            nonlocal counter
            h, m, s = pick_time_of_day(rng)
            duration = int(np.clip(rng.normal(dur_cfg["mean"], dur_cfg["std"]),
                                   dur_cfg["min"], dur_cfg["max"]))
            parts = max(2, int(rng.normal(avg_parts, 1)))
            initiator = user_emails[int(rng.integers(0, len(user_emails)))]

            if problem == "quantum":
                # Bad call quality
                qual = max(1.0, min(5.0, rng.normal(2.8, 0.5)))
                drops = max(0, int(rng.normal(2.1, 1.0)))
            else:
                qual = max(1.0, min(5.0, rng.normal(*CALL_QUALITY_HEALTHY["avg_quality_score"])))
                drops = max(0, int(rng.poisson(CALL_QUALITY_HEALTHY["drop_count"][0])))

            counter += 1
            return {
                "call_id": f"CALL-{counter:07d}",
                "customer_id": cust["customer_id"],
                "initiator_email": initiator,
                "start_timestamp": make_timestamp(d, h, m, s),
                "duration_minutes": duration,
                "participant_count": parts,
                "call_type": "ad_hoc" if is_adhoc else "scheduled",
                "avg_quality_score": round(qual, 2),
                "drop_count": drops,
            }

        if problem == "brightpath":
            week_scales = [1.0, 1.0, 1.0, 0.85, 0.65, 0.45, 0.35]
            weekly_base = n_users * base_rate / avg_parts / 4.33

            for week_idx in range(7):
                week_start = start + timedelta(days=week_idx * 7)
                week_end = week_start + timedelta(days=6)
                wk_weekdays = [d for d in weekdays if week_start <= d <= week_end]
                wk_weekends = [d for d in weekends if week_start <= d <= week_end]
                n_calls = max(1, int(weekly_base * week_scales[week_idx]))
                n_wd = int(n_calls * WEEKDAY_SHARE["calls"])
                n_we = n_calls - n_wd

                for _ in range(n_wd):
                    if not wk_weekdays:
                        continue
                    d = pick_weekday(rng, wk_weekdays)
                    is_adhoc = rng.random() < adhoc_ratio
                    rows.append(_make_call(d, is_adhoc))

                for _ in range(n_we):
                    if not wk_weekends:
                        continue
                    d = wk_weekends[int(rng.integers(0, len(wk_weekends)))]
                    is_adhoc = rng.random() < adhoc_ratio
                    rows.append(_make_call(d, is_adhoc))
        else:
            n_wd = int(total_calls * WEEKDAY_SHARE["calls"])
            n_we = total_calls - n_wd

            for _ in range(n_wd):
                d = pick_weekday(rng, weekdays)
                is_adhoc = rng.random() < adhoc_ratio
                rows.append(_make_call(d, is_adhoc))

            for _ in range(n_we):
                if not weekends:
                    continue
                d = weekends[int(rng.integers(0, len(weekends)))]
                is_adhoc = rng.random() < adhoc_ratio
                rows.append(_make_call(d, is_adhoc))

    return rows


# ---------------------------------------------------------------------------
# BigQuery loading
# ---------------------------------------------------------------------------

def load_to_bigquery(client: bigquery.Client, dataset_ref: str,
                     table_name: str, rows: list[dict]):
    """Load rows into BigQuery via newline-delimited JSON."""
    if not rows:
        print(f"  {table_name}: 0 rows (skipping)")
        return

    table_id = f"{dataset_ref}.{table_name}"

    # Write JSONL to in-memory buffer
    buf = BytesIO()
    for row in rows:
        buf.write((json.dumps(row) + "\n").encode("utf-8"))
    buf.seek(0)

    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )

    job = client.load_table_from_file(buf, table_id, job_config=job_config)
    job.result()  # Wait for completion

    table = client.get_table(table_id)
    print(f"  {table_name}: {table.num_rows:,} rows loaded")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Generate Cymbal Meet synthetic data")
    parser.add_argument("--dry-run", action="store_true",
                        help="Generate data and print counts without loading to BigQuery")
    args = parser.parse_args()

    start, end = compute_date_range()
    print(f"Date range: {start} to {end} (7 weeks, {len(get_weekdays(start, end))} weekdays)")

    # Generate all tables with per-table seeds
    print("\nGenerating customers...")
    customers = generate_customers(np.random.default_rng(SEED_CUSTOMERS), start, end)
    print(f"  {len(customers)} rows")

    print("Generating logins...")
    logins = generate_logins(np.random.default_rng(SEED_LOGINS), start, end)
    print(f"  {len(logins):,} rows")

    print("Generating calendar_events...")
    cal_events = generate_calendar_events(np.random.default_rng(SEED_CALENDAR), start, end)
    print(f"  {len(cal_events):,} rows")

    print("Generating device_telemetry (this takes a moment)...")
    telemetry = generate_device_telemetry(np.random.default_rng(SEED_TELEMETRY), start, end)
    print(f"  {len(telemetry):,} rows")

    print("Generating calls...")
    calls = generate_calls(np.random.default_rng(SEED_CALLS), start, end)
    print(f"  {len(calls):,} rows")

    total = len(customers) + len(logins) + len(cal_events) + len(telemetry) + len(calls)
    print(f"\nTotal: {total:,} rows across 5 tables")

    if args.dry_run:
        print("\n--dry-run: skipping BigQuery load")
        return

    project_id = get_project_id()
    client = bigquery.Client(project=project_id)
    dataset_ref = f"{project_id}.{DATASET_ID}"

    print(f"\nLoading into {dataset_ref}...")
    load_to_bigquery(client, dataset_ref, "customers", customers)
    load_to_bigquery(client, dataset_ref, "logins", logins)
    load_to_bigquery(client, dataset_ref, "calendar_events", cal_events)
    load_to_bigquery(client, dataset_ref, "device_telemetry", telemetry)
    load_to_bigquery(client, dataset_ref, "calls", calls)

    print("\nDone. All synthetic data loaded into BigQuery.")


if __name__ == "__main__":
    main()
