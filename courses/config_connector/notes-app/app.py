"""Lab notes app for CCL000 — Deploying and using Config Connector with GKE.

A single-page Flask app that gives the student one place to record the values
the lab asks them to note (the GKE cluster's name, location, and mode).

The app is intentionally STATELESS: notes are stored in the browser's
localStorage, not on the server. This keeps the data durable for the full lab
session regardless of how Cloud Run scales (0..N instances, recycles, etc.) —
the server never holds note data, so there is nothing to lose when an instance
is replaced. The server only serves the page and the field catalog.
"""

import os

from flask import Flask, render_template

app = Flask(__name__)


# The full catalog of things the lab asks the student to note, grouped into the
# sections the student encounters them in. Each field has a stable `key` (used
# for storage), a `label`, optional `help` text, and a `placeholder` shown when
# the student hasn't filled it in yet. `type` controls the input widget.
SECTIONS = [
    {
        "id": "cluster",
        "title": "Task 1.1 — The GKE cluster",
        "subtitle": "Step 3: \"Note the cluster's name and location... Record these "
        "in your notes\" — you'll refer back to the single cluster that drives "
        "everything.",
        "fields": [
            {
                "key": "cluster_name",
                "label": "Cluster name",
                "help": "From Kubernetes Engine > Clusters.",
                "placeholder": "e.g. config-clustermode-standard-0",
            },
            {
                "key": "cluster_location",
                "label": "Cluster location",
                "help": "The region/zone shown in the clusters list.",
                "placeholder": "e.g. us-central1",
            },
            {
                "key": "cluster_mode",
                "label": "Mode",
                "help": "Cluster basics > Mode.",
                "placeholder": "Standard",
            },
        ],
    },
    {
        "id": "portal_state",
        "title": "Task 1.4 — Portal object state (while SQL instance is being created)",
        "subtitle": "Step 23: \"In your note-taking app, record the READY and STATUS "
        "values you see right now for each of these objects.\" Capturing this snapshot "
        "lets you see how the states differ across objects at the same moment.",
        # Table layout: one row per object, two values each (READY, STATUS). Each
        # row owns two storage keys, "<key>_ready" and "<key>_status".
        "layout": "table",
        # Dropdown choices for the two columns. The blank "—" option (added by the
        # select builder) is the "not applicable / not yet reached" value.
        "ready_options": ["True", "False"],
        "status_options": ["UpToDate", "DependencyNotReady", "Updating", "UpdateFailed"],
        "rows": [
            {"key": "portal_sa_portal_app", "kind": "IAMServiceAccount", "name": "portal-app"},
            {"key": "portal_ipm_cloudsql_client", "kind": "IAMPolicyMember", "name": "portal-app-cloudsql-client"},
            {"key": "portal_ipm_cloudsql_instanceuser", "kind": "IAMPolicyMember", "name": "portal-app-cloudsql-instanceuser"},
            {"key": "portal_ipm_storage_objectadmin", "kind": "IAMPolicyMember", "name": "portal-app-storage-objectadmin"},
            {"key": "portal_bucket_uploads", "kind": "StorageBucket", "name": "portal-uploads"},
            {"key": "portal_sqlinstance_db", "kind": "SQLInstance", "name": "portal-db"},
            {"key": "portal_sqldatabase_portal", "kind": "SQLDatabase", "name": "portal"},
            {"key": "portal_sqluser_portal_app", "kind": "SQLUser", "name": "portal-app"},
        ],
    },
    {
        "id": "day2_proof",
        "title": "Task 1.8 — Day-2 in-place proof",
        "subtitle": "Step 46: \"In your note-taking app, record the uid and "
        "creationTimestamp for both objects.\" Capture this pre-update baseline before "
        "you apply the day-2 change.",
        "fields": [
            {
                "key": "day2_events_uid",
                "label": "events table — uid",
                "help": "metadata.uid of bigquerytable/events.",
                "placeholder": "e.g. 1a2b3c4d-...",
            },
            {
                "key": "day2_events_created",
                "label": "events table — creationTimestamp",
                "help": "metadata.creationTimestamp of bigquerytable/events.",
                "placeholder": "e.g. 2026-06-23T14:05:11Z",
            },
            {
                "key": "day2_bucket_uid",
                "label": "clickstream-raw bucket — uid",
                "help": "metadata.uid of storagebucket/clickstream-raw.",
                "placeholder": "e.g. 9z8y7x6w-...",
            },
            {
                "key": "day2_bucket_created",
                "label": "clickstream-raw bucket — creationTimestamp",
                "help": "metadata.creationTimestamp of storagebucket/clickstream-raw.",
                "placeholder": "e.g. 2026-06-23T14:06:02Z",
            },
        ],
    },
]


@app.route("/")
def index():
    # Notes live in the browser; the server just renders the field catalog.
    return render_template("index.html", sections=SECTIONS)


@app.route("/healthz")
def healthz():
    return "ok", 200


if __name__ == "__main__":
    # Cloud Run provides the port to listen on via $PORT (default 8080).
    port = int(os.environ.get("PORT", 8080))
    # For local dev, set FLASK_DEBUG=1 to auto-reload on code AND template edits
    # (otherwise Flask caches templates and you must restart to see changes).
    # On Cloud Run the app is served by gunicorn, so this block doesn't run.
    debug = os.environ.get("FLASK_DEBUG") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)
