# Cymbal Meet — Admin Guide: User Onboarding

## Step-by-Step Best Practices for Onboarding New Cymbal Meet Users

Version 2.5 | Last Updated: December 2025 | Document ID: CM-ADM-ONB-001

---

## 1. Overview

Effective onboarding is the strongest predictor of long-term Cymbal Meet adoption. Organizations that follow a structured onboarding process achieve 70%+ login rates within 30 days, compared to 35% for organizations that simply provision accounts and send login credentials.

This guide provides a step-by-step onboarding framework suitable for initial deployments, seat expansions, and acquired workforce integration.

## 2. Pre-Onboarding Checklist (Admin Tasks)

Complete these tasks before users receive their first communication about Cymbal Meet.

### 2.1 Technical Readiness

- [ ] Cymbal Meet licenses are provisioned in the admin console for all target users
- [ ] SSO / identity provider integration is configured and tested (SAML 2.0 or OIDC)
- [ ] Calendar integration is verified (Google Calendar connector or Outlook add-in deployed)
- [ ] Network QoS is configured for Cymbal Meet traffic (see Device Performance guide)
- [ ] Conference room devices are installed, firmware is updated, and room calibration is complete
- [ ] Firewall rules allow Cymbal Meet traffic (TCP 443, UDP 10000-20000)
- [ ] Desktop client is available via software distribution (SCCM, Intune, Jamf, etc.)
- [ ] Mobile client is available in managed app catalog (if using MDM)

### 2.2 Content Readiness

- [ ] Welcome email template is prepared (see Section 4)
- [ ] Training sessions are scheduled (see Section 5)
- [ ] Quick-start guide is localized (if applicable)
- [ ] Internal support channel is established (Slack channel, Teams channel, or email alias)
- [ ] FAQ document is prepared with organization-specific answers (VPN configuration, approved use cases, recording policy)

### 2.3 People Readiness

- [ ] Executive sponsor is identified and has agreed to send endorsement communication
- [ ] Department champions are identified and briefed (see Best Practices Guide)
- [ ] IT help desk is trained on Cymbal Meet L1 support (basic troubleshooting, account issues)
- [ ] CSM is informed of onboarding timeline and target user count

## 3. Onboarding Timeline

### Standard Onboarding (New Deployment)

| Day | Activity | Owner | Success Metric |
| --- | --- | --- | --- |
| Day -7 | Executive sponsor sends announcement email | Executive Sponsor | Email sent to all target users |
| Day -3 | IT deploys desktop client via software distribution | IT Admin | Client installed on >90% of target machines |
| Day 0 | Welcome email sent with login instructions and training schedule | IT Admin / Comms | Email delivered to 100% of target users |
| Day 0-1 | Users log in for the first time | Users | 40% first-day login rate |
| Day 1-3 | Tier 1 training sessions (basic usage) | Training Lead | 70% attendance |
| Day 3-5 | Champions host department intro sessions | Champions | Each department has at least one session |
| Day 7 | First adoption checkpoint | IT Admin / CSM | 60% login rate, 30% have joined a meeting |
| Day 7-14 | Tier 2 training for meeting organizers | Training Lead | 50% of organizers trained |
| Day 14 | Second adoption checkpoint | IT Admin / CSM | 65% login rate, 50% have joined a meeting |
| Day 21 | Migrate recurring meetings to Cymbal Meet calendar integration | Champions | 80% of recurring meetings migrated |
| Day 30 | 30-day adoption review with CSM | CSM / IT Admin | 70% login rate target |

### Accelerated Onboarding (Seat Expansion)

For organizations adding users to an existing Cymbal Meet deployment:

| Day | Activity | Success Metric |
| --- | --- | --- |
| Day 0 | Licenses provisioned, welcome email sent | 100% provisioned |
| Day 0-2 | Self-paced training (link to recorded Tier 1 session) | 60% complete training |
| Day 3 | Champion intro session for new users | Session held |
| Day 7 | Adoption checkpoint | 60% login rate |
| Day 14 | Follow-up with non-adopters | Targeted outreach sent |

### Acquired Workforce Onboarding

When onboarding users from an acquired company who may be using a competing videoconferencing tool:

| Phase | Timeline | Activity | Success Metric |
| --- | --- | --- | --- |
| Discovery | Week 1-2 | Audit current tool usage, identify power users, understand workflows | Audit complete |
| Preparation | Week 3-4 | Deploy Cymbal Meet alongside legacy tool, configure SSO, train champions from acquired team | Technical readiness |
| Soft Launch | Week 5-8 | Encourage Cymbal Meet for new meetings; legacy tool remains available | 30% of new meetings on Cymbal Meet |
| Migration | Week 9-12 | Migrate recurring meetings, disable new meeting creation on legacy tool | 70% of meetings on Cymbal Meet |
| Sunset | Week 13-16 | Remove legacy tool, full transition to Cymbal Meet | Legacy tool decommissioned |

**Key Principles for Acquired Workforce:**

- Do NOT force an immediate switch — this creates resentment and resistance
- Identify 2-3 champions from the acquired team (peer influence is more effective than top-down mandates)
- Acknowledge that the legacy tool has features users value — show how Cymbal Meet addresses the same needs
- Track the acquired cohort separately from existing users to measure progress accurately
- Extend timeline if adoption rate falls below 20% at the Soft Launch checkpoint — forcing the issue will backfire
- Have the acquired team's leadership (not the parent company's) communicate the transition plan

## 4. Communication Templates

### 4.1 Executive Sponsor Announcement (Day -7)

**Subject:** Introducing Cymbal Meet — Our New Videoconferencing Platform

**Body:**

> Team,
>
> I'm excited to announce that we're adopting Cymbal Meet as our standard videoconferencing platform. Cymbal Meet provides HD video, seamless calendar integration, conference room devices, and mobile support — everything we need for effective collaboration.
>
> Starting [DATE], you'll receive login credentials and training invitations. Our IT team has worked to ensure a smooth transition, and [CHAMPION NAMES] in your departments will be available to help you get started.
>
> I'll be using Cymbal Meet for our upcoming [MEETING NAME] on [DATE], and I encourage everyone to join from the Cymbal Meet client to get hands-on experience.
>
> [EXECUTIVE NAME]

### 4.2 Welcome Email (Day 0)

**Subject:** Welcome to Cymbal Meet — Get Started in 3 Steps

**Body:**

> Welcome to Cymbal Meet!
>
> **Step 1:** Log in at meet.cymbalmeet.com with your company credentials (SSO)
> **Step 2:** Download the desktop client: [LINK] (also available on mobile: iOS / Android)
> **Step 3:** Join the training session on [DATE] at [TIME]: [MEETING LINK]
>
> **Quick Start:**
> - To join a meeting: Click the meeting link in your calendar
> - To start an instant call: Open Cymbal Meet > click "New Meeting"
> - To schedule a meeting: Use the Cymbal Meet button in your calendar app
>
> **Need help?** Contact [SUPPORT CHANNEL] or reach out to your department champion: [CHAMPION NAME]

### 4.3 Non-Adopter Follow-Up (Day 14+)

**Subject:** We noticed you haven't tried Cymbal Meet yet — can we help?

**Body:**

> Hi [NAME],
>
> We noticed you haven't logged into Cymbal Meet yet. We want to make sure there's nothing blocking you from getting started.
>
> **Common issues we can help with:**
> - Login or SSO problems → Contact [SUPPORT CHANNEL]
> - Can't find the desktop client → Download here: [LINK]
> - Not sure how it works → Watch this 3-minute intro video: [LINK]
> - Prefer your current tool → Let's talk about how Cymbal Meet handles your workflows: [CHAMPION CONTACT]
>
> If you've already started using Cymbal Meet, great — ignore this message!

## 5. Training Program

### 5.1 Tier 1: All Users (30 minutes)

**Format:** Live session on Cymbal Meet (recorded for on-demand access)

**Agenda:**
1. Logging in and navigating the interface (5 min)
2. Joining a meeting via link and calendar (5 min)
3. Audio and video settings (5 min)
4. Screen sharing and chat (5 min)
5. Mobile app overview (3 min)
6. Q&A (7 min)

**Materials:** Quick-start PDF handout, FAQ document, support contact information

### 5.2 Tier 2: Meeting Organizers (60 minutes)

**Format:** Live instructor-led workshop on Cymbal Meet

**Agenda:**
1. Scheduling meetings (calendar integration deep-dive) (15 min)
2. Meeting settings: recording, waiting room, permissions (10 min)
3. Advanced features: breakout rooms, polls, whiteboard (15 min)
4. Conference room device basics for meeting organizers (10 min)
5. Hands-on exercise: schedule and run a meeting with breakout rooms (10 min)

**Prerequisites:** Tier 1 completion (or equivalent experience)

### 5.3 Tier 3: IT Administrators (2 hours)

**Format:** Hands-on workshop (in-person or virtual)

**Agenda:**
1. Admin Console overview: users, devices, policies, analytics (20 min)
2. User provisioning and SSO configuration (15 min)
3. Device management: deployment, firmware, troubleshooting (20 min)
4. Network requirements and QoS configuration (15 min)
5. Security policies and compliance settings (15 min)
6. Analytics and reporting: adoption metrics, call quality, device health (15 min)
7. Hands-on lab: configure a test policy, deploy a firmware update, pull an analytics report (20 min)

## 6. Adoption Measurement During Onboarding

### Key Metrics

| Metric | Day 7 Target | Day 14 Target | Day 30 Target |
| --- | --- | --- | --- |
| First login rate | 60% | 70% | 80% |
| Active users (logged in within last 7 days) | 50% | 60% | 70% |
| Meeting participation (joined at least 1 meeting) | 30% | 50% | 65% |
| Meeting scheduling (created at least 1 meeting) | 10% | 15% | 20% |
| Training completion (Tier 1) | 50% | 70% | 85% |
| Support tickets | <5% of users | <3% of users | <2% of users |

### Monitoring and Intervention Triggers

| Signal | Threshold | Intervention |
| --- | --- | --- |
| Low first-login rate | <40% by Day 7 | Resend welcome email; have champions do in-person outreach |
| Login rate plateau | No increase for 5+ consecutive days | Identify and address specific blockers (SSO issues, client deployment failures) |
| High support ticket rate | >5% of users by Day 7 | Review tickets for common themes; create FAQ or fix systematic issues |
| Department outlier | Any department >20 points below org average | Champion-led targeted intervention for that department |
| Zero meetings joined | >30% of logged-in users by Day 14 | Check calendar integration; schedule champion-led team meetings |

## 7. Post-Onboarding Handoff

At Day 30, transition from onboarding mode to steady-state adoption management:

1. **Onboarding Report:** Compile final metrics and share with executive sponsor and CSM
2. **Champions Transition:** Shift champions from onboarding support to ongoing adoption (monthly tips sessions, new hire onboarding)
3. **Support Transition:** Route Cymbal Meet issues through standard IT support with escalation to CSM for systemic issues
4. **Legacy Tool Review:** If a legacy tool is still active, set a sunset date based on onboarding results
5. **Ongoing Metrics:** Transition to monthly adoption reporting (see Best Practices Guide, Section 4)

## 8. Troubleshooting Common Onboarding Issues

### Users Can't Log In

| Symptom | Cause | Fix |
| --- | --- | --- |
| "Account not found" | License not provisioned | Admin Console > Users > verify provisioning |
| SSO redirect loop | IdP configuration error | Check SAML assertion mapping; verify ACS URL |
| "Access denied" | Conditional access policy blocking | Check IdP conditional access rules for Cymbal Meet |
| Password prompt (SSO expected) | User navigated to wrong login URL | Ensure login URL is `meet.cymbalmeet.com/sso` |

### Calendar Integration Not Working

| Symptom | Cause | Fix |
| --- | --- | --- |
| No "Cymbal Meet" button in calendar | Add-in not deployed | Deploy Outlook add-in via group policy; enable Google Calendar integration in Workspace admin |
| Meeting links not generated | Calendar connector offline | Admin Console > Integrations > Calendar > verify status |
| Wrong time zone on meetings | User profile time zone mismatch | User: Settings > Profile > Time Zone; Admin: check IdP attribute mapping |

### Desktop Client Won't Install

| Symptom | Cause | Fix |
| --- | --- | --- |
| Blocked by endpoint protection | Client not allowlisted | Add Cymbal Meet installer hash to allowlist |
| Insufficient disk space | <500 MB available | Free disk space or install web client only |
| Admin rights required | Local admin policy | Deploy via MDM/SCCM with elevated permissions |

---

*Cymbal Meet Customer Success Team — For onboarding planning and support, contact your assigned Customer Success Manager. We recommend scheduling a kickoff call at least 2 weeks before your target onboarding date.*
