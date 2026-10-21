# FDE on Google Cloud: Activity Guides

The four team discussion activities for Forward Deployed Engineering (FDE) on Google Cloud, and the site that serves them to a class.

## Discussion activities

Each activity runs 13 minutes in teams of 3–4 and follows the Cymbal Logistics case thread.

| # | Activity | Question it asks |
|---|---|---|
| 1 | Pilot Autopsy | Who owns the fix? |
| 2 | Scope Defense Sparring | Absorb, defer, or route? |
| 3 | Trick Question to Eval Case | How do you turn a scary anecdote into a permanent test? |
| 4 | Escalation Triage Under Load | Defect, or working as designed? |

The [Instructor Activity Guide](markdown/instructor-activity-guide.md) covers class setup, the shared 13-minute run sheet, and an answer key with takeaways for each activity. It is for the instructor only.

## Layout

```text
markdown/   Source for each guide. Edit these.
html/       Generated pages. Don't edit by hand.
build/      md2html.py and template.html, which turn markdown/ into html/
server.py   Serves the home page and the guides
Dockerfile  Container image for Cloud Run (copies server.py and html/)
deploy.sh   Regenerates html/, then deploys to Cloud Run
```

Run every command below from this folder.

## Edit a guide

1. Edit the guide's file in `markdown/`.
2. Regenerate the HTML:

   ```bash
   python3 build/md2html.py markdown/*.md
   ```

3. Commit the Markdown and HTML changes together, so `html/` always matches `markdown/`.

`md2html.py` supports only the Markdown the guides use: headings, paragraphs, lists, tables, block quotes, and fenced code. The first table before any `##` heading renders as stat cards. Empty table cells render as editable cells that teams can fill in.

## Preview locally

Run:

```bash
python3 server.py
```

Then open `http://localhost:8080`. The instructor guide is at `/instructor-activity-guide`.

## Deploy

Run:

```bash
./deploy.sh your-project-id us-central1
```

The script regenerates `html/`, enables the required APIs, and deploys a public Cloud Run service named `fde-activity-guides`. The service scales to zero when idle. The script prints the class URL and the instructor URL.

For prerequisites, update steps, and cleanup, see "Setup 1: Deploy the guide site" in the [Instructor Activity Guide](markdown/instructor-activity-guide.md).

> **Note:** The instructor page isn't linked from the home page, but it isn't access controlled. Anyone with the URL can open it.
