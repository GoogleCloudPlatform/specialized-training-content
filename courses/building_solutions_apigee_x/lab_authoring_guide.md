## SCBL Authoring Guide

What follows is a step-by-step guide for creating a new Qwiklab in this repository. Tip: Browse the repository folders first and then follow this guide when you're ready to create your first lab.

## 1. Create a new branch for your lab

1. In your favorite terminal or [GitHub Desktop UI](https://desktop.github.com/)

1. Clone this repository

1. Git pull from main

1. Create a new [branch](https://guides.github.com/activities/hello-world/#branch)

Note: Don't work off the main branch!

## 2. Create a SCBL### folder for your lab

1. Inside the gcp-trainer-classroms/labs/ folder, create a new folder for your lab materials. Please copy the [scbl000-lab-template](https://github.com/CloudVLab/gcp-trainer-classroons/tree/master/labs/scbl000-lab-template) folder as a template/starting point. Each folder can only correspond to one lab.

1. Rename the folder based on the lab name. E.g. If the lab name is "Creating a Windows Virtual Machine", then an option is rename the folder as "scbl000-creating-windows-vm". A permanent number for the lab will be assigned before publication.
   
### Folder structure

Next, you will create the necessary folder structure and files for your new lab

1. Inside the folder you just created, you will need to create the below folder and file structure

scbl000-short-lab-name
 - instructions/
    - img/
    - en.md
 - terraform/
    - main.tf
    - variables.tf
    - outputs.tf
    - runtime.yaml 
 - QL_OWNER
 - qwiklabs.yaml

Note:
 - the `instructions/` sub-folder is where your actual lab markdown code will live in en.md
 - all lab images will be in `instructions/img/`
 - Terraform scripts to be run upon clicking "Start Lab" will be stored in the `terraform/` sub-folder. 
 - the `QL_OWNER` file (no extension) is the email address of the owner of the lab
 - the metadata for the lab (title, permissions, etc) is stored in `qwiklabs.yaml` which you will create next

Tip: Save time by copying the structure from an existing lab and changing to meet your needs rather than re-creating from scratch each time.

## 3. Create a qwiklabs.yaml file in your folder

Inside of the top level scbl### folder, create a blank file titled `qwiklabs.yaml`. This file will store critical descriptive and perrmission-related metadata about your lab. If you lab already has activity tracking, this file will also tell the engine where to find the activity tracking and testing scripts.

Example qwiklabs.yaml
```
---
schema_version: 2
default_locale: en
title: Text Classification with Model Garden
description: Model Garden provides easy access to models for many use cases. In this hands-on lab, 
  you'll learn to navigate Model Garden to find models suitable for natural language classification tasks.
duration: 120
max_duration: 120
credits: 1
level: introductory
tags: []
resources: []
environment:
  resources:
  - type: gcp_project
    id: project_0
    ssh_key_user: user_0
    startup_script:
      type: qwiklabs
      path: terraform
    allowed_locations:
    - us-central1-a
  - type: gcp_user
    id: user_0
    permissions:
    - project: project_0
      roles:
      - roles/editor
  student_visible_outputs:
  - label: Open Google Cloud console
    reference: project_0.console_url
  - label: Username
    reference: user_0.username
  - label: Password
    reference: user_0.password
  - label: GCP Project ID
    reference: project_0.project_id
```

Notes:
* It's critical the `title` is unique across all labs in all repositories to prevent one lab from overrwriting another
* Add metadata tags to your labs with the lab number
- scbl000
- course_name
- product(s) as individual tags

* Permission your lab with the least permissions needed to complete the lab to prevent abuse


## 4. Create the QL_OWNER file

Recently added as a feature, we can now associate labs with owners. Inside your lab folder, create a file titled `QL_OWNER` (no file extension) and list the owner of the lab. 

Example
```
# Lab owner
youremail@domain.com  # First Last
```

## 5. Create the lab instructions

1. If you haven't already, create a sub-folders titled `instructions/` and `instructions/img/` within your main lab folder.

1. Inside of `instructions/` create a markdown file titled `en.md` (en = english).

1. Follow the below markdown guide when authoring `en.md`

### Lab Guide Template - Markdown
For section-specific guidelines and examples, see Lab Guides: Design and Content Guidelines: go/lab-guide-guidelines

# Lab Title

## Overview
Write a brief summary of the lab.

Example:

In this lab, you create a virtual machine (VM) to host a typical application.  You configure persistent disk storage and firewall rules required to run the application.

In this lab, you run a Minecraft server on a Compute Engine instance. You use an n1-standard-1 machine type that includes a 10-GB boot disk, 1 virtual CPU (vCPU), and 3.75 GB of RAM. This machine type runs Debian Linux by default. To ensure that there is enough room for the  Minecraft server’s world data, you also attach a high performance 50-GB persistent solid-state drive (SSD) to the instance. This dedicated Minecraft server can support up to 50 players.

## Objectives
Describe objectives of the lab.

Example:

In this lab, you learn how to perform the following tasks:
* Create a Compute Engine instance with a persistent disk
* Configure network firewall rules
* Schedule regular backups
* Configure startup and shutdown scripts

## Task #. Task Title
Write a brief summary of what the learner will accomplish in this task.

### Sub-Task Title

1. Write the first step as a command.

    Here are a few optional words that explain the step. Here is the output from the step. Mention output if significant.

2. Write the second step as a command.

### Another Sub-Task Title
1. Write the first step.
2. Write the second step.
3. For __Name__, type __thisname__
4. For __Description__, type __description__ and click __Save__.

Code blocks start and end with ```

Example
1. To list available regions, execute the following command:

    ```
    gcloud compute regions list
    ```

If it’s necessary to display the actual output, format as a code block and add (do not copy).

Example

1. Verify the output (do not copy)

    ```
    Error starting adb shell. Activity not started.
    ```

### Fragments

What are they?
Fragments are extremely useful ways to not have to write the same repeatable instructions from lab to lab (and they ensure consistency across curriculum developers). Consider something like a generic “start qwiklabs” set of steps -- it’s easy to embed a pre-written fragment of a document into your own by simply importing it as shown below.

How do I embed them?
Pick a fragment from the /fragments folder in the root of the repo.

Each lab should have the following fragment for starting Qwiklabs:
```
![[/fragments/startqwiklab]]
```

And each lab should end with the following fragment for ending Qwiklabs:
```
![[/fragments/endqwiklab]]
```

### Tables

For tables, use Markdown tables instead of HTML tables. You can use this generator: https://www.tablesgenerator.com/markdown_tables

Here is an example:

```
| Instance name | Role |
|---|---|
| dc  | Active Directory domain controller  |
| dev  |  Development server |
| cluster-sql1  |  SQL Server instance (primary) |
| cluster-sql2  |  SQL Server instance |
| web |  Web server |
```

Renders as follows:

| Instance name | Role |
|---|---|
| dc  | Active Directory domain controller  |
| dev  |  Development server |
| cluster-sql1  |  SQL Server instance (primary) |
| cluster-sql2  |  SQL Server instance |
| web |  Web server |

### Info and Warning Boxes

To display a blue info box, use:
```
<ql-infobox>This is an info box.</ql-infobox>
```

To display a red warning box, use:
```
<ql-warningbox>This is a warning box.</ql-warningbox>
```

### Images

All resized icons are found in our gcs bucket here: gs://cloud-training/images

Images used across all labs (from the GCS bucket), should use this format:

```
![Navigation menu](https://storage.googleapis.com/cloud-training/images/menu.png "Navigation menu")
```

This renders like this: ![Navigation menu](https://storage.googleapis.com/cloud-training/images/menu.png "Navigation menu")

Here are more examples:
```
![Cloud Shell](https://storage.googleapis.com/cloud-training/images/devshell.png "Cloud Shell")
```

This renders like this: ![Cloud Shell](https://storage.googleapis.com/cloud-training/images/devshell.png "Cloud Shell")

```
![Cloud Shell Editor](https://storage.googleapis.com/cloud-training/images/cloud-shell-editor.png "Cloud Shell Editor")
```

This renders like this: ![Cloud Shell Editor](https://storage.googleapis.com/cloud-training/images/cloud-shell-editor.png "Cloud Shell Editor")

Each lab folder can have its own image folder. Use the ![[/img/imagename.png]] format to include it in your lab guide if you want to use your own images.

### Probes

Probes are single-question "quizzes" embedded in labs. They give the learner the ability to check their understanding in a low-stakes context as they learn the material. Probes are defined with custom HTML tags. Note that they will only render in QwikLabs - they will not be visible in any standard Markdown viewer, since they require special JS to render.

#### Multiple Choice:

Attribute | Type    | Required | Description
--------- | ------- | -------- | -----------
shuffle   | boolean | false    | Whether to shuffle the answer options each time the page is loaded.

Example:

```html
<ql-multiple-choice-probe shuffle>
  <ql-stem>Which is the best search engine?</ql-stem>
  <ql-option>DuckDuckGo</ql-option>
  <ql-option correct>AskJeeves</ql-option>
  <ql-option>Google Search</ql-option>
  <ql-option>Bing</ql-option>
</ql-multiple-choice-probe>
</section>
```

The `<ql-multiple-choice-probe>` element must contain:

- a single `<ql-stem>` element with the probe's question stem.
- one or more `<ql-option>` elements with the text of options the user can choose.
  - a single `<ql-option>` element must have the `correct` attribute.

#### Multiple Select:

Attribute | Type    | Required | Description
--------- | ------- | -------- | ---
shuffle   | boolean | false    | Whether to shuffle the answer options each time the page is loaded.

Example:

```html
<ql-multiple-select-probe shuffle>
    <ql-stem>Who are the greatest rappers of all time?</ql-stem>
    <ql-option correct>Nas</ql-option>
    <ql-option correct>Jay-Z</ql-option>
    <ql-option>Big Bird</ql-option>
    <ql-option correct>The Notorious B.I.G.</ql-option>
</ql-multiple-select-probe>
```

The `<ql-multiple-select-probe>` element must contain:

- a single `<ql-stem>` element with the probe's question stem.
- one or more `<ql-option>` elements with the text of options the user can choose.
  - any number of the `<ql-option>` elements can have the `correct` attribute.


#### True / False:

Attribute | Type    | Required | Description
--------- | ------- | -------- | ---
answer    | boolean | true     | The true/false answer - 'true' for true, otherwise false.

Example:

```html
<ql-true-false-probe answer="true">
  <ql-stem>Identity theft is not a joke.</ql-stem>
</ql-true-false-probe>
```

The `<ql-true-false-probe>` element must contain a single `<ql-stem>` element with the probe's question stem.

