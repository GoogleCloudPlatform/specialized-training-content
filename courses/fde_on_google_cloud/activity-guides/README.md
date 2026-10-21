# FDE on Google Cloud: Activity Guides

The four team activities for Forward Deployed Engineering (FDE) on Google Cloud, and the site that serves them to a class.

## Activities

Each activity runs 13 minutes in teams of 3–4 and follows the Cymbal Logistics case thread.

| # | Activity | Question it asks |
|---|---|---|
| 1 | Unblock the Launch | Who owns the fix? |
| 2 | Scope Defense Sparring | Absorb, defer, or route? |
| 3 | Trick Question to Eval Case | How do you turn a scary anecdote into a permanent test? |
| 4 | Escalation Triage Under Load | Defect, or working as designed? |

The [Instructor Activity Guide](markdown/instructor-activity-guide.md) covers class setup, the shared 13-minute run sheet, and an answer key with takeaways for each activity. It is for the instructor only.

## Class worksheet

Teams record their answers in a shared Google Sheet, one tab per activity. Before each class:

1. Open the [FDE Class Worksheet template](https://www.roi-links.com/fde-activities) and select **File > Make a copy**. The template is view-only.
2. Share your copy: **Share > General access > Anyone with the link > Editor**.
3. Create a short URL for your copy (for example, at tinyurl.com).
4. Post the short URL in the class chat for students.

For the tab layouts, see "Setup 2: Create the class worksheet" in the [Instructor Activity Guide](markdown/instructor-activity-guide.md).

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

`md2html.py` supports only the Markdown the guides use: headings, paragraphs, lists, tables, block quotes, fenced code, and `https://` links. The first table before any `##` heading renders as stat cards. Empty table cells render as editable cells that teams can fill in.

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

## Fallback: read the guides on GitHub

If you can't deploy the Cloud Run service, or students can't reach it, have students read the guides on GitHub instead. GitHub renders the Markdown in `markdown/` as readable pages, so no deploy is needed.

Post these four links in the class chat:

- [Activity 1: Unblock the Launch](https://github.com/GoogleCloudPlatform/specialized-training-content/blob/main/courses/fde_on_google_cloud/activity-guides/markdown/01-unblock-the-launch.md)
- [Activity 2: Scope Defense Sparring](https://github.com/GoogleCloudPlatform/specialized-training-content/blob/main/courses/fde_on_google_cloud/activity-guides/markdown/02-scope-defense-sparring.md)
- [Activity 3: Trick Question to Eval Case](https://github.com/GoogleCloudPlatform/specialized-training-content/blob/main/courses/fde_on_google_cloud/activity-guides/markdown/03-trick-question-to-eval-case.md)
- [Activity 4: Escalation Triage Under Load](https://github.com/GoogleCloudPlatform/specialized-training-content/blob/main/courses/fde_on_google_cloud/activity-guides/markdown/04-escalation-triage-under-load.md)

Keep these points in mind:

- **Link to the files, not the folder.** The Instructor Activity Guide and its answer keys are in the same `markdown/` folder.
- **Teams record answers on the class worksheet.** On GitHub, the worksheet tables in the guides are read-only, so teams can't fill them in.
- **Formatting is plainer.** The summary at the top of each guide shows as a regular table instead of cards. The content is the same.
- **The links point to the `main` branch.** They work only after these guides are merged to `main`.
