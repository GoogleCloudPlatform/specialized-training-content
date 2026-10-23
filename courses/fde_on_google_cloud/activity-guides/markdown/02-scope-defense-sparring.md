# Activity 2: Scope Defense Sparring

**Absorb, defer, or route?** · Forward Deployed Engineering on Google Cloud · Team activity

| Total time | Your work time | Team size | Your team produces |
|---|---|---|---|
| 13 minutes | 8 minutes | 3–4 people, sparring in pairs | A call on each request, on the class worksheet |

## The situation

Cymbal Logistics is in **Week 3 of an 8-week sprint**. The Week 3 demo went well: the agent handles order status, tracking, and damaged-parcel claims.

Then Cymbal's executive sponsor says:

> "This is fantastic. Our CEO wants this agent negotiating **ocean freight contracts by voice** in time for investor day, three weeks from now. And our UI team is behind, so we need your engineers to **build the React screens** for our customer portal."

You need to protect the sprint without damaging the relationship.

## Your task

Spar in **pairs**. One person plays the **Cymbal sponsor** and the other plays the **FDE lead**. Swap after Round 1. In a team of 3, the third person observes with the scorecard and takes the FDE lead role in Round 2.

The FDE lead uses the three-step pushback:

1. **Acknowledge.** Say why the idea has real value to Cymbal.
2. **Quantify.** Use the fact card to name the cost to this sprint.
3. **Re-anchor and redirect.** Point to SCOPE.md, then say where the request goes: absorb it with a written trade-off, defer it to the Sprint 2 backlog, or route it to another team.

## How to run it

| Clock | Step |
|---|---|
| 0:00 | Form pairs, pick a **Scribe** and a **Reporter**, and read the fact card and SCOPE.md (1 minute) |
| 1:00 | **Round 1** (3 minutes): the sponsor asks for voice negotiation and the React screens |
| 4:00 | **Swap roles. Round 2** (3 minutes): the new sponsor adds the EDI request and pushes back on any deferral |
| 7:00 | As a team, agree on your call for each request; the Scribe records it on the class worksheet (1 minute) |
| 8:00 | Stop |

## Fact card (illustrative estimates)

**Squad:** a tech lead, 2 FDE builders, and a delivery lead, paired with 3 Cymbal developers. Build and hill climbing run through Week 6, and the 90% launch gate must be met before Weeks 7–8 (readiness and handover).

| Request | Estimate | What it touches |
|---|---|---|
| Voice negotiation of ocean freight contracts | About 6 weeks | New telephony integration, a new domain, an eval set rebuilt from zero |
| React portal screens | About 16 engineer-days | Frontend work only; nothing to do with the agent |
| Support the EDI carrier status format (Round 2 only) | About 4 engineer-days, plus new eval cases | The tracking tool the agent already uses |

## SCOPE.md excerpt

```markdown
# SCOPE.md: Cymbal Order and Shipment Support Agent (Sprint 1)

## In scope
- Chat agent for order status, shipment tracking, reroutes, and damaged-parcel claims
- Instant refunds up to $500; larger claims escalate to a human
- Tracking, reroute, and claims APIs called as tools from ADK

## Out of scope
- Voice and telephony channels
- Frontend or UI development (Cymbal's web team owns the portal)
- Ocean freight and contract negotiation
- Manual data cleanup or ETL of legacy systems

## Exit criteria
- At least 90% pass rate on the eval set
- Cymbal's team ships to production and runs a game day unassisted
```

## Role cards

**Cymbal sponsor.** You are excited, under pressure from your CEO, and used to getting a yes. Lines to use:

- "The CEO has already mentioned this to the board."
- "You're Google. Can't you add more engineers?"
- "If you can't do voice, what are we paying for?"
- (Round 2) "The EDI change is tiny. Just squeeze it in."

**FDE lead.** Never say "that's not my job." Every answer ends by saying who will handle the request and what happens next.

## Observer scorecard

| Did the FDE lead... | Yes / No |
|---|---|
| Acknowledge the value before saying no? | |
| Use a number from the fact card? | |
| Point to a line in SCOPE.md? | |
| Instead of stopping at "no," say who will handle the request and when? (For example: the Sprint 2 backlog, a telephony specialist team, Cymbal's web team, or an implementation partner) | |
| Get a written trade-off before absorbing anything? | |

## Team worksheet

Your **Scribe** fills in your team's rows on the **A2 Scope Defense** tab of the **class worksheet**. The instructor posts the link in chat at the start of class. If you don't have it, write in this table.

| Request | Your call: absorb, defer, or route | Who handles it, and what the sponsor agreed to |
|---|---|---|
| Voice negotiation of ocean freight | | |
| React portal screens | | |
| EDI carrier status format | | |

## Report-out (2 minutes for the whole class)

When the instructor calls time, each Reporter answers **the item for their team number** in one or two sentences:

| Team | Report this |
|---|---|
| 1 | The strongest sentence your FDE lead used on the voice request |
| 2 | Where the React screens should go, and why |
| 3 | Did you absorb the EDI request? If so, what did the sponsor agree to give up? |
| 4 | The sponsor line that was hardest to answer, and how you answered it |
| 5 | Which SCOPE.md line or qualification criterion did the most work |
| 6+ | Start again at item 1 |

## Reminder from the slides

- **Operating modes:** Build (co-develop), Consult (advise), Triage (route to the right team).
- **Intake routing:** unvalidated ideas go to pre-sales discovery. Staff augmentation goes to PSO or an implementation partner.
- **SCOPE.md** lives in the Git root, so people and AI coding tools work from the same boundaries.
