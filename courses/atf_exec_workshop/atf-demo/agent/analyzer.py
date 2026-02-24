"""
Analyze engagement metrics to find companies with issues.

Compares 30-day averages against targets and flags any metric
that's more than 20% below target.
"""


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
        if ratio < 0.80:
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
        from data.engagement import NEGATIVE_COMMENTS
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


def find_all_issues(companies, engagement):
    """
    Scan all companies and return a dict of {company_id: [issues]}.

    Only includes companies that have at least one issue.
    """
    results = {}
    for company in companies:
        cid = company["company_id"]
        eng = engagement[cid]
        issues = find_issues(company, eng)
        if issues:
            results[cid] = issues
    return results
