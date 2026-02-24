# Presenter Script

Step-by-step guide for delivering the demo scenario.

## Before you start

- Start the demo server locally, or deploy to Cloud Run (see README.md)
- Open to **Intro to Cymbal Meet** page

---

## Intro to Cymbal Meet

### The business

1. Let's look at Cymbal Meet, a videoconferencing company that sells hardware for conference rooms and SaaS subscriptions for rooms and end-users.
1. They do $500M a year in revenue, sell globally, and serve SMB, mid-market, and enterprise customers.

### 2026 planning

1. The executive team kicked off 2026 with a strategic planning effort focused on identifying the biggest problems and opportunities for the business.
1. For each, they defined the current state of the business, where they wanted the business to go, and what impact these changes would have.
1. Then, they worked with an AI consulting team to evaluate these high priority initiatives and identify which might be good candidates for agentic AI innovation.

## Big business problems

### High-level

So let's look at the top three business problems the executive team decided to tackle:

1. Improving net retention (kind of the holy grail for recurring revenue businesses)
1. Accelerating product development (get features to market faster)
1. Optimize the entire approach to long-term, strategic customer contracts

### Drill down into problem 1

1. Let's expand the problem 1 card and drill down.
1. The problem is basically that there are customers who fall short of desired engagement levels, and they end up failing to upsell, or even worse, they churn.
1. Cymbal Meet is failing to address the majority of these shortfalls actively and with high-quality interventions.
1. Leadership estimates that if they can improve interventions, and as a result improve engagement, they can drive up gross and net retention.
1. You can see their goals are to move from good to world-class gross/net retention rates.
1. And the estimate is that in the first year, this could drive \$65M in additional revenue; and over 5 years drive $450M.
1. Now, notice that at this point we're not talking about agents, or even AI, at all. This is important. Building valuable solutions starts by looking at the business, not the technology.
1. We'll come back and talk about whether agents makes sense in a minute.

### The other problems

1. Let's expand the problem 2 card.
   1. You can see a similar analysis, and similar goal setting has taken place here. We won't dig too deep on this one.
1. But I do want to dig into problem 3 (expand card). 
   1. Notice this problem is about increasing retention and increasing contract length with the top 50 customers.
   2. You can see in the description of the business problem that this requires a lot of relationship management and very complex contract negotiations.
   
### Agentic innovation fit

1. The executive team brought in a consulting team to help evaluate these strategic initiatives to determine which are most likely to be good candidates for agentic innovation.
2. Let's look at problem 1.
   1. Agents are good at looking at structured and unstructured data and identifying patterns, even when not given explicit instructions on what to look for. Since finding undesirable engagement patterns is key to this problem, that seems a good fit.
   2. Agents are good at reading, understanding, reasoning about, and creating content. This means agents can look at CRM data, documentation, professional services engagement summaries, and other sources to identify good ways to respond to engagement shortfalls, and they can craft personalized interventions for each customer.
   3. And obviously agents, being software, are good at doing these things at scale.
   4. Given these characteristics, this problem seems promising, so the leadership team is going to task the internal innovation team to explore how agentic AI can be applied.
3. Problem 3 is another story.
   1. It's heavily reliant on personal relationships and EQ.
   2. It requires creation and vetting of complex legal documents that are often unique.
   3. And it's a problem that doesn't affect thousands of instances; there's really only 50 customers, and typically you negotiate annually or every few years.
   4. This is not a great candidate, and so while the company will tackle this problem, it's not one that the internal innovation team is going to prioritize for agentic intervention.

> [!TIP] 
> Ask for their reaction.
> - Does that make sense? 
> - Any thoughts/questions?

## Analyzing the current processes

### Approach

1. So the innovation team begins their investigation into how agents might have an impact on this problem.
2. The team takes the problem and finds the various operational process currently in place for this area of the business.
3. For each of those processes, they're going to build a process map to understand what is done today, and where help might be beneficial.

### Processes

1. So for our example, we're going to focus on one of the discovered processes.
2. This is a process for identifying when SMB and mid-market customers are falling short of expected engagement, and the creating and executing intervention campaigns at scale.

### The scaled product engagement intervention process

1. So the team gathers existing documentation, and does research where there are gaps, and comes up with a process map.
2. The process is comprised of stages, and stages are comprised of tasks.
   1. In real, complex processes, stages might have sub-stages and tasks might have steps.
   2. We've simplified a bit for this discussion.
3. The detection phase is where:
   1. Customer Success managers collect usage data.
   2. They compare data against targets.
   3. They identify and characterize different types of engagement shortfalls.
   4. And they do sort a fuzzy-logic scan to identify undesirable patterns that aren't as simple as falling 20% below target on a specific metric.
4. The design phase is where:
   1. The CSM looks at templates for interventions.
   2. They look at CRM system details, internal knowledgebases, etc.
   3. They tweak the template or create a new intervention based on what they find.
5. The execution phase is where:
   1. The CSM sends emails.
   2. They configure backend systems to do in-product notifications.
6. And the sync a report phase is where:
   1. The CRM gets updated with information about outreach.
   2. Systems are configured to collect and report intervention results.
   3. Etc.
7. Paint points
   1. You'll notice that the team went above and beyond and actually identified pain points for each of the stages.
   2. All of the stages have one common pain point which is that it's a lot of manual toil.
   3. And due to that sheer amount of work, you run into things like missed signals and poorly conceived interventions.

## Reimagining the process

### Approach

1. The next phase entails going through the current process, and identifying how/why agents can be integrated.
2. Type of touchpoints:
   1. Agents may take over a task entirely (that's replacement).
   2. Agents may work with a human to accomplish a task (that's augmentation).
   3. Agents may actually make possible new steps that weren't feasible before (that's adding).
   4. And agents may act as a bridge between systems (that's integration).
3. Processes might also end up with certain tasks removed as they're no longer needed.

### The reimagined process

1. You can see that for most of the detection phase tasks:
   1. Agents replace the human effort.
   2. They query the data sources, detect shortfalls, categorize, etc.
   3. One task that's added is checking a new data source—the CRM—is used to make detection smarter.
2. In the design phase:
   1. The agent does additional work to identify why the shortfall is occurring.
   2. It takes over defining the intervention.
   3. And for complex interventions, it proposes tailored content to the CSM, who reviews and updates.
3. In the execution phase:
   1. The agent takes over the work of sending the emails.
   2. It surfaces in-product outreach programs to the CSM for review/approval.
   3. And if the CSM approves, it then activates the in-product campaign.
4. In the sync and report phase:
   1. The agent updates backend systems like the CRM and the Customer Success dashboard.
   2. The manual effort to create results reports is deleted since the CSM dashboard will show results.
   3. And the agentic system will create an audit trail showing all intervention activity.

> [!TIP] 
> Ask for their reaction.
> - Do the different types of touchpoints make sense? 
> - Any thoughts/questions?

## Agentic solution design

1. At this point, it's time to turn general ideas about agent involvement into actual agent designs.
2. You can see the activities in this phase include:
   1. Defining exactly what each agent does.
   2. Designing how the agent will do those things.
   3. And spelling out how the agents talk to each other, where they run, and how they integrate with external systems.
3. And there's a list here of typical artifacts generated during these activities.
   1. Documentation
   2. Evaluation data
   3. Etc.

## Building and deploying agents

1. Once the agents have been designed it's time to start building.
2. You prototype, pilot, and validate agent concepts.
3. Then you build, launch, and operate production agents.

## Agent demo

### Intro

1. Ok, so that's all great—but what will an agentic solution really look like?
2. Well, we've put together a demo that illustrates the types of things you can expect.

### CRM

> [!NOTE] 
> Click the button in CRM System card.

1. CRM: Here we have a CRM system with our customers. 
   1. There are 24 in this demo system, but assume we're closer to 2400 in real life.
1. Note that for each customer we have a history of interactions which span support, sales, customer success, etc.

### CSM Dashboard

> [!NOTE] 
> Click Cymbal Meet Logo in center panel to return to home page.
> Click the button in CSM Dashboard card.

1. This is a dashboard that Customer Success Managers use to track:
   1. Customer health
   2. Customer engagement with the product
   3. Outreach and intervention activities
   4. Etc.
1. If we drill down into a customer (Nexus Tech), you can see that we chart actual engagement behaviors against targets.
   1. These engagement signals are known to be important; drops in engagement are highly correlated with stalled expansion and churn.
   2. You can see that this customer has a shortfall in 7-Day Active users over the last 30 days, and a big shortfall in the frequency with which they schedule meetings that use Cymbal Meet.
1. As we noted in the problem/process pages, because finding these issues and building/running interventions is time consuming and prone to consistency/quality issues, we're failing to address them all successfully. That's where the agents come in.


### The agents in action

> [!NOTE] 
> Return to CSM Dashboard listing.

1. Cymbal Meet has built an agentic system that kicks in weekly to find and address these engagement issues. 
2. I'm going to invoke the system as though it was early Monday morning (click button).
3. Don't worry about reading the status report; this is just showing that the agentic system is doing it's thing.
4. We can see that the unattended system scans all the customers and finds those with engagement issues.
5. For each issue, it searches internal docs, the CRM system, and other sources of data, then composes an appropriate, customized response.
6. Some interventions are tailored emails; some are configurations of the backend system to trigger in-product guidance for users, etc.

### The results

> [!NOTE] 
> Close the agent run modal.

1. You'll notice that the dashboard has been updated, and shows interventions that are underway and pending approval. 
   1. This is a clue that some things the agent can do entirely on its own; others, you want a human-in-the-loop making approvals and/or tweaks.
2. If we look at Nexus Tech, we can see:
   1. There's a messaging campaign recommended which would touch end-users directly. 
      1. This is something that requires CSM approval before it is executed. 
      2. We'll approve, and the agentic system will then do the activation.
   2. You can also see that this customer had a second intervention, which is a custom email outreach to the administrator.
   3. Let's actually look at each of these to see what was done, and why agents are helpful.
3. Here is the customer success manager's email. You can see:
   1. The agent has sent emails of various types to primary technical contacts at the customers who have engagement issues.
   2. If we look at the email to Nexus Tech, you can see it calls out: 
      1. Things that are good, including positive themes received from users of the product. These themes will differ across customers, and LLM-backed agents are particularly good at reading, classifying, and measuring the sentiment of text input.
      2. Areas that are underperforming, again with themes pulled out from text responses of end users. 
      3. Recommended actions that are built particularly for this customer. 
         1. You'll notice each action says why it was selected, and in this case, the first one is based on CRM notes. The scanning of the CRM notes, the decision on what to suggest, and the phrasing of the email and explanation is all done by the agents.
   3. If we look at Greenleaf, you can see the format is similar but the recommendations and reasoning are different.
   4. If we look at the third email, you can see this is more of a direct intervention, telling the customer what's wrong and what to do about it. Again, the agent can decide what performance details to share, how to format, and what directions to pull from troubleshooting guides and present neatly in the email.
4. If we check out the VC system backend we can see:
   1. The intervention the CSM approved has been enabled.
   2. The other similar interventions are pending CSM approval.
5. And what exactly is being approved/enabled?
   1. Well, when a user logs into the VC client, they see a UI like this.
   2. But if it's a Nexus Tech employee where the calendar outreach interventions have been built and enabled, it looks like this:
      1. The agent has composed the text presented.
      2. The agent has decided what actions to enable.
      3. With CSM approval, the agent configured the system to present the prompt to the user in product.
      4. Because this outreach directly affects lots of users, the agent didn't do this automatically, the CSM applies some judgement in allowing/disallowing the outreach.

> [!TIP] 
> Ask for their reaction.
> - Does that give you a sense for the types of things an agent can do, and the benefits it might achieve? 

## Takeaways

1. Okay, that was quite the involved demo scenario.
2. But hopefully it did a good job driving home these takeaways:
   1. Success with agentic innovation starts with a focus on the business, not the cool technology.
   2. Agents aren't always the answer; some things are best handled by people with important skills that agents don't have.
   3. The process is non-trivial. It requires a methodical approach to executing a clearly laid out blueprint.
   4. Agents are really good at things that are data intensive, require straightforward reasoning about data, and produce personalized, adaptive outputs.
