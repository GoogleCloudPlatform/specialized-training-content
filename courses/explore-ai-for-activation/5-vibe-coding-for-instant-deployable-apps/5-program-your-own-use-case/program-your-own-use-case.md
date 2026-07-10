# Program Your Own Use Case

## Time Required
45 minutes

## Overview
In this lab, you apply everything you have learned about vibe coding to build a real application of your own design. You choose the idea, define the features, design the UI, and build it using either Gemini Canvas or Google AI Studio.

### You learn how to:
- Gather and structure application requirements before writing a single prompt.
- Translate a personal or professional need into a clear app specification.
- Apply iterative vibe coding techniques independently to an original problem.
- Make an informed choice about which AI coding tool best fits a given use case.

## Your Scenario

This lab has no pre-built scenario. That is the point.

Think about a tool that would genuinely make your work or personal life easier—a simple tracker, a form, a calculator, a dashboard, a scheduler, anything that solves a real problem you have. The best vibe coding projects start with a clear, personal motivation.

> [!NOTE]
> A good first app is small and focused. Resist the urge to build something ambitious. A well-scoped app you can finish in 30 minutes is far more valuable than a half-built complex one.

## Lab Instructions

### Task 1: Define your use case

Before writing a single prompt, you need a clear picture of what you are building and why. Well-defined requirements lead to better prompts and far fewer dead ends.

1. Take 5 minutes to brainstorm ideas. Think about repetitive tasks, manual processes, or information you frequently look up or track. Write down 3 to 5 rough ideas.

> [!NOTE]
> Good starting points: expense trackers, shift schedulers, personal habit trackers, simple inventory lists, quote or reference tools, meeting note templates, form builders, or anything you currently manage in a spreadsheet or on paper.

2. Pick your best idea. Write a **2 to 3-sentence description** of the app. Be specific about who uses it and what problem it solves. For example:

   > *"A personal reading tracker that lets me log books I'm reading, mark them as complete, and see how many I've finished this year. I want to quickly add books and view them in a clean, filterable list."*

3. Write a **feature list** of 5 to 8 items—specific things your app should be able to do. Keep each item to one sentence. For example:
   - Add a book with a title, author, and start date
   - Mark a book as "Reading", "Completed", or "Want to Read"
   - Display a count of books completed this year
   - Filter the list by status
   - Export the list as CSV

4. Review your feature list. Mark each item as either **core** (the app is not useful without it) or **nice-to-have** (useful, but not critical). You will build the core features in Task 3 and tackle the nice-to-haves in the Bonus Task.

> [!NOTE]
> If you are stuck for ideas, open a new chat in [Gemini](https://gemini.google.com/app) and describe your job or a daily frustration. Ask: *"What simple web app could I build to solve this?"* Use the suggestions as a starting point, then make the idea your own.

5. **Choose your tool.** Use this as a guide:
   - **Gemini Canvas**—best for self-contained, single-page apps built with plain HTML, CSS, and JavaScript. Great for dashboards, forms, and quick tools.
   - **Google AI Studio**—best for multi-page applications, or when you want a structured React/TypeScript project you can download and deploy.

> [!IMPORTANT]
> Write down your app description, feature list, and tool choice before moving on. You will paste this information directly into your first prompt in Task 2.

### Task 2: Design and generate the UI

With your requirements defined, you will now design the visual layout and generate the first version of the UI. Just like in the earlier labs, you will focus entirely on structure first—no logic yet.

1. Create a **wireframe sketch** of your app. It should include:
   - A header with the app name
   - The main content regions
   - Key input fields, buttons, and data display areas

   You have three options:
   - Draw it by hand on paper or a whiteboard and take a photo
   - Use any drawing tool on your computer
   - Ask Gemini to generate a wireframe sketch for you based on your description

> [!NOTE]
> The sketch does not need to be detailed or polished. Labeled boxes are enough. Its purpose is to give the AI a concrete structure to work from rather than making everything up.

2. Open your chosen tool:
   - **Canvas:** Open [Gemini](https://gemini.google.com/app), click the __+__ icon, and select **Canvas** from the __Tools__ list.
   - **AI Studio:** Open [Google AI Studio](https://aistudio.google.com/apps) and log in. Select the __Build__ menu on the left.

3. Paste your wireframe image into the prompt window. Then run a structured prompt similar to the one below, adapting it to your own app:

```text
You are a senior front-end developer.

Use the attached sketch to build the first version of this app's UI.

App description: [paste your 2-3 sentence description here]

Steps:
1. Build a clean, responsive layout using [HTML/CSS/JS | React and Tailwind CSS].
2. Match the sketch structure as closely as possible.
3. Include all the major UI regions: [list your main sections].
4. Keep the design simple, accessible, and readable.
5. Do not add any data logic or backend functionality yet. Build the visual layout only.

Output: Return only the code needed for the layout.
```

4. Review the generated UI. Ask yourself:
   - Does it include all the regions from my sketch?
   - Are the inputs and buttons clearly labeled?
   - Does the overall layout make sense for the use case?

5. Make targeted layout refinements—spacing, typography, card styling—through focused follow-up prompts. Do not add any features yet.

> [!NOTE]
> You should now have a clean, responsive UI shell. No functionality is required at this stage.

### Task 3: Program the features

With the UI in place, you will now add your core features one at a time. This is where vibe coding discipline matters most: **one feature per prompt, test before moving on.**

1. Look at your core feature list from Task 1. Order the features from simplest to most complex. Start with the one that is easiest to implement—usually the ability to add or display a piece of data.

2. Write a focused prompt for your first feature. Be specific about what it should do and what it should not touch. Follow the pattern below:

```text
Start with the existing application. Do not rewrite the whole thing.

Add the ability to [describe the feature clearly].
- [Specific behavior 1]
- [Specific behavior 2]

Do not add any other new features yet.
```

> [!IMPORTANT]
> Never ask for more than one new feature per prompt. If a prompt is too broad, the AI will make assumptions that silently break existing functionality. Add one thing, test it, then move on.

3. After each prompt completes, **test the feature thoroughly** before running the next prompt:
   - Does the new feature work as expected?
   - Did anything that was already working break?
   - If something is broken, ask the AI to fix that specific issue before continuing.

4. Work through your entire core feature list this way—one feature at a time—until all core features are implemented and tested.

> [!NOTE]
> It is completely normal for some prompts to produce imperfect results. Ask for specific, targeted fixes rather than asking the AI to start over.

### Bonus Task 4: Extend and refine

1. Add one or more of the nice-to-have features from your Task 1 list. Use the same one-feature-at-a-time approach from Task 3.

2. Polish the UI. Ask the AI to improve the visual design—spacing, typography, color consistency, hover effects—without changing any of the underlying logic.

3. Think about what would make this app genuinely production-ready. Consider adding one of the following:
   - **Data persistence** using `localStorage` so data survives a page refresh
   - **Export functionality**—a CSV download or a clipboard copy button
   - **A light/dark theme toggle**
   - **Mobile responsiveness** with a stacked layout on small screens

4. Share your app with a colleague or friend. Ask them to try to break it. Fix any issues they find.

## Congratulations!
In this lab, you have:
- Defined a real-world application from requirements through to a working product.
- Applied iterative vibe coding techniques independently to an original use case.
- Translated a personal or professional problem into a functional web application.
- Made deliberate, targeted prompting decisions to build features incrementally.
