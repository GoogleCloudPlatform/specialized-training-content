# DSL Challenge Lab: Prepating Data for ML Training and Serving Workflows

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
  a. Check when data in the source tables were last updated.
  b. Run parallel training jobs with different hyperparameters.
  c. Deploy only the model that performed the best to Vertex AI. 

## Task 3: Update Airflow DAG for continuous training

In this task, you update the DAG from the previous task to trigger automatically when new data is added to the Cloud Storage bucket containing the raw data. You know from the relevant teams that this data will not be added at a regular cadence, so you cannot simply schedule the pipeline to run at a regular interval

1. Update the pipeline to trigger only when new data is added to the Cloud Storage bucket where data is stored. Test this by adding **ADD FILE LOCATION/NAME** to the bucket aftet updating the DAG.

2. You want to ensure that only recent data is being used to train the model and often old data is added to the Cloud Storage bucket. Add a step in the Airflow DAG to stop the pipeline if the data is older than 60 days. 

3. Add operators to the DAG to email someone on your team when the training job has completed or if a pipeline run was stopped due to stale data. Include information about the model training job.

## Task 4: Create and manage a feature store


## Task 5: Implement data transformation and model into a real-time streaming pipeline\

  
### Congratulations! 
