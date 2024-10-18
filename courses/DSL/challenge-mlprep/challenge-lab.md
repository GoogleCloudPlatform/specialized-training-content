# DSL Challenge Lab: Preparing Data for ML Training and Serving Workflows

## Introduction

Your company has begun the process of scaling out their new mobile payment service to a broader user base, however there is a persistent concern of fraudulent transactions. Your support team is able to work with customers resolve these tickets when the fraudulent transaction slips past your current rules-based fraud detection system, but this is time-consuming for that team. The ultimate goal is to have a better AI-powered system for detecting fraudulent transactions to alleviate the pressure on the support team and improve customer experience.

The data scientists at your company have successfully trained a proof-of-concent model for detecting fraduluent transactions using a data sample provided by the team managing the relational database. However, the data scientists are concerned that the distribution of their data sample is not truly representative of all transactions occuring and wish to be able to train the model on a much larger dataset. Additionally, there are other issues that will have to be addressed before moving into production.

  1. The data preparation and feature engineering code is all written using the Pandas package in Jupyter notebooks. Though this works well for the sample data stored in a single CSV file, this approach does not scale to the entire dataset.
  2. The model training code is currently being manually executed by the data science team. In production, they want to be able to orchestrate feature engineering, model training, and model deployment in a more automated fashion.
  3. New training data will be added to a Cloud Storage bucket, but not at a regular cadence. The data science team wants to be able to retrain and deploy the model when new training is added to the bucket without manual intervention.
  4. The data science team wants to be able to easily share the training data and their prepared features with other teams, but some teams are not as familiar with the tools being used to process the data for training.
  5. The consumers of the model's predictions are unhappy with the time it takes for the model to generate predictions. This is adding latency to downstream applications and leading to negative customer experience.

You have been asked to use your knowledge of data engineering to design a solution for the data science team to address these issues.

## Understanding the data and code

Sample data is located in the following Cloud Storage location. You should copy this data to a bucket in your own Google Cloud project for the sake of this exercise. 

```
gs://cloud-training/specialized-training/dsl_data
```

There are 6 folders in this Cloud Storage location containing data. Each folder contains CSV files exported from a single table in the relational database that will need to be loaded into BigQuery throughout this project. The sole exception are the CSV files in the `sample_preproc_data` folder, which contains the prepared data sample that the data scientists used to work on the proof-of-concept model. The sample data has the following schema and it is what is expected by the data science team:

### Sample Data Schema

| **Field name**          | **Type**  | **Mode** | **Description**                                                                                   |
|-------------------------|-----------|----------|---------------------------------------------------------------------------------------------------|
| transactionId (PK)      | INTEGER   | REQUIRED | Unique Id for transaction                                                                         |
| step                    | INTEGER   | REQUIRED | Number of hours from beginning of data collection                                                 |
| action                  | STRING(8) | REQUIRED | Type of transaction, there are five possible values: PAYMENT, CASH_IN, CASH_OUT, DEBIT, TRANSFER. |
| amount | FLOAT | REQUIRED | Amount of transaction |
| idOrig (FK)             | STRING    | REQUIRED | UserId of user originating the transaction                                                        |
| oldBalanceOrig          | FLOAT     | REQUIRED | Balance of idOrig account before transaction                                                      |
| newBalanceOrig          | FLOAT     | REQUIRED | Balance of idOrig account after transaction                                                       |
| idDest (FK)             | STRING    | REQUIRED | UserId, BankId or MerchantId of destination for the transaction                                   |
| oldBalanceDest          | FLOAT     | NULLABLE | Balance of idDest account before transaction if relevant                                          |
| newBalanceDest          | FLOAT     | NULLABLE | Balance of idDest account after transaction if relevant                                           |
| isFraud | BOOLEAN | REQUIRED | Flag for fraudulent transactions |
| isFlaggedFraud | BOOLEAN | REQUIRED | Transactions marked as fraud by rule-based system. |
| isUnauthorizedOverdraft | BOOLEAN   | NULLABLE | Flag for unauthorized overdrafts if relevant                                                      |
| isSuccessful            | BOOLEAN   | REQUIRED | Flag for successful transactions                                                                  |

The schema for the other tables are as follows:

### Users

| **Field Name** | **Type** | **Mode** | **Description**                                           |
|----------------|----------|----------|-----------------------------------------------------------|
| userId (PK)    | STRING   | REQUIRED | The User ID of a User involved in a transaction           |
| first_name     | STRING   | REQUIRED | First name of the user, collected at account creation     |
| last_name      | STRING   | REQUIRED | Last name of the user, collected at account creation      |
| street_address | STRING   | REQUIRED | Street address of the user, collected at account creation |
| city           | STRING   | REQUIRED | City of the user, collected at account creation           |
| state          | STRING   | REQUIRED | State of the user, collected at account creation          |
| zip_code       | INTEGER  | REQUIRED | Zip code of the user, collected at account creation       |

### Merchants

| **Field Name** | **Type** | **Mode** | **Description**                                               |
|----------------|----------|----------|---------------------------------------------------------------|
| merchantId (PK)| STRING   | REQUIRED | The merchant ID of a merchant involved in a transaction       |
| company_name   | STRING   | REQUIRED | Name of merchant, collected at account creation               |
| contact_name   | STRING   | REQUIRED | Contact name for merchant, collected at account creation      |
| first_name     | STRING   | REQUIRED | First name of the merchant, collected at account creation     |
| last_name      | STRING   | REQUIRED | Last name of the merchant, collected at account creation      |
| street_address | STRING   | REQUIRED | Street address of the merchant, collected at account creation |
| city           | STRING   | REQUIRED | City of the merchant, collected at account creation           |
| state          | STRING   | REQUIRED | State of the merchant, collected at account creation          |
| zip_code       | INTEGER  | REQUIRED | Zip code of the merchant, collected at account creation       |

### Banks

| **Field Name** | **Type** | **Mode** | **Description**                                           |
|----------------|----------|----------|-----------------------------------------------------------|
| bankId (PK)    | STRING   | REQUIRED | The bank ID of a bank involved in a transaction           |
| bank_name      | STRING   | REQUIRED | Name of bank, collected at account creation               |
| contact_name   | STRING   | REQUIRED | Contact name for bank, collected at account creation      |
| first_name     | STRING   | REQUIRED | First name of the bank, collected at account creation     |
| last_name      | STRING   | REQUIRED | Last name of the bank, collected at account creation      |
| street_address | STRING   | REQUIRED | Street address of the bank, collected at account creation |
| city           | STRING   | REQUIRED | City of the bank, collected at account creation           |
| state          | STRING   | REQUIRED | State of the bank, collected at account creation          |
| zip_code       | INTEGER  | REQUIRED | Zip code of the bank, collected at account creation       |

### Transactions

| **Field name**          | **Type**  | **Mode** | **Description**                                                                                   |
|-------------------------|-----------|----------|---------------------------------------------------------------------------------------------------|
| transactionId (PK)      | INTEGER   | REQUIRED | Unique Id for transaction                                                                         |
| step                    | INTEGER   | REQUIRED | Number of hours from beginning of data collection                                                 |
| action                  | STRING(8) | REQUIRED | Type of transaction, there are five possible values: PAYMENT, CASH_IN, CASH_OUT, DEBIT, TRANSFER. |
| idOrig (FK)             | STRING    | REQUIRED | UserId of user originating the transaction                                                        |
| oldBalanceOrig          | FLOAT     | REQUIRED | Balance of idOrig account before transaction                                                      |
| newBalanceOrig          | FLOAT     | REQUIRED | Balance of idOrig account after transaction                                                       |
| idDest (FK)             | STRING    | REQUIRED | UserId, BankId or MerchantId of destination for the transaction                                   |
| oldBalanceDest          | FLOAT     | NULLABLE | Balance of idDest account before transaction if relevant                                          |
| newBalanceDest          | FLOAT     | NULLABLE | Balance of idDest account after transaction if relevant                                           |
| isUnauthorizedOverdraft | BOOLEAN   | NULLABLE | Flag for unauthorized overdrafts if relevant                                                      |
| isSuccessful            | BOOLEAN   | REQUIRED | Flag for successful transactions                                                                  |

### Fraud Transactions

| **Field name**          | **Type**  | **Mode** | **Description**                                                 |
|-------------------------|-----------|----------|-----------------------------------------------------------------|
| transactionId (PK)      | INTEGER   | REQUIRED | Unique Id for transaction                                       |
| step                    | INTEGER   | REQUIRED | Number of hours from beginning of data collection               |
| action                  | STRING(8) | REQUIRED | Type of transaction                                             |
| amount                  | FLOAT     | REQUIRED | Amount of the transaction                                       |
| idOrig (FK)             | STRING    | REQUIRED | UserId of user originating the transaction                      |
| idDest (FK)             | STRING    | REQUIRED | UserId, BankId or MerchantId of destination for the transaction |
| isFraud                 | BOOLEAN   | REQUIRED | Flag for fraudulent transactions                                |
| isFlaggedFraud          | BOOLEAN   | REQUIRED | Flag for transactions flagged as fraudulent                     |





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
