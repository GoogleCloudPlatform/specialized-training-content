"""
Pull the last 100 Google Cloud Logging entries into a JSON file.

Usage:
    export GOOGLE_CLOUD_PROJECT=your-project-id
    python pull_cloud_logs.py

    # Optional: filter to a specific log name or resource
    python pull_cloud_logs.py --filter 'resource.type="cloud_run_revision"'

    # Optional: change output file
    python pull_cloud_logs.py --output my_logs.json
"""

import argparse
import json
import os
import sys

from google.cloud import logging as cloud_logging


def pull_logs(project_id: str, log_filter: str | None, limit: int) -> list[dict]:
    """Fetch the most recent log entries and return them as dicts."""
    client = cloud_logging.Client(project=project_id)

    entries = client.list_entries(
        filter_=log_filter,
        order_by=cloud_logging.DESCENDING,
        max_results=limit,
    )

    results = []
    for entry in entries:
        results.append({
            "timestamp": entry.timestamp.isoformat() if entry.timestamp else None,
            "severity": entry.severity,
            "log_name": entry.log_name,
            "resource": {
                "type": entry.resource.type if entry.resource else None,
                "labels": dict(entry.resource.labels) if entry.resource else {},
            },
            "payload": entry.payload if isinstance(entry.payload, (dict, str)) else str(entry.payload),
            "labels": dict(entry.labels) if entry.labels else {},
            "insert_id": entry.insert_id,
        })

    return results


def main():
    parser = argparse.ArgumentParser(description="Pull recent Google Cloud log entries to JSON.")
    parser.add_argument("--filter", default=None, help="Optional Cloud Logging filter string.")
    parser.add_argument("--output", default="cloud_logs.json", help="Output JSON file (default: cloud_logs.json).")
    parser.add_argument("--limit", type=int, default=200, help="Number of entries to pull (default: 100).")
    args = parser.parse_args()

    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
    if not project_id:
        print("ERROR: GOOGLE_CLOUD_PROJECT environment variable is not set.")
        print("  export GOOGLE_CLOUD_PROJECT=your-project-id")
        sys.exit(1)

    print(f"Pulling last {args.limit} log entries from project={project_id} ...")
    if args.filter:
        print(f"  filter: {args.filter}")

    entries = pull_logs(project_id, args.filter, args.limit)

    with open(args.output, "w") as f:
        json.dump(entries, f, indent=2, default=str)

    print(f"Wrote {len(entries)} entries to {args.output}")


if __name__ == "__main__":
    main()