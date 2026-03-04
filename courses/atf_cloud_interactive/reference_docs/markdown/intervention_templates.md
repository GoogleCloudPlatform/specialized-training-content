# Cymbal Meet — Intervention Templates

## Standardized Templates for Customer Engagement Interventions

Version 1.4 | Last Updated: January 2026 | Document ID: CM-INT-TPL-001

---

## 1. Overview

When Cymbal Meet identifies a customer experiencing engagement challenges, the Customer Success team creates a tailored intervention document. This document serves as both an internal action plan and a customer-facing deliverable.

This guide provides template structures for the most common intervention types. Each template includes required sections, guidance on what to include, and example content. Templates should be customized with the customer's specific data, context, and recommended actions.

## 2. Intervention Types

| Type | When to Use | Typical Trigger |
| --- | --- | --- |
| Adoption Plan | Users aren't logging in or using core features | Login rate <50%, low meeting adoption |
| Technical Remediation Plan | Infrastructure or configuration issues impacting quality | Call quality <3.5, device issues, network problems |
| Executive Briefing | Strategic engagement with customer leadership needed | Declining usage, renewal risk, executive sponsor departure |
| Re-Engagement Campaign | Usage was healthy but is declining | Week-over-week usage decline >20% for 3+ weeks |
| Onboarding Acceleration Plan | New deployment or acquired workforce falling behind schedule | Onboarding milestones missed (see Admin Guide) |

## 3. Template: Adoption Plan

### Use When
- Login rate is below 50% of licensed users
- Meeting adoption is significantly below segment benchmarks
- Feature adoption is limited (e.g., only scheduled meetings, no ad-hoc usage)
- Calendar integration is underutilized despite healthy logins

### Document Structure

#### Section 1: Executive Summary

Provide a 2-3 sentence overview of the customer's adoption challenge, the impact on their investment, and the goal of this intervention.

**Example:**
> Pinnacle Financial Group currently has a 25% active login rate across 1,800 licensed Cymbal Meet seats, significantly below the enterprise benchmark of 75%. Analysis indicates that 1,200 seats from the recent Apex Communications acquisition remain on legacy videoconferencing tools. This adoption plan outlines a 90-day strategy to achieve 65%+ login rates by transitioning the acquired workforce to Cymbal Meet.

#### Section 2: Current State Assessment

| Metric | Current Value | Segment Benchmark | Gap |
| --- | --- | --- | --- |
| Active login rate | [value] | [benchmark] | [gap] |
| Meetings per user/month | [value] | [benchmark] | [gap] |
| Ad-hoc call ratio | [value] | [benchmark] | [gap] |
| Platform diversity | [value] | [benchmark] | [gap] |

Include a brief analysis of what's driving the gap — not just the numbers but the underlying cause (e.g., legacy tool persistence, missing calendar integration, lack of training).

#### Section 3: Root Cause Analysis

Identify the specific reasons for low adoption. Common root causes include:

- **Legacy tool persistence** — Users have not been transitioned from a previous platform
- **Insufficient training** — Users don't know how to use Cymbal Meet effectively
- **Missing executive sponsorship** — No visible leadership endorsement
- **Configuration gaps** — Calendar integration not set up, SSO issues, client not deployed
- **Feature restrictions** — IT policies disabling features users need (ad-hoc calls, screen sharing)

#### Section 4: Recommended Actions

Provide a numbered list of specific, actionable steps with owners and timelines.

**Example Actions:**

1. **Identify and Appoint Champions from Acquired Organization** (Week 1)
   - Select 3-5 respected individuals from the former Apex team
   - Brief them on Cymbal Meet features and the migration plan
   - Provide champion toolkit (quick-start guide, FAQ, escalation path)

2. **Executive Communication** (Week 1-2)
   - Acquired organization leadership sends endorsement email
   - Schedule a town hall on Cymbal Meet hosted by a senior leader from the acquired team

3. **Phased Migration** (Weeks 3-12)
   - Week 3-4: Deploy Cymbal Meet client to acquired users alongside legacy tool
   - Week 5-8: Champions lead department-level intro sessions
   - Week 9-10: Migrate recurring meetings to Cymbal Meet calendar integration
   - Week 11-12: Disable new meeting creation on legacy tool

4. **Training Delivery** (Weeks 3-8)
   - Schedule Tier 1 training sessions specifically for acquired users
   - Record sessions for on-demand access
   - Follow up with non-attendees within 3 business days

5. **Weekly Progress Tracking** (Ongoing)
   - Monitor acquired cohort login rate separately
   - Weekly checkpoint with champions
   - Escalate to CSM if login rate is below 30% at Week 6

#### Section 5: Success Criteria

| Milestone | Target Date | Metric |
| --- | --- | --- |
| [Milestone 1] | [Date] | [Specific metric and target] |
| [Milestone 2] | [Date] | [Specific metric and target] |
| [Milestone 3] | [Date] | [Specific metric and target] |

#### Section 6: Resources and Support

- Links to relevant Cymbal Meet documentation
- Champion toolkit materials
- Training session recordings
- CSM contact information and escalation path

---

## 4. Template: Technical Remediation Plan

### Use When
- Device telemetry shows degraded performance (high latency, packet loss, low quality scores)
- Call quality scores are consistently below 3.5
- Multiple conference rooms are experiencing simultaneous issues
- Users report audio/video problems that correlate with telemetry data

### Document Structure

#### Section 1: Executive Summary

**Example:**
> Coastal Logistics Inc. is experiencing severe device performance issues across all 35 conference rooms since their January office relocation. Telemetry data shows packet loss averaging 4% (vs. 0.3% baseline), network latency of 95ms (vs. 25ms baseline), and video quality scores of 2.2 (vs. 4.2 baseline). Root cause analysis indicates the new office network lacks QoS configuration for video traffic. This remediation plan provides a prioritized action list to restore normal performance within 14 days.

#### Section 2: Impact Assessment

| Metric | Current Value | Healthy Baseline | Severity |
| --- | --- | --- | --- |
| Network latency | [value] ms | 25 ms | [Critical/Warning/Normal] |
| Packet loss | [value]% | 0.3% | [Critical/Warning/Normal] |
| Video quality score | [value] | 4.2 | [Critical/Warning/Normal] |
| CPU usage | [value]% | 35% | [Critical/Warning/Normal] |
| Affected devices | [count] of [total] | 0 | [scope] |

**User Impact:** Describe how the technical issues are affecting end users (e.g., "Users report video freezing in 80% of meetings, leading to a 40% drop in meeting room usage over the past 3 weeks").

#### Section 3: Root Cause Analysis

Detail the technical root cause with evidence:

**Example:**
> Network assessment reveals that the new office at 500 Harbor Drive was provisioned with standard enterprise networking (Cisco Meraki switches, 1 Gbps uplinks) but without QoS policies for real-time communication traffic. Cymbal Meet video traffic (UDP 10000-20000) competes with bulk data transfers, cloud backups, and software updates during business hours. Packet captures confirm that video packets are being queued behind large TCP flows, causing both latency spikes and packet drops when buffers overflow.
>
> Additionally, the conference room VLAN (VLAN 40) shares physical switch uplinks with the general office VLAN (VLAN 10), with no traffic prioritization between VLANs.

#### Section 4: Remediation Steps

**Priority 1 — Immediate (Days 1-3):**
1. [Specific technical action with commands/configuration details]
2. [Specific technical action]

**Priority 2 — Short-Term (Days 4-7):**
3. [Specific technical action]
4. [Specific technical action]

**Priority 3 — Validation (Days 8-14):**
5. [Monitoring and verification steps]
6. [Success criteria check]

**Example Remediation Steps:**

1. **Configure DSCP QoS Markings** (Day 1)
   - Configure all switches between conference rooms and WAN uplink to mark Cymbal Meet traffic:
     - Audio (UDP, DSCP EF/46): Priority Queue
     - Video (UDP, DSCP AF41/34): Assured Forwarding
     - Signaling (TCP 443, DSCP CS3/24): Class Selector
   - Refer to Cymbal Meet Device Performance Guide, Section 5 for complete DSCP configuration

2. **Create Dedicated Conference Room VLAN with Priority Queuing** (Day 2)
   - Move conference room switch ports to a dedicated VLAN with strict priority queuing
   - Allocate minimum 30% of uplink bandwidth to the conference room VLAN

3. **Verify Firewall Rules** (Day 2)
   - Confirm UDP 10000-20000 is allowed to media.cymbalmeet.com
   - Confirm no proxy or SSL inspection on media traffic
   - Check NAT session timeouts (minimum 120 seconds)

4. **Firmware Update** (Day 3)
   - Update all 35 devices to firmware 4.2.1 (latest stable)
   - Schedule staged rollout: 7 devices per night over 5 nights

5. **Monitor and Validate** (Days 4-14)
   - Review telemetry daily for the first week post-remediation
   - Target: latency <40ms, packet loss <0.5%, quality score >3.8
   - If targets not met after QoS changes, escalate to L2 Support for deeper network analysis

#### Section 5: Prevention

Steps to prevent recurrence:
- Document QoS requirements in the organization's network change management process
- Include Cymbal Meet network requirements in future office build-out checklists
- Set up telemetry alerts for latency >50ms or packet loss >1%

---

## 5. Template: Executive Briefing

### Use When
- Usage trends are declining and require leadership attention
- Executive sponsor has departed and a replacement is needed
- Renewal is approaching and engagement metrics are concerning
- Strategic decisions needed (expansion, contraction, competitive displacement)

### Document Structure

#### Section 1: Executive Summary

One paragraph. State the situation, the business impact, and the ask.

**Example:**
> BrightPath Education's Cymbal Meet usage has declined 60% over the past 4 weeks, coinciding with the departure of VP of Operations Sarah Kim, who served as the internal executive sponsor. Without intervention, we project usage will fall below 20% of licensed capacity within 3 weeks, putting the upcoming renewal at significant risk. We recommend identifying a replacement executive sponsor and implementing a re-engagement campaign immediately.

#### Section 2: Engagement Snapshot

Present key metrics in a clear, executive-friendly format:

| Metric | 4 Weeks Ago | Current | Trend | Benchmark |
| --- | --- | --- | --- | --- |
| Weekly active users | [value] | [value] | [arrow] | [benchmark] |
| Meetings per week | [value] | [value] | [arrow] | [benchmark] |
| Call quality | [value] | [value] | [arrow] | [benchmark] |

Include a simple trend visualization if possible (week-over-week chart).

#### Section 3: Risk Assessment

| Risk Factor | Level | Details |
| --- | --- | --- |
| Renewal risk | [High/Medium/Low] | [Brief explanation] |
| Competitive displacement risk | [High/Medium/Low] | [Brief explanation] |
| User satisfaction risk | [High/Medium/Low] | [Brief explanation] |

#### Section 4: Recommended Actions

Keep this short and strategic — executives need 3-5 clear actions, not a detailed project plan.

1. **[Action]** — [Who] — [By when]
2. **[Action]** — [Who] — [By when]
3. **[Action]** — [Who] — [By when]

**Example:**
1. **Identify a new executive sponsor** — Customer's CTO or COO — Within 2 weeks
2. **Schedule executive re-engagement meeting** — CSM + Customer's new sponsor — Week 3
3. **Launch re-engagement campaign** — CSM + Champions — Weeks 3-6
4. **Monthly executive check-in** — CSM + Sponsor — Ongoing through renewal

#### Section 5: CSM Next Steps

- Immediate actions the CSM will take
- Scheduled follow-ups
- Escalation criteria (what would trigger further intervention)

---

## 6. Template: Re-Engagement Campaign

### Use When
- Previously healthy adoption is declining week-over-week
- A specific event caused usage to drop (leadership change, organizational restructuring, negative experience)
- Users have not logged in for 14+ days but were previously active

### Document Structure

#### Section 1: Situation Overview

Describe the decline with data: when it started, how severe, and the likely cause.

#### Section 2: Target Segments

Categorize users by their current engagement level:

| Segment | Definition | Count | Strategy |
| --- | --- | --- | --- |
| Active | Logged in within 7 days | [count] | Reinforce, encourage peer advocacy |
| At-risk | Last login 8-21 days ago | [count] | Targeted outreach, remove friction |
| Lapsed | Last login 22+ days ago | [count] | Re-onboarding campaign |

#### Section 3: Campaign Plan

**Week 1: Diagnose and Prepare**
- Confirm root cause of decline
- Identify any technical blockers (SSO issues, client bugs, network changes)
- Prepare re-engagement communications
- Brief champions on the campaign

**Week 2-3: Outreach**
- At-risk users: personalized email from champion or manager with specific call to action
- Lapsed users: re-onboarding email with updated quick-start guide and training link
- All users: internal communication from new/existing executive sponsor

**Week 4-6: Reinforce**
- Champions host "refresher" sessions for at-risk and lapsed users
- Gamification campaign to incentivize re-engagement (see Best Practices Guide, Section 6)
- Weekly adoption metrics shared with department managers

**Week 7-8: Evaluate**
- Compare adoption metrics to pre-decline baseline
- If recovery <70% of previous levels, escalate to executive briefing
- Transition to ongoing adoption monitoring

#### Section 4: Success Criteria

| Metric | Pre-Decline Baseline | Current | Week 4 Target | Week 8 Target |
| --- | --- | --- | --- | --- |
| Active login rate | [baseline] | [current] | [target] | [target] |
| Weekly meetings | [baseline] | [current] | [target] | [target] |
| At-risk user count | 0 | [current] | [target] | [target] |

---

## 7. Template: Onboarding Acceleration Plan

### Use When
- Initial deployment is behind schedule on adoption milestones
- Acquired workforce onboarding is stalling
- Specific departments are significantly behind the rest of the organization

### Document Structure

#### Section 1: Gap Analysis

| Milestone | Target Date | Status | Gap |
| --- | --- | --- | --- |
| 60% first login | Day 7 | [Actual %] by Day [actual] | [Gap description] |
| 70% training complete | Day 14 | [Actual %] by Day [actual] | [Gap description] |
| 70% login rate | Day 30 | [Actual %] by Day [actual] | [Gap description] |

#### Section 2: Blockers Identified

List specific blockers preventing onboarding success:

| Blocker | Affected Users | Severity | Owner |
| --- | --- | --- | --- |
| [Blocker description] | [Count or %] | [Critical/High/Medium] | [Owner] |

**Common Blockers:**
- SSO configuration issues preventing login
- Desktop client not deployed to all target machines
- Calendar integration not configured for Outlook/Google Calendar
- Legacy tool still available and preferred
- No department champions assigned or champions are ineffective
- Training sessions scheduled at inconvenient times or not promoted

#### Section 3: Acceleration Actions

Numbered list of specific actions to get onboarding back on track, with owners and deadlines. Each action should directly address a blocker from Section 2.

#### Section 4: Revised Timeline

Updated milestones with realistic dates based on the acceleration plan.

---

## 8. General Formatting Guidelines

All intervention documents should follow these formatting standards:

### Branding
- Include Cymbal Meet logo in the document header
- Use Cymbal Meet brand colors: Primary blue (#1A73E8), Secondary gray (#5F6368)
- Font: Google Sans or Roboto for headings; Roboto for body text

### Structure
- Every document starts with an Executive Summary (2-3 sentences)
- Use tables for metrics — easier to scan than paragraphs
- Limit each section to one page when possible
- Include a "Next Steps" or "CSM Contact" section at the end

### Tone
- Professional but approachable
- Data-driven — always include specific numbers, not just qualitative assessments
- Action-oriented — every section should lead to a clear next step
- Customer-facing sections should be empathetic, not accusatory (e.g., "adoption opportunity" not "adoption failure")

### Delivery
- Generate as PDF for formal delivery
- Store in GCS at `gs://{bucket}/{customer_id}/{date}_{type}_{id}.pdf`
- Share link with CSM for distribution to the customer
- CSM should present the document in a meeting, not just send it as an attachment

---

*Cymbal Meet Customer Success Team — These templates are maintained by the CS Operations team. For template updates or new template requests, contact cs-ops@cymbalmeet.com.*
