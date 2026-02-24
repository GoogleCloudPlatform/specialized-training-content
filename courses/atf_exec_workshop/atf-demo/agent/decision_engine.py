"""
Select interventions for companies with engagement issues.

Based on the issues found by the analyzer, picks from three
intervention types:
  1. Admin Weekly Email (auto-execute, any issue)
  2. Calendar Extension In-App Messaging (needs approval, calendar <50%)
  3. Device Performance Email (auto-execute, device issues)
"""

import random

random.seed(123)  # Reproducible for demo


# Feature recommendations keyed by (segment, primary_issue_metric)
FEATURE_RECS = {
    ("Enterprise", "7da_users"): {
        "name": "User Onboarding Webinar Series",
        "description": "Structured training for new and existing users",
        "relevance": "Enterprise organizations see 40%+ adoption increase "
                     "with formal onboarding programs",
        "why_recommended": "Based on your organization's size and the gap "
                           "between licensed seats and weekly active users, "
                           "structured onboarding is the highest-leverage "
                           "investment to close that adoption gap.",
    },
    ("Mid-Market", "7da_users"): {
        "name": "Team Champion Program",
        "description": "Designate and train power users in each department",
        "relevance": "Mid-sized teams see 35% higher adoption with "
                     "internal champions",
        "why_recommended": "Your team size and departmental structure make "
                           "a champion-led rollout especially effective — "
                           "accounts with similar profiles saw adoption "
                           "climb 35% within 60 days of launching this program.",
    },
    ("SMB", "7da_users"): {
        "name": "Quick Start Video Series",
        "description": "5-minute tutorials covering essential features",
        "relevance": "Get your team productive fast with bite-sized training",
        "why_recommended": "Smaller teams benefit most from self-serve "
                           "enablement. Your current active-user ratio "
                           "suggests several team members haven't explored "
                           "key features — short videos are the fastest "
                           "path to change that.",
    },
    ("Enterprise", "calendar_meetings"): {
        "name": "Calendar Integration Masterclass",
        "description": "Live workshop on maximizing scheduler productivity",
        "relevance": "Customers using calendar features save 2hrs/week "
                     "per user",
        "why_recommended": "Your calendared-meeting volume is well below "
                           "what we typically see for an account of your "
                           "size. Similar enterprise customers who adopted "
                           "calendar integration reclaimed an average of "
                           "2 hours per user per week.",
    },
    ("Mid-Market", "calendar_meetings"): {
        "name": "Calendar Integration Masterclass",
        "description": "Live workshop on maximizing scheduler productivity",
        "relevance": "Customers using calendar features save 2hrs/week "
                     "per user",
        "why_recommended": "Your team's meeting patterns indicate "
                           "scheduling is still happening outside Cymbal "
                           "Meet. Mid-market peers who integrated their "
                           "calendars saw a measurable drop in no-shows "
                           "and scheduling conflicts.",
    },
    ("SMB", "calendar_meetings"): {
        "name": "Calendar Integration Masterclass",
        "description": "Live workshop on maximizing scheduler productivity",
        "relevance": "Customers using calendar features save 2hrs/week "
                     "per user",
        "why_recommended": "Small teams get outsized benefit from calendar "
                           "integration — it removes friction from the "
                           "scheduling step that often keeps people on "
                           "competing tools. Your usage data suggests this "
                           "is a quick win.",
    },
}

DEFAULT_FEATURE_REC = {
    "name": "Meeting Analytics Dashboard",
    "description": "Track usage patterns and identify optimization "
                   "opportunities",
    "relevance": "Data-driven insights to improve meeting culture",
    "why_recommended": "Your account's engagement patterns reveal "
                       "untapped potential. The Analytics Dashboard will "
                       "surface the specific usage trends driving your "
                       "metrics, so your team can focus on the areas "
                       "with the biggest impact.",
}

# Room names for device issues
ROOM_NAMES = [
    "Conference Room A - Main", "Conference Room B - East",
    "Conference Room C - West", "Executive Boardroom",
    "Training Room 1", "Training Room 2",
    "Huddle Room 3A", "Huddle Room 3B",
    "All-Hands Room", "Client Meeting Room",
]

ROOM_LOCATIONS = [
    "Building 1, Floor 1", "Building 1, Floor 2",
    "Building 1, Floor 3", "Building 2, Floor 1",
    "Building 2, Floor 2", "Building 3, Floor 1",
]


def get_feature_recommendation(segment, issues):
    """Pick the most relevant feature recommendation."""
    # Find the worst issue metric
    primary_metric = max(issues, key=lambda i: i["gap_pct"])["metric"]
    key = (segment, primary_metric)
    return FEATURE_RECS.get(key, DEFAULT_FEATURE_REC)


def get_positive_metrics(engagement_data):
    """Find metrics that are above 80% of target (the good news)."""
    targets = engagement_data["targets"]
    averages = engagement_data["averages"]
    positives = []
    for metric in ["7da_users", "call_volume", "device_utilization",
                    "dialin_sessions", "calendar_meetings"]:
        target = targets[metric]
        actual = averages[metric]
        if target > 0 and actual / target >= 0.80:
            ratio = round(actual / target, 2)
            # Generate a plausible cohort percentile — higher for stronger metrics
            if ratio >= 1.0:
                pctile = random.randint(88, 97)
            elif ratio >= 0.90:
                pctile = random.randint(78, 92)
            else:
                pctile = random.randint(65, 82)
            positives.append({
                "metric": metric,
                "actual": actual,
                "target": target,
                "ratio": ratio,
                "percentile": pctile,
            })
    return positives


def generate_device_issues(company):
    """Create a list of 2-5 fake problem devices for a company."""
    num = min(random.randint(2, 5), company["purchased_boxes"])
    rooms = random.sample(ROOM_NAMES, num)
    devices = []
    for room in rooms:
        devices.append({
            "name": room,
            "location": random.choice(ROOM_LOCATIONS),
            "avg_fps": random.randint(11, 19),
            "avg_resolution": random.choice(["480p", "680p", "720p"]),
            "issues": [],
        })
        d = devices[-1]
        if d["avg_fps"] < 20:
            d["issues"].append("Low FPS")
        if d["avg_resolution"] in ("480p", "680p"):
            d["issues"].append("Low Resolution")
    return devices


def _has_crm_signal(activities, company_id, keywords):
    """Check if any CRM activity note for this company contains keywords."""
    for a in activities:
        if a["company_id"] != company_id:
            continue
        note = a.get("note", "").lower()
        if any(kw in note for kw in keywords):
            return True
    return False


def select_remediations(company, issues, activities):
    """
    For each issue metric, pick an appropriate remediation action based on
    CRM signals and company attributes.

    Returns a list of remediation dicts, each with:
      - metric: which metric this addresses
      - name: short title
      - description: what the action involves
      - rationale: why this was chosen (references CRM data)
    """
    cid = company["company_id"]
    segment = company["segment"]
    remediations = []

    for issue in issues:
        metric = issue["metric"]

        # --- Low 7-Day Active Users ---
        if metric == "7da_users":
            has_change_mgmt = _has_crm_signal(
                activities, cid,
                ["change management", "department heads", "slow to promote"],
            )
            if has_change_mgmt:
                # Option B: Executive Sponsor Enablement Kit
                remediations.append({
                    "metric": metric,
                    "name": "Executive Sponsor Enablement Kit",
                    "description": (
                        "Deliver a ready-made toolkit to the executive sponsor "
                        "including: talking points by department, a pre-built "
                        "internal email template for department heads, current "
                        "adoption metrics formatted for leadership review, and "
                        "a 30-day change management playbook. "
                        "<a href='#'>Download Executive Sponsor Kit (PDF)</a>"
                    ),
                    "rationale": (
                        "CRM notes indicate department heads have been slow to "
                        "promote adoption and the admin has requested change "
                        "management assets. Top-down executive sponsorship is "
                        "the most effective lever for enterprise adoption."
                    ),
                })
            else:
                # Option C: Inactive User Re-engagement Drip
                remediations.append({
                    "metric": metric,
                    "name": "Inactive User Re-engagement Drip",
                    "description": (
                        "Launch a 3-part automated email sequence targeting "
                        "users inactive for 7+ days: (1) 'Here's what your "
                        "team discussed this week' with meeting highlights, "
                        "(2) 'New features since your last visit' showcasing "
                        "recent improvements, (3) 'Your account is ready' "
                        "with a one-click rejoin link."
                    ),
                    "rationale": (
                        "No CRM signals suggest an organizational blocker. "
                        "Directly re-engaging the inactive user cohort with "
                        "personalized content is the highest-yield automated "
                        "approach for this customer profile."
                    ),
                })

        # --- Low Dial-in Sessions ---
        elif metric == "dialin_sessions":
            mdm = company.get("mdm_system", "")
            if mdm:
                remediations.append({
                    "metric": metric,
                    "name": f"MDM Dial-in Contact Deployment ({mdm})",
                    "description": (
                        f"We've prepared a step-by-step deployment guide for "
                        f"pushing dedicated Cymbal Meet dial-in number contacts "
                        f"to all employee mobile devices via {mdm}. "
                        f"<a href='#'>Download {mdm} Deployment Guide (PDF)</a>"
                    ),
                    "rationale": (
                        f"This customer uses {mdm} for mobile device management. "
                        f"Pushing dial-in contacts directly to employee phones "
                        f"removes the biggest friction point — most users don't "
                        f"know the dial-in numbers exist or can't find them when "
                        f"they need to join from a phone."
                    ),
                })
            else:
                remediations.append({
                    "metric": metric,
                    "name": "Dial-in Quick Reference & Awareness Campaign",
                    "description": (
                        "Generate a branded one-page PDF with the company's "
                        "dedicated dial-in numbers, PIN format, and mobile "
                        "shortcut instructions. Distribute via admin email "
                        "and recommend posting in common areas near conference "
                        "rooms."
                    ),
                    "rationale": (
                        "No MDM system on file for automated phone contact "
                        "deployment. A manual reference card plus awareness "
                        "campaign addresses the knowledge gap that typically "
                        "suppresses dial-in adoption."
                    ),
                })

        # --- Low Call Volume ---
        elif metric == "call_volume":
            has_contest_signal = _has_crm_signal(
                activities, cid,
                ["contest", "challenge", "gamification", "leaderboard",
                 "competitive", "game"],
            )
            if has_contest_signal:
                remediations.append({
                    "metric": metric,
                    "name": "Cymbal Meet Call Contest",
                    "description": (
                        "Launch a 2-week company-wide call contest with "
                        "multiple category options: Most Calls Participated In, "
                        "Most Attendees in Calls You Host, Most External "
                        "Attendees Invited, and Longest Total Call Time. "
                        "Cymbal Meet provides product swag as prizes. "
                        "Notifications, real-time leaderboards, and weekly "
                        "standings emails can all be enabled on the backend "
                        "if the admin opts in. If you'd like to discuss further "
                        "or enable this contest, "
                        "<a href='#'>schedule a meeting with your CSM</a>."
                    ),
                    "rationale": (
                        "CRM notes indicate this customer has a competitive "
                        "team culture and has successfully run engagement "
                        "contests before. Gamification is a natural fit to "
                        "drive call volume adoption."
                    ),
                })
            else:
                remediations.append({
                    "metric": metric,
                    "name": "Department-Level Rollout Playbook",
                    "description": (
                        "Provide a phased rollout playbook targeting the 2-3 "
                        "departments with lowest call volume first. Includes "
                        "department-specific use cases, quick-start guides, "
                        "and a 30-day adoption tracking template."
                    ),
                    "rationale": (
                        "Focused department-by-department rollout is more "
                        "effective than organization-wide pushes for driving "
                        "call volume in large organizations."
                    ),
                })

        # --- Low Calendar Meetings ---
        elif metric == "calendar_meetings":
            # Check if in-app messaging intervention will be triggered (ratio < 0.80)
            # If so, note that it's being handled via in-app + CSM review
            if issue.get("ratio", 0) < 0.80:
                remediations.append({
                    "metric": metric,
                    "name": "Calendar Extension In-App Messaging Campaign",
                    "description": (
                        "A targeted in-app messaging campaign has been created "
                        "to promote calendar extension adoption among your users. "
                        "This intervention is pending review and approval by your "
                        "Customer Success Manager to ensure messaging timing and "
                        "targeting align with your rollout strategy."
                    ),
                    "rationale": (
                        "Calendar meeting adoption is strongly correlated with "
                        "extension installation rates. In-app messaging provides "
                        "contextual prompts at the moment users would benefit most, "
                        "with CSM oversight ensuring appropriate rollout pacing."
                    ),
                })
            else:
                # Calendar already has dedicated in-app messaging intervention;
                # add a supporting remediation for the email
                remediations.append({
                    "metric": metric,
                    "name": "Calendar Integration Activation Guide",
                    "description": (
                        "Send a step-by-step guide for enabling the Cymbal Meet "
                        "calendar extension across the organization. Includes "
                        "admin deployment instructions, user quick-start cards, "
                        "and a FAQ addressing common setup questions."
                    ),
                    "rationale": (
                        "Calendar meeting adoption is strongly correlated with "
                        "extension installation rates. Providing clear activation "
                        "instructions removes the primary friction point."
                    ),
                })

    return remediations


def select_interventions(company, issues, engagement_data, contacts,
                         activities=None):
    """
    Given a company and its issues, return a list of intervention dicts.

    Each intervention has: type, auto_execute, and type-specific fields.
    """
    interventions = []
    segment = company["segment"]
    cid = company["company_id"]

    # Find primary contact for this company
    primary = next(
        (c for c in contacts if c["company_id"] == cid and c["is_primary"]),
        contacts[0] if contacts else {"full_name": "Admin", "role": "Admin"},
    )

    positive_metrics = get_positive_metrics(engagement_data)
    feature_rec = get_feature_recommendation(segment, issues)

    # Add cohort percentiles to improvement issues (modest: 40-75%)
    enriched_issues = []
    for iss in issues:
        enriched = dict(iss)
        ratio = enriched.get("ratio", 0)
        if ratio < 0.50:
            enriched["percentile"] = random.randint(38, 52)
        elif ratio < 0.70:
            enriched["percentile"] = random.randint(50, 68)
        else:
            enriched["percentile"] = random.randint(62, 78)
        enriched_issues.append(enriched)

    # Synthesize positive feedback into common themes (as if LLM-summarized)
    POSITIVE_THEMES = [
        "Reliable audio and video quality across devices",
        "Intuitive interface with minimal learning curve",
        "Seamless calendar and scheduling integration",
        "Strong mobile experience for remote participants",
        "Consistent connection stability in meetings",
        "Effective screen sharing and collaboration tools",
    ]

    NEGATIVE_THEMES = [
        "Adoption among infrequent users remains a challenge",
        "Calendar scheduling workflow could be streamlined",
        "Feature discoverability needs improvement",
        "Occasional audio issues in larger conference rooms",
        "Admin controls and user management need more depth",
    ]

    pos_feedback = engagement_data.get("feedback", [])
    pos_count = sum(1 for f in pos_feedback if f in [
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
    ])
    neg_count = sum(1 for f in pos_feedback if f in [
        "Wish more of our team actually used this regularly",
        "Calendar integration could be much better",
        "Some features are hard to discover",
        "We still default to a competitor for important meetings",
        "Connection drops occasionally during calls",
        "Audio echo issues in some conference rooms",
        "Too many steps to schedule a meeting",
        "Learning curve is steeper than expected",
        "Need better admin controls for user management",
    ])

    # Pick 2-3 themes based on what feedback exists
    themed_positive = random.sample(POSITIVE_THEMES, min(3, len(POSITIVE_THEMES)))
    themed_negative = random.sample(NEGATIVE_THEMES, min(3, len(NEGATIVE_THEMES)))

    # --- Select metric-specific remediations ---
    remediations = select_remediations(
        company, enriched_issues, activities or []
    )

    # --- Intervention 1: Admin Weekly Email (always, if any issues) ---
    interventions.append({
        "type": "admin_email",
        "auto_execute": True,
        "recipient": primary["full_name"],
        "recipient_role": primary["role"],
        "highlights": positive_metrics,
        "improvements": enriched_issues,
        "feature_rec": feature_rec,
        "feedback_positive": themed_positive,
        "feedback_negative": themed_negative,
        "remediations": remediations,
    })

    # --- Intervention 2: Calendar Extension In-App Messaging ---
    calendar_issue = next(
        (i for i in issues if i["metric"] == "calendar_meetings"),
        None,
    )
    if calendar_issue and calendar_issue["ratio"] < 0.80:
        licensed = company["licensed_users"]
        install_rate = round(random.uniform(0.35, 0.55), 2)
        usage_rate = round(random.uniform(0.20, 0.40), 2)
        no_ext_count = int(licensed * (1 - install_rate))
        low_usage_count = int(licensed * install_rate * (1 - usage_rate))

        interventions.append({
            "type": "inapp_calendar",
            "auto_execute": False,  # Needs CSM approval
            "install_rate": install_rate,
            "usage_rate": usage_rate,
            "message_a": {
                "target": "no_extension",
                "user_count": no_ext_count,
                "headline": "Schedule Meetings Faster",
                "body": (
                    "Save time and reduce friction! Install the Cymbal "
                    "Meet scheduler extension to add video meetings "
                    "directly from your calendar."
                ),
                "cta": "Install Now",
            },
            "message_b": {
                "target": "has_extension_low_usage",
                "user_count": low_usage_count,
                "headline": "Get More from Your Meeting Scheduler",
                "body": (
                    "We noticed you have the Cymbal Meet extension "
                    "installed\u2014great! Here are some tips to make "
                    "scheduling even easier."
                ),
                "cta": "Watch Tutorial",
            },
        })

    # --- Intervention 3: Device Performance Email ---
    device_issue = next(
        (i for i in issues if i["metric"] == "device_utilization"),
        None,
    )
    from data.engagement import PROBLEM_PROFILES
    has_device_flag = PROBLEM_PROFILES.get(cid, {}).get("device_issues")

    if device_issue or has_device_flag:
        devices = generate_device_issues(company)
        interventions.append({
            "type": "device_email",
            "auto_execute": True,
            "recipient": primary["full_name"],
            "recipient_role": primary["role"],
            "devices": devices,
        })

    return interventions
