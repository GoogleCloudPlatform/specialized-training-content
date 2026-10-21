# Activity 1: Unblock the Launch

**Who owns the fix?** · Forward Deployed Engineering on Google Cloud · Team activity

| Total time | Your work time | Team size | Your team produces |
|---|---|---|---|
| 13 minutes | 8 minutes | 3–4 people | One completed worksheet row |

## The situation

Cymbal Logistics is in **Week 6 of an 8-week sprint**. Production launch is two weeks away.

- The Order and Shipment Support Agent passes **68%** of its eval cases. The launch gate is **90%**.
- Cymbal's leadership says the model is unreliable.
- The account team says Cymbal's data is bad.
- Nobody has looked at the evidence.

You are the FDE squad. Your job is to replace blame with a diagnosis.

## Your task

Your team gets **one exhibit**, based on your team number:

| Team | Exhibit |
|---|---|
| 1 | Exhibit 1: The lost parcel |
| 2 | Exhibit 2: The early refund |
| 3 | Exhibit 3: The overnight drop |
| 4 | Exhibit 4: The $600 eval cases |
| 5 | Exhibit 5: The friendlier prompt |
| 6+ | Start again at Exhibit 1 |

Read your exhibit, then your Scribe fills in **your exhibit's row** on the **A1 Unblock the Launch** tab of the **class worksheet**. The instructor posts the class worksheet link in chat at the start of class. If you don't have it, write in the worksheet table in this guide.

## How to run it

| Clock | Step |
|---|---|
| 0:00 | Pick roles (30 seconds): **Timekeeper**, **Scribe**, **Reporter** |
| 0:30 | Read your exhibit on your own (2 minutes) |
| 2:30 | Discuss; the Scribe fills in your row on the class worksheet (4 minutes) |
| 6:30 | Reporter rehearses the one-sentence report-out (1 minute) |
| 7:30 | Buffer; stop at 8:00 |

## Worksheet

The **A1 Unblock the Launch** tab of the class worksheet has one row per exhibit, with the columns below. Fill in only your exhibit's row.

| Column | What to write |
|---|---|
| Symptom | What a user or the eval suite saw |
| Failure mode | One of: Model and Input Drift · Instruction Breakdown · Tool-Calling and Integration Failure · Hallucination · Not a model failure |
| Root cause | The real cause, in one line |
| Fix | Prompt change, tool change, callback, eval set change, process change, or escalation |
| Owner | FDE squad · Cymbal developers · Cymbal business SME · Platform team (or a pair of these) |

| Exhibit | Symptom | Failure mode | Root cause | Fix | Owner |
|---|---|---|---|---|---|
| 1. The lost parcel | | | | | |
| 2. The early refund | | | | | |
| 3. The overnight drop | | | | | |
| 4. The $600 eval cases | | | | | |
| 5. The friendlier prompt | | | | | |

## The exhibits

### Exhibit 1: The lost parcel

A customer asked about parcel **CYM-4471**. Excerpt from the request trace:

```text
span  tool_call  verify_tracking_status(tracking_id="CYM-4471")
      upstream   GET /v2/status/CYM-4471 -> 504 Gateway Timeout (8,003 ms)
      result     ""                       # empty string returned to the model
span  model_response
      "I'm sorry, parcel CYM-4471 appears to be lost in transit.
       I've opened a lost-parcel claim for you."
```

Fact: the parcel was delivered on time. The tracking API was slow during a nightly batch job.

### Exhibit 2: The early refund

Excerpt from a 9-turn session log. The prompt's `<constraints>` block says: *"Never call issue_instant_refund until status is DELIVERED."*

```text
turn 1   user   "Hi, my parcel arrived damaged"
...
turn 6   user   "It's CYM-2290, the box was crushed, I need a refund"
turn 7   tool   issue_instant_refund(tracking_id="CYM-2290", amount=180)
turn 8   tool   verify_tracking_status(tracking_id="CYM-2290") -> IN_TRANSIT
turn 9   agent  "I've issued a $180.00 refund."
```

Fact: in short sessions this never happens. In sessions longer than 6 turns, it happens in 7% of cases.

### Exhibit 3: The overnight drop

```text
Eval pass rate
  Fri   77%
  Mon   77%
  Tue   68%     # 41 cases newly failing

git log since Friday:   no commits to prompts, tools, or config
Model setting:          auto-updating model alias
Platform release notes: new model version rolled out Monday night
```

Example of a newly failing case. The prompt says *"Ask only one clarifying question at a time."*

```text
Before:  "What's your tracking number?"
After:   "What's your tracking number, and can you upload photos of the damage?"
```

### Exhibit 4: The $600 eval cases

Breakdown of the 96 failing eval cases:

| Category | Failing cases | Notes |
|---|---|---|
| Expect `issue_instant_refund` for claims of $520–$650 | 40 | Agent escalates instead of refunding |
| Tracking and reroute flows | 31 | Mixed causes |
| Other | 25 | Mixed causes |

Facts:

- Cymbal's refund policy caps instant refunds at **$500**. ADR-004 enforces the cap in the Python tool.
- Cymbal's operations team wrote these eval cases from historical tickets, when the cap was **$750**.

### Exhibit 5: The friendlier prompt

```text
commit 9f3e1c2   author: cymbal-dev   branch: main (direct push, no PR)
message: "Make the tone friendlier"

- <format>Short, plain sentences. No markdown or JSON.</format>
+ <format>Be warm and friendly, and lay out details clearly.</format>
```

Facts:

- Since this commit, 22% of replies contain markdown tables. The chat widget shows them as raw `|` characters.
- Branch protection is off, and the eval suite runs nightly, not on each pull request.

## Report-out (2 minutes for the whole class)

When the instructor calls time, each Reporter says **one sentence** in team order, about 20 seconds each:

> "Exhibit **N** is a **[failure mode]** problem. The fix is **[fix]**, and **[owner]** owns it."

No slides and no role-play. The instructor may ask one follow-up question.

## Reminder from the slides

- **Systematic debugging:** read the trace, reproduce the failure as a test, fix the cause.
- **Frontier workarounds:** reproduce in a minimal test, unblock with a wrapper or callback, send the repro upstream, remove the wrapper when the fix ships.
- **Enforce hard rules in code**, not in longer prompts.
