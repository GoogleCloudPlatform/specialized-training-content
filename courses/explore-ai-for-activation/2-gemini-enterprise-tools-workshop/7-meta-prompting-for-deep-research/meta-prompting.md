# Meta-Prompting for Deep Research

## Time Required
20 minutes

## Overview
Meta-prompting means asking Gemini to improve a prompt before you use it. Instead of spending time crafting the perfect research brief yourself, you describe what you want, ask Gemini to rewrite it into a stronger prompt, and then run that improved version.

This lab shows the difference a better prompt makes. You will run a simple, vague request through Deep Research, use meta-prompting to produce a stronger version, and run it again to compare the results.

### You learn how to:
- Recognize the limitations of a vague Deep Research prompt.
- Use meta-prompting to turn a weak prompt into a well-structured one.
- Compare research quality before and after meta-prompting.

## Scenario

<p align="left">
  <img src="images/human-ai.png" width="70%" alt="Cymbal Capital Partners" />
</p>

Cymbal Capital Partners is evaluating a new investment opportunity. You are creating a research brief for a meeting this afternoon with your boss and a couple of partners. You have tried using Deep Research. The results are pretty good, but not great. 

Your want to use meta-prompting to see if Gemini can help you build a prompt that produces a better result than a quick, unstructured question.

## Lab Instructions

### Task 1: Run a weak baseline prompt

Start with the kind of prompt most people write on their first try.

1. Choose a company to research. Pick one from the list below, or use any company you find interesting.

   | Company | What they do |
   |---------|--------------|
   | **Stripe** | Payments infrastructure for the internet |
   | **Databricks** | Data and AI platform for enterprises |
   | **Anthropic** | AI safety company and developer of the Claude model |
   | **Canva** | Online design and visual communication platform |
   | **Scale AI** | Data labeling and AI infrastructure for ML teams |
   | **Hugging Face** | Open-source AI model hub and developer tools |
   | **Perplexity AI** | AI-powered answer engine and search alternative |
   | **Harvey AI** | Generative AI platform built for legal work |

2. Open Gemini Enterprise and start a new chat. Select **Deep Research** from the **Tools** list.

3. Paste the following prompt, replacing `[Company Name]` with your chosen company:

```text
Research [Company Name] and tell me if it would be a good investment for Cymbal Capital Partners.
```

4. Review the research plan when it appears. Notice how broad or narrow the plan is given the vague prompt.

5. Click **Start research**. When the output is ready, keep this tab open—you will compare it with Task 3.

### Task 2: Use Meta-Prompting to build a better prompt

Now ask Gemini to improve the weak prompt before running Deep Research again.

1. Open a **new chat** in Gemini Enterprise in a new borwser tab. Do **not** select Deep Research—use the regular chat mode for this step.

2. Paste the following prompt, replacing `[Company Name]` with the same company you chose:

```text
You are an expert at writing Deep Research prompts. Rewrite my rough question into the best possible Deep Research prompt. Return only the improved prompt, ready to paste directly into Deep Research.

Here is my rough question:
"Research [Company Name] and tell me if it would be a good investment for a venture capital firm."
```

3. Read the improved prompt Gemini returns. Notice what it added—structure, scope, output format, evidence standards—things you did not specify. That is meta-prompting: Gemini applied its own knowledge of what makes a good prompt so you did not have to.

### Task 3: Run Deep Research with the improved prompt

1. Copy the improved prompt from Task 2.

2. Open a **new chat**, select **Deep Research**, and paste the improved prompt.

3. Review the research plan—compare it with the one from Task 1. A stronger prompt should produce a more detailed and better-organised plan.

4. Click **Start research**.

5. When the output is complete, compare it side by side with your Task 1 result:
   - Does this version cite specific sources?
   - Are uncertain claims labeled as Unverified?
   - Is the recommendation more specific and actionable?
   - Which output would you actually use in a partner meeting?


### Bonus Task 4: Apply Meta-Prompting to your own work

Think of a research question relevant to your own organization. It does not need to be investment-related. Some ideas:

| Scenario | Example question |
|----------|-----------------|
| **Market research** | What are the emerging trends in [your market] over the next 2–3 years? |
| **Competitor analysis** | How do the top competitors to [your product] differentiate on features and pricing? |
| **Technology evaluation** | What are the leading tools for [a capability your team needs] and what are the trade-offs? |
| **Regulatory landscape** | What compliance requirements apply to [your industry] in [a region]? |
| **Partnership scouting** | Who are the most credible vendors in [a domain relevant to you]? |

1. Write a one-sentence rough version of your question.

2. Use the meta-prompting technique from Task 2 to improve it into a full Deep Research prompt.

3. Run the improved prompt and share one key finding with the group.

## Congratulations!

In this lab, you have:
- Run a vague prompt through Deep Research and identified its limitations.
- Used meta-prompting to turn that weak prompt into a well-structured research brief.
- Compared research quality before and after meta-prompting and seen why prompt structure matters.
