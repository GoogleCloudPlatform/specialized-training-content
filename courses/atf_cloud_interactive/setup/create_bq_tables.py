#!/usr/bin/env python3
"""Creates the cymbal_meet BigQuery dataset and all tables.

Usage:
    python create_bq_tables.py

Requires $PROJECT_ID env var or active gcloud config.
Idempotent — safe to re-run.
"""

import os
import subprocess

from google.cloud import bigquery

DATASET_ID = "cymbal_meet"
LOCATION = "US"


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


TABLE_SCHEMAS: dict[str, list[bigquery.SchemaField]] = {
    "customers": [
        bigquery.SchemaField("customer_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("company_name", "STRING"),
        bigquery.SchemaField("segment", "STRING"),
        bigquery.SchemaField("licensed_users", "INT64"),
        bigquery.SchemaField("conference_rooms", "INT64"),
        bigquery.SchemaField("annual_contract_value", "FLOAT64"),
        bigquery.SchemaField("contract_start_date", "DATE"),
        bigquery.SchemaField("csm_name", "STRING"),
        bigquery.SchemaField("interactions", "RECORD", mode="REPEATED", fields=[
            bigquery.SchemaField("interaction_date", "DATE"),
            bigquery.SchemaField("type", "STRING"),
            bigquery.SchemaField("contact_name", "STRING"),
            bigquery.SchemaField("note", "STRING"),
        ]),
    ],
    "logins": [
        bigquery.SchemaField("login_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("customer_id", "STRING"),
        bigquery.SchemaField("user_email", "STRING"),
        bigquery.SchemaField("login_timestamp", "TIMESTAMP"),
        bigquery.SchemaField("platform", "STRING"),
    ],
    "calendar_events": [
        bigquery.SchemaField("event_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("customer_id", "STRING"),
        bigquery.SchemaField("organizer_email", "STRING"),
        bigquery.SchemaField("event_date", "DATE"),
        bigquery.SchemaField("start_time", "TIMESTAMP"),
        bigquery.SchemaField("end_time", "TIMESTAMP"),
        bigquery.SchemaField("invited_count", "INT64"),
        bigquery.SchemaField("cal_platform", "STRING"),
    ],
    "device_telemetry": [
        bigquery.SchemaField("telemetry_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("customer_id", "STRING"),
        bigquery.SchemaField("device_id", "STRING"),
        bigquery.SchemaField("room_name", "STRING"),
        bigquery.SchemaField("timestamp", "TIMESTAMP"),
        bigquery.SchemaField("cpu_usage_pct", "FLOAT64"),
        bigquery.SchemaField("memory_usage_pct", "FLOAT64"),
        bigquery.SchemaField("network_latency_ms", "FLOAT64"),
        bigquery.SchemaField("packet_loss_pct", "FLOAT64"),
        bigquery.SchemaField("video_quality_score", "FLOAT64"),
    ],
    "calls": [
        bigquery.SchemaField("call_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("customer_id", "STRING"),
        bigquery.SchemaField("initiator_email", "STRING"),
        bigquery.SchemaField("start_timestamp", "TIMESTAMP"),
        bigquery.SchemaField("duration_minutes", "INT64"),
        bigquery.SchemaField("participant_count", "INT64"),
        bigquery.SchemaField("call_type", "STRING"),
        bigquery.SchemaField("avg_quality_score", "FLOAT64"),
        bigquery.SchemaField("drop_count", "INT64"),
    ],
}


def main():
    project_id = get_project_id()
    client = bigquery.Client(project=project_id)
    dataset_ref = f"{project_id}.{DATASET_ID}"

    # Create dataset (idempotent)
    dataset = bigquery.Dataset(dataset_ref)
    dataset.location = LOCATION
    dataset = client.create_dataset(dataset, exists_ok=True)
    print(f"Dataset {dataset_ref} ready (location={dataset.location})")

    # Create tables (idempotent)
    for table_name, schema in TABLE_SCHEMAS.items():
        table_id = f"{dataset_ref}.{table_name}"
        table = bigquery.Table(table_id, schema=schema)
        table = client.create_table(table, exists_ok=True)
        print(f"  Table {table_name} ready ({len(schema)} columns)")

    print("\nAll tables created. Run generate_data.py next to load synthetic data.")


if __name__ == "__main__":
    main()
