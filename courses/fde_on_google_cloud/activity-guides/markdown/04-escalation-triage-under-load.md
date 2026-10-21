# Discussion 4: Escalation Triage Under Load

**Defect, or working as designed?** · Forward Deployed Engineering on Google Cloud · Team activity

| Total time | Your work time | Team size | Your team produces |
|---|---|---|---|
| 13 minutes | 8 minutes | 3–4 people | Five short answers on the class worksheet |

## The situation

It is **48 hours before Cymbal's canary launch**, which will send 10% of live traffic to the agent.

The final load test shows:

- **3% of model calls are rejected** with `429 RESOURCE_EXHAUSTED`.
- Usage averages **60% of the capacity Cymbal purchased**.
- The client has **no retries configured**. Every 429 reaches the user as "Sorry, something went wrong."

A Cymbal developer posts this in the shared chat:

> "URGENT!!! Gemini keeps throttling Cymbal Logistics even though we pay $1.2M a year for capacity. Full logs attached (cymbal_prod_logs.zip, 48 MB, includes customer conversations). Launch is Wednesday. FIX IT ASAP!!!"

## Your evidence

Teams look at different evidence:

| Team number | Your evidence |
|---|---|
| Odd (1, 3, 5, ...) | **Evidence A** |
| Even (2, 4, 6, ...) | **Evidence B** |

Both evidence sets are simplified for the exercise: purchased capacity is shown as **100 requests per second**.

### Evidence A

One minute of the load test, one row per second (the pattern repeats every minute):

| Second | Requests sent | 429 errors |
|---|---|---|
| :00 | 150 | 50 |
| :01 | 140 | 40 |
| :02 | 118 | 18 |
| :03 | 97 | 0 |
| :04–:59 | 45–70 each second | 0 |
| **Whole minute** | **about 3,550 (59% of capacity)** | **108 (3.0%)** |

The batch job that refreshes tracking for all open claims starts at **:00** of every minute.

### Evidence B

One minute of the load test, one row per second (other minutes look similar):

| Second | Requests sent | 429 errors |
|---|---|---|
| :00 | 58 | 3 |
| :01 | 61 | 0 |
| :02 | 49 | 4 |
| :03 | 66 | 2 |
| :04 | 52 | 0 |
| :05 | 47 | 5 |
| :06–:59 | 45–68 each second | 0–5 each second |
| **Whole minute** | **about 3,400 (57% of capacity)** | **102 (3.0%)** |

Traffic is steady, and the batch job has already been moved off the minute boundary. Two other partner teams in the Field Gotchas catalog report the same pattern this week, on the same model and region.

## Your task: five short answers

Your Scribe writes the answers in your team's row on the **D4 Escalation Triage** tab of the **class worksheet**. The instructor posts the link in chat at the start of class. If you don't have it, write in the table below.

| # | Question | Your answer |
|---|---|---|
| 1 | Is this a platform defect or the platform working as designed? Which line of your evidence decided it? | |
| 2 | What client-side change ships **before** the canary? | |
| 3 | What priority does this get? Use the decision tree below. | |
| 4 | Where does each learning go: the customer repo, the Field Gotchas catalog, or the product issue tracker? | |
| 5 | **Evidence A:** write a 2-line reply to the Cymbal developer. **Evidence B:** rewrite the chat post as a clean escalation (template below). | |

## How to run it

| Clock | Step |
|---|---|
| 0:00 | Pick roles (30 seconds): **Timekeeper**, **Scribe**, **Reporter** |
| 0:30 | Read the situation and your evidence (1.5 minutes) |
| 2:00 | Answer questions 1–4 (3.5 minutes) |
| 5:30 | Answer question 5 (2 minutes) |
| 7:30 | Reporter checks the report-out item for your team number (30 seconds) |
| 8:00 | Stop |

## Priority decision tree

```text
Does it block launch?
├── No  -> File P2/P3 by impact
└── Yes -> Can the FDE deploy a client-side workaround today?
           ├── Yes -> Deploy the workaround and file P2 (customer unblocked)
           └── No  -> File P1 launch blocker (triggers core engineering triage)

P0 is reserved for an active production outage or a security or data-loss incident.
```

## Clean escalation template

Follow the four-step protocol: **scrub** PII and secrets, build a **minimal repro**, **calibrate priority**, and **route** to the designated tracker with trace IDs.

```text
Title:      [component] short description of the behavior
Impact:     failure rate %, scale, launch date, workaround status
Repro:      standalone script or command anyone can run (describe it)
Priority:   P0 / P1 / P2 / P3, and why
Evidence:   trace IDs, timestamps, region, model version
```

Leave out customer names, deal sizes, and conversation content.

## Report-out (2 minutes for the whole class)

When the instructor calls time, each Reporter answers **the item for their team number** in one or two sentences:

| Team | Evidence | Report this |
|---|---|---|
| 1 | A | Defect or working as designed, and the line of evidence that decided it |
| 2 | B | Defect or working as designed, and the line of evidence that decided it |
| 3 | A | What changes on Cymbal's side before the canary |
| 4 | B | Your clean escalation's title and priority |
| 5 | A | What goes in the Field Gotchas catalog |
| 6+ | | Start again at item 1 |

## Reminder from the slides

- **Clean escalations:** a sanitized repro plus the version, workaround status, and a calibrated priority gets triaged. A 50 MB raw log dump stalls.
- **3-tier knowledge routing:** customer repo (runbooks, ADRs), Field Gotchas catalog (cross-customer limits and workarounds), product issue tracker (platform defects).
- **Upstream leverage:** a fix for one customer is 1x, a practice-wide template is 10x, a platform fix is 1,000x.
