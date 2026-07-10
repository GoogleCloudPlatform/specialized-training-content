# Bring Your Own Agent Use Case

## Time Required
45 minutes

## Overview
This is your lab. You have spent the previous labs building agents for Cymbal Insurance—structured scenarios with defined prompts and expected outputs. Now it is your turn to define the problem and build the solution.

In this lab, you design and build an agent that solves a real challenge from your own work or organization. You will apply everything you have learned: prompt-based creation, the flow builder, knowledge documents, starter prompts, scheduling, and multi-agent routing.

### You learn how to:
- Translate a real workplace problem into a well-defined agent use case.
- Choose the right agent architecture for your scenario.
- Write effective instructions that make your agent reliable and consistent.
- Test and refine your agent using the Preview tab.

## Your Scenario

This lab does not have a prescribed scenario. You will define one. Think about the tasks in your organization that are:
- **Repetitive**—done the same way every time, following a known process
- **Information-heavy**—require reading, summarizing, or extracting from documents or web sources
- **Routing-based**—categorize inputs and direct them to different responses or people
- **Scheduled**—should happen automatically at a regular cadence without a human trigger

The best agent use cases solve a real pain point. Start there.

## Lab Instructions

### Task 1: Define your use case

Before you build anything, invest a few minutes in clearly defining the problem. Agents built from vague intentions are hard to test and even harder to refine.

1. In a new document or notebook, answer the following questions:

   - **What is the problem?** Describe in one or two sentences the specific task or workflow that is inefficient, inconsistent, or time-consuming today.
   - **Who does it affect?** Name the role or team that would benefit from this agent.
   - **What does the agent receive as input?** (Examples: a raw email, a form submission, a name and date, a URL, a file upload, a scheduled trigger)
   - **What does the agent produce as output?** (Examples: a structured report, a routed response, a drafted email, a summary, an alert)
   - **What information does the agent need to do its job?** (Examples: company policy documents, product data, routing rules, web search access)

2. Based on your answers, choose the agent architecture that fits your use case:

   | If your use case is... | Choose this approach |
   |---|---|
   | A single-purpose task with clear input and output | Simple agent (prompt-based) |
   | Grounded in a specific document or policy | Agent Designer with knowledge file upload |
   | Multiple distinct steps or roles | Multi-agent system with sub-agents |
   | Needs to run automatically on a schedule | Agent with a configured schedule |

> [!NOTE]
> You can combine approaches. A scheduled agent can also have sub-agents. A knowledge-grounded agent can also have starter prompts. Start simple and add complexity only if it is needed.

3. Write a one-paragraph description of your agent. Include: what it is called, what problem it solves, who uses it, what it takes as input, and what it produces as output. This paragraph will become the basis for your agent creation prompt.

### Task 2: Design and build your agent

1. Open your Gemini Enterprise web app and click **+ New agent**.

2. **If you are using the prompt-based method:** Write a detailed creation prompt based on your Task 1 description. Structure it clearly:

   ```text
   Create an agent called "[Your Agent Name]".

   Purpose: [One sentence describing the agent's job]

   When a user submits [describe the input], the agent should:
   1. [First action]
   2. [Second action]
   3. [Third action]

   Output format: [Describe the structure of the output — headers, sections, labels, etc.]

   Constraints:
   - [Any rules about what the agent should or should not do]
   - [Tone, length, or accuracy requirements]
   ```

3. **If you are using the flow builder:** Click **Proceed to builder** and configure each node manually. For each agent node, write instructions that answer these three questions:
   - What is this agent's specific job?
   - What does it receive as input?
   - What exactly does it produce as output?

4. If your agent needs knowledge documents, prepare them before building:
   - Create a Google Doc with the relevant policy, reference material, or structured data
   - Download as a PDF
   - Upload in the **Knowledge** section of the agent configuration panel

5. If your agent benefits from starter prompts—the most common questions or requests a user would have—add up to three in the **Personalization** section.

6. If your agent should run on a schedule, click the **Schedule** tab and configure the frequency, time, timezone, and execution prompt.

### Task 3: Test and refine

A first draft agent rarely performs perfectly. Testing and refinement are part of the process.

1. Click the **Preview** tab and run at least three tests using realistic inputs. For each test, evaluate:
   - Does the agent understand the input correctly?
   - Is the output structured the way you designed it?
   - Are edge cases handled appropriately, or does the agent break?

2. Identify the weakest part of the output and use the left chat pane to address it directly:

   ```text
   Update the instructions so that [describe the specific behavior you want to change].
   ```

3. Test again after each refinement. Repeat until the output is reliable across different inputs.

4. Ask a colleague to test the agent without seeing your instructions. Observe where they get confused or where the output does not meet their expectations. Use that feedback to make one final round of refinements.

5. When you are satisfied, click **Create** (or **Update**) to launch the agent.

> [!NOTE]
> You can always return to edit an agent. Go to **Agent Gallery > Your agents**, click **Actions**, and select **Edit**. There is no penalty for iterating after launch.

### Bonus Task 4: Extend your agent

Choose one or more of the following extensions to push your agent further.

**Add a schedule**
If your agent performs a task that should happen automatically at a regular cadence, configure a schedule. Go to the **Schedule** tab, add a schedule with an appropriate frequency and execution prompt, and use **Run in preview** to verify it before activating.

**Add a sub-agent**
If your agent currently handles multiple distinct responsibilities in a single set of instructions, consider splitting it. Move one responsibility to a dedicated sub-agent. This often improves accuracy because each agent can focus on one job.

**Add knowledge documents**
If your agent currently relies entirely on its training data for factual information about your organization, consider uploading a relevant document to the **Knowledge** section. Test whether grounding the agent in a specific source improves accuracy and reduces hallucinations.

**User test with a real scenario**
Share your agent with someone who would genuinely use it in their day-to-day work. Give them three realistic inputs to test with. Collect their feedback on what was useful, what was confusing, and what was missing. Use that feedback to make one concrete improvement.

## Congratulations!

In this lab, you have:
- Translated a real workplace problem into a clearly defined agent use case.
- Chosen an agent architecture appropriate for your scenario.
- Written agent instructions that produce reliable, structured output.
- Tested and refined your agent using the Preview tab and real-world feedback.

You have now built agents for structured tasks, knowledge-grounded assistance, multi-department coordination, and autonomous scheduled workflows. The tools are the same for every use case—the skill is in knowing how to define the problem clearly enough that the agent can solve it reliably.
