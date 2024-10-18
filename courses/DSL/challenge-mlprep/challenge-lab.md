# DSL Challenge Lab: Preparing Data for ML Training and Serving Workflows

## Introduction

The data scientists at your company have successfully trained a prototype model for **INSERT USE CASE** using a representative data sample. However, in moving to production, they are running across multiple issues.

  1. The data preparation and feature engineering code is all written using the Pandas package in Jupyter notebooks. Though this works well for the sample data stored in a single CSV file, this approach does not scale to the entire dataset.
  2. The model training code is currently being manually executed by the data science team. In production, they want to be able to orchestrate feature engineering, model training, and model deployment in a more automated fashion.
  3. New training data will be added to a Cloud Storage bucket, but not at a regular cadence. The data science team wants to be able to retrain and deploy the model when new training is added to the bucket without manual intervention.
  4. The data science team wants to be able to easily share the training data and their prepared features with other teams, but some teams are not as familiar with the tools being used to process the data for training.
  5. The consumers of the model's predictions are unhappy with the time it takes for the model to generate predictions. This is adding latency to downstream applications and leading to negative customer experience.

You have been asked to use your knowledge of data engineering to design a solution for the data science team to address these issues.

## Understanding the data and code

## Task 1: Load the data into BigQuery and convert feature engineering code

Your task is to load the training data into BigQuery and to convert the feature engineering code into a more scalable solution. There are two tables spread across multiple CSV files. The sample data used by the data science team was created by joining a single CSV from each table using Pandas methods.

1. Import the training data into BigQuery as-is. 

2. Using the initial schema and transformations being performed as a starting point, create a new table with a schema which will be more performant for data transformation. Call this new table named `joined_for_transformation`.

3. Convert the Pandas transformation code into a more scalable solution using SQL in BigQuery. Store the results in a new table named `prepared_data`.

4. Create a single query to automate this entire process. This will be helpful later in the project as you start to automate other parts of the model training and serving.

## Task 2: Orchestrating model training and deployment

In this task, you use Cloud Composer to orchestrate feature engineering, model training, and model deployment in a more automated fashion. You will leverage the code provided by the data science team which has been packaged for training on Vertex AI.

1. Create a Cloud Composer instance for this task. You can use the console or the Google Cloud CLI, but doing this using Terraform for this task so that the provisioning process can easily be adapted for other projects.

2. Create an Airflow DAG to load data into BigQuery, transform the data for training, perform model training, and deploy the model.

3. Implement automated deployment of Airflow DAGs to Composer as the code is updated. You may want to consider using tools like Github and Cloud Build to aid with this.

4. Update your DAG to do the following:
   
  * Check when data in the source tables were last updated.
  * Run parallel training jobs with different hyperparameters.
  * Deploy only the model that performed the best to Vertex AI. 

## Task 3: Update Airflow DAG for continuous training

In this task, you update the DAG from the previous task to trigger automatically when new data is added to the Cloud Storage bucket containing the raw data. You know from the relevant teams that this data will not be added at a regular cadence, so you cannot simply schedule the pipeline to run at a regular interval

1. Update the pipeline to trigger only when new data is added to the Cloud Storage bucket where data is stored. Test this by adding **ADD FILE LOCATION/NAME** to the bucket aftet updating the DAG.

2. You want to ensure that only recent data is being used to train the model and often old data is added to the Cloud Storage bucket. Add a step in the Airflow DAG to stop the pipeline if the data is older than 60 days. 

3. Add operators to the DAG to email someone on your team when the training job has completed or if a pipeline run was stopped due to stale data. Include information about the model training job.

## Task 4: Create and manage a data mesh and a feature store

In this task, you will create a feature store using Vertex AI to ensure that features, including engineered features, are easy to share and access with low latency.

1. Using Dataplex, create a data mesh architecture to share your raw and transformed data with the data science team. The architecture has the following requirements:
- Zones for raw and curated data.
- The raw zone contains the original CSV data in Cloud Storage
- The BigQuery tables are in the curated zone.
- Add appropriate metadata to the curated datasets using Dataplex tags and tag templates.
- Enable data lineage to track changes to data over time.

2. Create a Feature Store on Vertex AI for your prepared training data. The [documentation] for Feature Store will be helpful for doing this.
  
3. The data science team has been wanting to update the model serving code to use Feature Store to lower latency for serving compared to querying BigQuery for the same data. Create an online feature store using **Optimized online serving from a public endpoint**. Name this feature store `online_serving_fs`.

## Task 5: Implement data transformation and model into a real-time streaming pipeline

In this task you will implement a streaming data pipeline using Apache Beam and Dataflow to serve streaming predictions on real-time data. A stream simulator is available for you using a Python script and Pub/Sub. However, as an additional challenge, you can try to set this up from scratch.

1. Start up the stream simulator on a small VM (say `e2-standard-2`) following the instructions [here](add-the.link)

2. Using the model artifact output from your training pipeline, create a streaming pipeline using Apache Beam with the following requirements.
- Ingest messages from the Pub/Sub topic used by the data generator
- A dead letter pattern should be implemented to prevent a bad message from stopping the pipeline.
- Parse messages into the format needed for model prediction, see [here](add-the.link) for hints if needed.
- Enrich the message by querying Feature Store
- Serve a prediction using the RunInference operator
- Write the predictions to a BigQuery table for later analysis
- If an anomaly is detected, also send an alert to the Pub/Sub topic called `fraud_alert`.

  
### Congratulations! 