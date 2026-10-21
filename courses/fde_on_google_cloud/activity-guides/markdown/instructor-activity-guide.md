# Instructor Activity Guide

Forward Deployed Engineering on Google Cloud · For the instructor only; don't hand this to teams.

## Before class: setup checklist

Do these once; they serve all four activities.

1. **Deploy the guide site** to Cloud Run (Setup 1).
2. **Create the class worksheet** (Setup 2).
3. **Assign teams** of 3–4 in breakout rooms, and keep the same teams for all four activities (Setup 3).

## Setup 1: Deploy the guide site

One script publishes the guides as a small Cloud Run website. The home page links to the four team guides. This Instructor Activity Guide gets its own URL, which is not linked from the home page.

### What you need

- The `gcloud` CLI, signed in with `gcloud auth login`
- A Google Cloud project with billing enabled
- Permission to enable APIs and deploy to Cloud Run from source in that project (Owner or Editor is simplest)
- `git` and `python3` (both come with macOS and Linux; Cloud Shell has everything)

### Deploy

1. Clone the course repository and change into the guides folder:

```bash
git clone --depth 1 https://github.com/GoogleCloudPlatform/specialized-training-content.git
cd specialized-training-content/courses/fde_on_google_cloud/activity-guides
```

2. Run the script with your project ID. The region is optional and defaults to `us-central1`:

```bash
./deploy.sh your-project-id us-central1
```

3. Wait for the build. The first deploy takes about 3–5 minutes.
4. Copy the two URLs the script prints at the end:

```text
Share with the class:   https://fde-activity-guides-xxxx.a.run.app
Instructor guide:       https://fde-activity-guides-xxxx.a.run.app/instructor-activity-guide   (keep this private)
```

### Update after editing a guide

From the same `activity-guides` folder, run `git pull` to get the latest guides (or edit the `.md` files in `markdown/` yourself), then rerun the same command. The script regenerates the HTML in `html/` before deploying, and both URLs stay the same.

### Good to know

- **Public link:** anyone with the class URL can open the guides. If your organization's policy blocks public Cloud Run services, the deploy fails at the IAM step; use a project without that restriction, or ask your admin.
- **Instructor URL:** `/instructor-activity-guide` is not linked from the home page, but it is not password protected. Don't post it in the class chat.
- **Cost:** the service scales to zero when idle, so a class costs pennies.
- **Remove after class:** `gcloud run services delete fde-activity-guides --project your-project-id --region us-central1`
- **Preview locally:** run `python3 server.py`, then open `http://localhost:8080`. The instructor guide is at `/instructor-activity-guide`.
- **Fallback if Cloud Run isn't available:** if you can't deploy, or students can't reach the site, post GitHub links to the four team guides in `markdown/` instead. The README in `activity-guides/` lists the links. Link to the individual files, not the folder, because this guide is in the same folder. Teams record their answers on the class worksheet, because the tables on GitHub can't be edited.

## Setup 2: Create the class worksheet

Create **one class worksheet** (a Google Sheet) with one tab per activity, and set sharing to "anyone with the link can edit". During each activity, Scribes type on that activity's tab; during the report-out, you share your screen on the same tab, so the class sees every team's answers without anyone presenting.

| Tab | Layout | Copy the columns from |
|---|---|---|
| A1 Unblock the Launch | One row per exhibit (1–5); columns: Exhibit, Team, Symptom, Failure mode, Root cause, Fix, Owner. With 6+ teams, add a second row per exhibit | The guide's **Worksheet** section |
| A2 Scope Defense | One block of 3 rows per team (voice, React, EDI); columns: Team, Request, Call, Who handles it / what the sponsor agreed to | The guide's **Team worksheet** section |
| A3 Eval Case | One row per team; columns: Team, Eval case (expected tool_uses and final response), Judge criterion 1, 2, 3, Fix chosen, Proof | The guide's **Your task** section |
| A4 Escalation Triage | One row per team; columns: Team, Evidence (A/B), Q1–Q5 | The guide's **Your task: five short answers** table |

Prefill the Team column (and Activity 4's Evidence column: odd = A, even = B) so Scribes find their row instantly. In person without laptops, print the guides; each has the same worksheet table to write on.

## Setup 3: Assign teams

- Pre-assign breakout rooms (or table groups) of 3–4 people, and number the teams. Team numbers drive exhibit assignments and report-out items.
- With more than 5 teams, the report-out items wrap around. With fewer, skip the higher-numbered items.

## At the start of class

- Post the guide site's home page link in chat. Teams open each guide from there. Printed guides also work; each one is self-contained.
- Post the class worksheet link in chat, and pin both links if your platform allows.

---

## Every activity uses the same 13-minute run sheet

| Clock | Block | Instructor does |
|---|---|---|
| 0:00–1:30 | Frame | Read the scenario slide; tell teams which guide to open from the guide site and which class worksheet tab to use |
| 1:30–2:30 | Spin-up | Open the pre-assigned breakout rooms (or form teams in the room) |
| 2:30–10:30 | Work | Teams work for 8 minutes; send a 2-minute warning at 8:30 |
| 10:30–11:00 | Regroup | Close the rooms |
| 11:00–13:00 | Report-out | Share your screen on the activity's tab; each team gives one item by team number (about 20 seconds each), then you say the takeaway line |

That leaves 2 minutes of buffer under the 15-minute cap.

---

## Activity 1: Unblock the Launch

**Answer key**

| Exhibit | Failure mode | Root cause | Fix | Owner |
|---|---|---|---|---|
| 1. Lost parcel | Tool-calling & integration failure that surfaces as a hallucination | The tool returns an empty string on a 504, and the model fills the gap | Tool wrapper with a short timeout that returns a typed error (for example, `UPSTREAM_TIMEOUT`); fall back to a human handoff | FDE squad, co-built with Cymbal developers |
| 2. Early refund | Instruction breakdown | A rule held only in the prompt erodes in long sessions | `before_tool_callback` that blocks `issue_instant_refund` unless the status is **DELIVERED**; add an eval case for it | FDE squad |
| 3. Overnight drop | Model & input drift | An auto-updating model alias picked up a new version | Pin the model version; reproduce in a minimal test; clarify the prompt or add a callback; send the repro upstream; remove the workaround when fixed | FDE triages; platform team fixes the model behavior |
| 4. $600 eval cases | Not a model failure | The eval cases encode an old $750 policy; the agent is correct | Correct the eval set; the business SME signs off on the expected outcomes | Cymbal business SME (owns business truth), with FDE help |
| 5. Friendlier prompt | Instruction breakdown caused by a process gap | Direct push to main, with no review and no eval gate | Branch protection; run the eval suite on every PR | Cymbal developers and FDE squad jointly |

**Listen for:** teams that stop at "the model hallucinated" (push on the cause), and Exhibit 4 teams that find the "bad data" claim was partly true, just not in the way anyone meant it.

**Takeaway line:** "'The model hallucinated' is a symptom. Find the cause in the trace, and name who owns each fix, including owners outside the squad."

---

## Activity 2: Scope Defense Sparring

**Answer key**

| Request | Call | Why |
|---|---|---|
| Voice negotiation of ocean freight | Defer to the Sprint 2 backlog; route the telephony integration to specialists (Triage) | About 6 weeks of new channel, domain, and eval work; out of scope; jeopardizes the 90% gate |
| React portal screens | Route to Cymbal's web team, or to PSO or an implementation partner | Staff augmentation; not agent work; listed as out of scope |
| EDI carrier status format | Can be absorbed, with a written trade-off the sponsor signs | Small, inside the existing tracking tool, improves the agent; still needs new eval cases |

**Listen for:** a flat "no" that doesn't say who will handle the request instead (the most common miss), and absorbing EDI without asking for anything in return.

**Takeaway line:** "'Not in this sprint' is never the whole answer. Name the cost, then say where the request goes."

---

## Activity 3: Trick Question to Eval Case

**Answer key**

- **Expected `tool_uses`:** `verify_tracking_status`, then `transfer_to_human`. `issue_instant_refund` must never appear.
- **Final response:** scored by an LLM judge, not matched word for word. The wording can vary; the behavior can't.
- **Strong judge criteria:** fails if any coverage or payout is stated or implied; fails if a refund tool is called; passes only if the case is handed to a human and the response says the risk team will follow up; fails if the response cites a policy that doesn't exist.
- **Fix:** **B (callback)** is the best primary fix, because a hard rule belongs in code. Pair it with a one-line **A** so the wording is good. **C (sub-agent)** is overkill for one rule; it becomes right if hazmat rules grow, which is the "too many rules for one prompt" trigger.
- **Proof:** confirm the new case fails before the fix and passes after; rerun all 300 eval cases (the merge gate); add user simulations with hazmat scenarios and save any failures as new cases.
- **Reply to the CRO:** thank them for the catch, give the denominator (91% across 300 cases), say this failure is now a permanent test, and give a date to show the rerun results.

**Optional 30-second aside (from option 3C):** fixing this by adding pages of hazmat rules to the main prompt often fixes hazmat and breaks other flows, while raising latency and token cost. That is why the fix goes into a callback.

**Takeaway line:** "Thank the CRO for a new eval case. Answer with the denominator and the flywheel, not with a defense."

---

## Activity 4: Escalation Triage Under Load

**Answer key**

| Question | Evidence A (odd teams) | Evidence B (even teams) |
|---|---|---|
| 1. Defect or working as designed? | Working as designed. 429s appear only in seconds above purchased capacity; the 59% average hides the bursts | Likely a defect. 429s appear at 45–68 requests/second, well under capacity, and other teams see the same pattern |
| 2. Before the canary | Spread out the batch job; add retries with exponential backoff and jitter | Retries with backoff and jitter; an overflow or fallback path; an alert on the 429 rate |
| 3. Priority | No product defect ticket; the fix is on the customer side | **P2**: it blocks launch, but a client-side workaround is deployed |
| 4. Where it goes | Customer runbook (batch schedule); Field Gotchas entry: "average utilization hides per-second bursts" | Product issue tracker (clean escalation); Field Gotchas entry for the workaround; remove the workaround when the fix ships |
| 5. Written output | Reply: what changed, why, and the retest time | Escalation with no customer name, no deal size, no conversation content; repro = a fixed-rate load script below capacity that logs 429 timestamps and trace IDs |

**Close with the go/no-go (one question to the room):** "Do we launch Wednesday?" Answer: yes, if a rerun of the load test with the workaround shows zero failures users can see and the alert is live. Otherwise, delay.

**Takeaway line:** "Before you escalate, prove it isn't working as designed. If it's a defect, ship the workaround, then send a clean, scrubbed repro at the right priority."

**Before class:** check Evidence A's explanation against the current Provisioned Throughput documentation, especially how purchased capacity is measured over time and what happens to traffic above it, and adjust the wording if needed.
