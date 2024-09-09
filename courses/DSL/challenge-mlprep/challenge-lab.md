# DSL Challenge Lab: Prepating Data for ML Training and Serving Workflows

## Introduction

The data scientists at your company have successfully trained a prototype model for **INSERT USE CASE** using a representative data sample. However, in moving to production, they are running across multiple issues.

  1. The data preparation and feature engineering code is all written using the Panda package in Jupyter notebooks. Though this works well for the sample data stored in a single CSV file, this approach does not scale to the entire dataset.
  2. The model training code is currently being manually executed by the data science team. In production, they want to be able to orchestrate feature engineering, model training, and model deployment in a more automated fashion.
  3. New training data will be added to a Cloud Storage bucket, but not at a regular cadence. The data science team wants to be able to retrain and deploy the model when new training is added to the bucket without manual intervention.
  4. The data science team wants to be able to easily share the training data and their prepared features with other teams, but some teams are not as familiar with the tools being used to process the data for training.
  5. The consumers of the model's predictions are unhappy with the time it takes for the model to generate predictions. This is adding latency to downstream applications and leading to negative customer experience.

You have been asked to use your knowledge of data engineering to design a solution for the data science team to address these issues.

## Understanding the data and code

## Task 1: Migrating the data to BigQuery

Your task is to not only migrate the data to BigQuery, but also to modify the schema so it is easy for analysts to query. You could simply run an import with the schema auto-detection flag enabled. While this would work, it would be difficult for most analysts to query the nested fields using SQL. 

1. Use the initial schema as a starting point. Redesign the data to be better optimized for a BigQuery data warehouse. Draw a diagram of your planned schema changes. 

2. Write a program to migrate the data into BigQuery. You can do this using Bash, Python, Java, or Dataform, but you need to write a program so it could be run repeatedly. You can use the BigQuery console to help, but the final results need to be code. Create a Dataflow Workbench instance and write the code in Jupyter Notebooks if you like. 

3. Using Looker Studio, create a dashboard that contains the following information: 
   1. Visits by Page
   2. Most Popular Items
   3. Sales by Category
   4. Visit by Device Type


## Task 2: Writing Dataflow batch pipelines

In this task, you use Apache Beam and Dataflow to run a batch processing pipeline to accomplish the same job as in the previous task. Read the data from Cloud Storage, parse it, and write it to BigQuery using a schema that is optimized for analytics. 

1. Using Apache Beam, create a pipeline to migrate the clickstream data to BigQuery in accordance with the schema you created earlier. Program the pipeline in a Jupyter Notebook. 

2. Once you have the pipeline tested, run it using Google Cloud Dataflow. 

## Task 3: Processing the data in real time

In this task, you use Google tools to process data in real time. The data is sent to a Pub/Sub topic. You program subscribers to process the messages as they arrive. 

1. Write a simulator that creates visits and posts them as messages to a Google Pub/Sub topic. Use variables to control the number of visits sent per minute and how long the simulator should run. You can program this any way you like. 

2. Create a push subscriber running in Cloud Run or Cloud Functions. Process the messages as they come in. Parse them, and write the data to BigQuery where it can be analyzed. In Looker Studio, create a simple report that shows clicks by page in real time. 

3. Do the same thing as the previous step, but program a pull subscriber. Deploy the program to a Compute Engine virtual machine. Use an instance group to set up autoscaling. Also, implement some kind of health check that you can use to ensure if the pull process is not running, the machine will be restarted. 

4. Write an Apache Beam pipeline with the following requirements:
   1. Write the raw data to files in Google Cloud Storage at regular intervals. 
   2. Parse the messages and write the data to BigQuery. 
   3. Calculate page views by minute. Create a dashboard that reports this information.
   4. Run the pipeline in Dataflow. 

5. You want to detect a potential denial of service attack. Create an Apache Beam pipeline that calculates page views per minute. Write this information to the Google Cloud logs. Create a log metric that reports this information in a Logging and Monitoring Dashboard. Next, create a log alert that triggers beyond some threshold. When the alert triggers, send yourself an email. 

6. Restart your Pub/Sub message simulator so enough messages are sent to trigger the alert. 

## Task 4: Using Google Cloud Composer to orchestrate data engineering tasks

In this task, you use Apache Airflow and Google Cloud Composer to automate a data engineering task. 

1. Create a Composer pipeline with the following requirements:
   1. When a file containing clickstream data is written to a Cloud Storage bucket, trigger the pipeline. 
   2. Run a Dataflow job that processes the file, parses the data, and writes it to BigQuery. 
   3. After the Dataflow job completes, send a message to Pub/Sub indicating the file was processed. 

2. Create a subscriber to the Pub/Sub topic that notifies you that the file was succesfully processed. 


## Task 5: Using Dataplex to share enterprise data

In this task, you use Google Cloud Dataplex to share your clickstream data with the organization. 

1. Using Dataplex, create a data mesh architecture to share your clickstream data with the organization. The architecture has the following requirements:
   1. Zones for raw and curated data. 
   2. The raw zone contains the original JSON data contining the clickstream events 
   3. The data should be automatically processed and written to BigQuery tables. The BigQuery tables are in the curated zone. 
   4. Share the data using Dataplex security. 
   5. Add appropriate metadata to the curated datasets using Dataplex tags and tag templates. 
   6. Enable data lineage to track changes to data over time.
  
### Congratulations! You built a data pipeline, migrated data that has been already collected in Cloud Storage, and stored it in BigQuery. You also built streaming data pipelines that performed analysis on the data in real-time and saved the results to Cloud Storage for raw data and BigQuery for processed data.
