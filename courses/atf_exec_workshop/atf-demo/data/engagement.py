"""
Generate 30 days of engagement metrics for each company.

Each company gets a "trend" (growing, flat, declining) and a base
performance level per metric. We pre-generate all 30 days on startup
so the data is consistent across page loads.

The PRD specifies these customers should be "problem" customers with
metrics >20% below target (used to trigger agent interventions):
  - Nexus Tech (1): low 7da_users, low calendar_meetings
  - GreenLeaf (2): device performance issues
  - BlueHorizon (3): low call_volume
  - Summit Peak (4): multiple issues (low 7da_users, low calendar)
  - Apex Mfg (6): low calendar_meetings
  - Vanguard Health (8): mostly fine, one concern (low dialin)
  - Velocity Motors (17): low 7da_users
"""

import random

# Seed for reproducible demo data
random.seed(42)

# Feedback comment templates from the PRD
POSITIVE_COMMENTS = [
    "Audio quality is consistently excellent",
    "Screen sharing is smooth and reliable",
    "Very easy to join meetings from any device",
    "Love the mobile app - works great on the go",
    "Connection is always stable",
    "Interface is intuitive and clean",
    "Best video quality we've seen",
    "Dial-in option is super helpful for remote folks",
    "Integration with our calendar is seamless",
    "Recording feature is fantastic for documentation",
]

NEGATIVE_COMMENTS = [
    "Wish more of our team actually used this regularly",
    "Calendar integration could be much better",
    "Some features are hard to discover",
    "We still default to a competitor for important meetings",
    "Connection drops occasionally during calls",
    "Audio echo issues in some conference rooms",
    "Mobile app drains battery quickly",
    "Too many steps to schedule a meeting",
    "Learning curve is steeper than expected",
    "Need better admin controls for user management",
]

NEUTRAL_COMMENTS = [
    "Works fine for our needs",
    "Does what we need it to do",
    "Good enough",
    "No major complaints",
    "Pretty standard videoconferencing tool",
    "Gets the job done",
    "Meets expectations",
]

# Which companies have issues and what kind.
# Keys are company_id, values describe which metrics to suppress.
PROBLEM_PROFILES = {
    1: {  # Nexus Tech
        "trend": "declining",
        "suppress": {"7da_users": 0.75, "calendar_meetings": 0.48},
    },
    2: {  # GreenLeaf
        "trend": "declining",
        "suppress": {"device_utilization": 0.74, "dialin_sessions": 0.75},
        "device_issues": True,
    },
    3: {  # BlueHorizon
        "trend": "declining",
        "suppress": {"call_volume": 0.76},
    },
    4: {  # Summit Peak
        "trend": "declining",
        "suppress": {"7da_users": 0.76, "calendar_meetings": 0.55},
    },
    6: {  # Apex Mfg
        "trend": "declining",
        "suppress": {"calendar_meetings": 0.50},
    },
    8: {  # Vanguard Health
        "trend": "flat",
        "suppress": {"dialin_sessions": 0.76},
    },
    17: {  # Velocity Motors
        "trend": "declining",
        "suppress": {"7da_users": 0.75},
    },
}


def calculate_targets(company):
    """Calculate engagement targets for a company based on PRD formulas."""
    lu = company["licensed_users"]
    pb = company["purchased_boxes"]
    return {
        "7da_users": round(lu * 0.70),
        "call_volume": round(lu * 7),
        "device_utilization": round(pb * 5),
        "dialin_sessions": round(lu * 7 * 0.20),
        "calendar_meetings": round(lu * 7 * 0.70),
        "feedback_score": 4.0,
    }


def generate_metrics_for_company(company):
    """
    Generate 30 days of metrics for one company.

    Returns a dict with:
      - targets: dict of target values
      - daily: list of 30 dicts (day 0 = oldest, day 29 = most recent)
      - averages: dict of 30-day averages (the "actual" values)
      - trend: "growing", "flat", or "declining"
      - feedback: list of comment strings
    """
    cid = company["company_id"]
    targets = calculate_targets(company)
    profile = PROBLEM_PROFILES.get(cid)

    # Determine trend
    if profile:
        trend = profile["trend"]
    else:
        # Healthy companies: mostly flat, a few growing
        trend = random.choice(["flat", "flat", "flat", "growing"])

    # Base performance ratios (how close to target on average)
    # Healthy companies perform at 85-110% of target
    base_ratios = {}
    metric_names = [
        "7da_users", "call_volume", "device_utilization",
        "dialin_sessions", "calendar_meetings",
    ]
    for m in metric_names:
        if profile and m in profile.get("suppress", {}):
            # Problem metric: use the suppressed ratio
            base_ratios[m] = profile["suppress"][m]
        else:
            # Healthy metric: 85-110% of target
            base_ratios[m] = random.uniform(0.85, 1.10)

    # Generate 30 daily data points
    daily = []
    for day in range(30):
        day_data = {}
        for m in metric_names:
            target = targets[m]
            base = target * base_ratios[m]

            # For suppressed (problem) metrics: 2-phase curve
            # Phase 1 (days 0-14): above 80% of target
            # Phase 2 (days 15-29): below 80% of target
            # Overall average ~73-78%
            # Exception: calendar_meetings uses flat curve (50-85% range)
            is_suppressed = (
                profile and m in profile.get("suppress", {})
            )
            if is_suppressed and m != "calendar_meetings":
                avg_ratio = base_ratios[m]  # e.g. 0.75
                # Phase 1 multiplier pushes to ~85% of target
                # Phase 2 multiplier drops to ~65% of target
                phase1_mult = 0.85 / avg_ratio  # ~1.13
                phase2_mult = (2.0 * avg_ratio - 0.85) / avg_ratio  # ~0.87
                # Smooth transition around day 15
                if day <= 12:
                    phase_mult = phase1_mult
                elif day <= 17:
                    # Transition zone: linear blend
                    t = (day - 12) / 5.0
                    phase_mult = phase1_mult * (1 - t) + phase2_mult * t
                else:
                    phase_mult = phase2_mult
                noise = random.uniform(0.95, 1.05)
                value = base * phase_mult * noise
            else:
                # Healthy metric: apply trend + noise
                if trend == "growing":
                    multiplier = 1.0 + (day / 30) * 0.15
                elif trend == "declining":
                    multiplier = 1.05 - (day / 30) * 0.15
                else:
                    multiplier = 1.0
                noise = random.uniform(0.92, 1.08)
                value = base * multiplier * noise

            day_data[m] = round(max(0, value))

        # Feedback score: 1-5 scale
        if profile and len(profile.get("suppress", {})) > 1:
            day_data["feedback_score"] = round(
                random.uniform(3.2, 4.0), 1
            )
        elif profile:
            day_data["feedback_score"] = round(
                random.uniform(3.5, 4.2), 1
            )
        else:
            day_data["feedback_score"] = round(
                random.uniform(3.8, 4.6), 1
            )

        daily.append(day_data)

    # Calculate 30-day averages
    averages = {}
    for m in metric_names:
        averages[m] = round(sum(d[m] for d in daily) / 30)
    averages["feedback_score"] = round(
        sum(d["feedback_score"] for d in daily) / 30, 1
    )

    # Generate feedback comments (20-40 per company)
    num_comments = random.randint(20, 40)
    feedback = []
    for _ in range(num_comments):
        # Weight toward negative if problem customer
        if profile and len(profile.get("suppress", {})) > 0:
            r = random.random()
            if r < 0.35:
                feedback.append(random.choice(NEGATIVE_COMMENTS))
            elif r < 0.65:
                feedback.append(random.choice(NEUTRAL_COMMENTS))
            else:
                feedback.append(random.choice(POSITIVE_COMMENTS))
        else:
            r = random.random()
            if r < 0.15:
                feedback.append(random.choice(NEGATIVE_COMMENTS))
            elif r < 0.35:
                feedback.append(random.choice(NEUTRAL_COMMENTS))
            else:
                feedback.append(random.choice(POSITIVE_COMMENTS))

    return {
        "company_id": cid,
        "targets": targets,
        "daily": daily,
        "averages": averages,
        "trend": trend,
        "feedback": feedback,
    }


def generate_all_metrics(companies):
    """Generate engagement data for all companies. Returns dict keyed by company_id."""
    return {
        c["company_id"]: generate_metrics_for_company(c)
        for c in companies
    }
