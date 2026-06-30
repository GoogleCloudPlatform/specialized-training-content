# Lab Notes App — Config Connector with GKE (CCL000)

A small Flask web app that gives the student a single place to record the values
the lab explicitly asks them to note — the GKE cluster name, location, and mode
from Task 1.1, step 3 ("Record these in your notes").

The home page shows every field with a placeholder when empty. Click **Edit** on a
section to open a data-entry modal; **Save** stores the values and updates the page.

## What's here

| File                   | Purpose                                              |
| ---------------------- | ---------------------------------------------------- |
| `app.py`               | Flask app: serves the page and the note catalog      |
| `templates/index.html` | Single-page UI with the edit modal + localStorage    |
| `requirements.txt`     | Flask + gunicorn                                     |
| `Dockerfile`           | Container build for Cloud Run                        |
| `.dockerignore`        | Keeps the build context lean                         |
| `build-push.sh`        | Build the amd64 image and push to Artifact Registry  |

The app is **stateless**: notes are stored in the browser's `localStorage`, not on
the server. The Flask app only serves the page and the field catalog — it never
holds note data. This makes notes durable for the entire lab session regardless of
how Cloud Run scales (0..N instances, recycles, scale-to-zero): there is nothing on
the server to lose. The trade-off is that notes are tied to the student's browser —
they persist across reloads and for the whole session, but won't follow the student
to a different browser, an incognito window, or a cleared-data state.

## Run locally

```bash
pip install -r requirements.txt
python app.py
# open http://localhost:8080
```

While iterating on the page, set `FLASK_DEBUG=1` so Flask auto-reloads on code
and template edits (otherwise templates are cached and you must restart to see
changes):

```bash
FLASK_DEBUG=1 python app.py
```

## Deploy to Cloud Run

Deployment is two steps: build/push the image (manual, out-of-band), then deploy it
with Terraform during lab setup.

**1. Build and push the image** to Artifact Registry. The app runs amd64 on Cloud
Run, so the script cross-builds from Apple Silicon and pushes:

```bash
./build-push.sh
```

Override the target registry via env vars if needed (defaults shown):

```bash
AR_PROJECT=jwd-gcp-demos AR_REPO=specialized-training IMAGE_NAME=notes-app ./build-push.sh
```

**2. Deploy via Terraform.** The lab's `tf_project0/notes-app.tf` deploys this
prebuilt image to Cloud Run in the host project (project 0) using the foundation's
`cloud_run` module, with public (`allUsers` → `run.invoker`) access. The service
URL is surfaced as the `notes_app_url` Terraform output.

Because the app is stateless (see above), Cloud Run can scale freely — notes live in
the student's browser and survive the full lab session regardless of instances.
