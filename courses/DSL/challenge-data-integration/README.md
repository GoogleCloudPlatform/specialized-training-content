# Data Integration

## F-ATC Company Overview

![F-ATC Logo](images/logo.png)

Fictional Aircraft Tracking Company (F-ATC) is a leading provider of flight tracking data analytics, dedicated to enhancing the safety of civil aviation worldwide. With a team of experienced aviation professionals and data scientists, we leverage advanced technologies to analyze vast amounts of flight data, providing critical insights to airlines, airports, and regulatory authorities.

Our mission is to revolutionize the way flight tracking data is utilized, empowering our partners to make informed decisions, optimize operations, and mitigate potential risks. By harnessing the power of data, F-ATC is committed to ensuring the highest standards of safety and efficiency in the global aviation industry.

The flight data is collected through a network of ADS-B receivers, arbitrarily distributed and linked to compact, remote edge computing platforms. These platforms are designed for efficient data processing at the source. Each receiver within the network plays a crucial role in capturing real-time data from aircraft within its coverage area.

Due to the dynamic nature of air traffic, the volume of data generated can be substantial. In densely populated airspace, the system can handle an influx of over 2,000 messages per second, originating from more than 100 aircraft. To manage this high-velocity data stream, the messages are published to a Pub/Sub topic. This approach ensures that the data is readily available for consumption by various applications and services. Additionally, the data is backed up to a Google Cloud Storage bucket, providing a durable and reliable storage solution for long-term retention and analysis. A sample service is available here to visualize the real-time data.

The rough architecture of the system is shown below, with the existing infrastructure on the left and the challenges for you as the Visualization Analyst on the right.

![Architecture](images/Architecture.svg)

## Task 1

The critical challenges from a data engineering perspective, beyond the potentially dirty data, lie in the physical implementation of the system. In data engineering, it is preferred to have duplicate data rather than to lose data. However, this means that the system must be designed to tolerate duplicate data throughout the pipeline. Duplication may occur at:

Data duplication is a common challenge in data engineering. Duplication can occur at various stages of a data pipeline.

**Sources of Data Duplication**

- **Aircraft Data Transmission:** An aircraft might transmit the same data multiple times, potentially with identical generation timestamps.
- **Logger Data Reception:** The logger responsible for collecting data may record the reception of the same data more than once.
- **Logger Data Transmission to Pub/Sub:** The logger might also send the data to Pub/Sub multiple times.
- **Pub/Sub Message Delivery:** Pub/Sub can deliver the same message to each subscription more than once.
- **Data Ingestion Failures (Dataflow and BigQuery):** In certain failure scenarios, data ingested by Dataflow and BigQuery may be duplicated.

To manage these challenges effectively, you will need to design your system to tolerate duplicate data throughout the pipeline. Data engineers prioritize data availability over strict uniqueness, preferring to have duplicate data rather than data loss.

![Representation of Challenges](images/Challenges.svg)

In situations where data needs to be aggregated for each aircraft session, a session window is a suitable choice. Fixed time (tumbling) windows and sliding (hopping) windows are not appropriate for this type of aggregation.

### Session Window Considerations
When defining a session window, consider the following:

- **Window Duration and "Shadows":** A window that is too short may prematurely close an aircraft's session if it enters a "shadow." Shadows are untracked airspace sections, often caused by ground obstructions like buildings, particularly near landing/takeoff areas or at the maximum range of loggers.
- **Window Duration and Flight Separation:** A window that is too long might merge a previous flight with a current flight. To prevent this, the session duration should be shorter than the fastest turnaround time for commercial airliners, which is approximately 45 minutes.
- **Data Latency:** The session window's length directly impacts when data becomes available for analysis. Data is not emitted until after the final data point for that session is received. Consequently, a longer session window will result in a longer delay before the data is available.

### Handling Redundant Data from Logger Network Expansion
As the F-ATC logger network expands, you may receive data from each aircraft multiple times. This redundancy is beneficial, as it helps eliminate "shadows" and provides more comprehensive data coverage over a wider area. You will need to design your system to effectively process and manage this duplicated data to ensure accurate aggregation and analysis.

The image provided illustrates the airspace over London Heathrow, displaying various flight activities such as overflights, aircraft in holding patterns, aircraft on final approach, and aircraft taking off. This visual representation highlights the complex nature of air traffic data and the need for robust session windowing techniques.

![Snapshot of real data from ADS-B showing holding and appraoching aircraft](images/Realtime.png)

<!----
Todo

----

## Setup:
Terraform script to deploy databases and load data into the following sources:
SQL Server on Cloud SQL
Postgres on AlloyDB or Spanner
Document storage on Firestore?
Log data in Cloud Storage
Data to be statically stored in AWS S3 buckets and Azure Blob Storage buckets for the project. Will need to think about managing this data and billing
Terraform script to deploy a small VM for streaming simulated data to Pub/Sub and writing transactions to Cloud SQL and/or AlloyDB/Spanner.

---->

<!----
Initial request

Perform ETL on the consolidated batch data to transform the data into an appropriate form for the data warehouse. A specific use case will need to be defined for this to be viable.

---->

Data is being written to a Cloud Storage bucket at `gs://flightdata-demo`. This bucket contains sample aircraft metadata in the `flightdata-data` directory, and aircraft log data in the root directory.

You will need to create a Cloud Storage bucket to store the processed data. This bucket will hold the refined aircraft information after it has been transformed.

The data in the root directory adheres to the Base Station format and is structured as [standard CSV](http://woodair.net/sbs/article/barebones42_socket_data.htm). While CSV is common, its structure can be inconsistent, making it challenging to use. A sample of the data is shown below:

```csv
MSG,8,1,1,ABFDAF,1,2025/03/19,04:18:28.888,2025/03/19,04:18:28.926,,,,,,,,,,,,0
MSG,7,1,1,A3DC34,1,2025/03/19,04:18:28.891,2025/03/19,04:18:28.927,,8750,,,,,,,,,,
MSG,4,1,1,AC56BA,1,2025/03/19,04:18:28.892,2025/03/19,04:18:28.927,,,298,311,,,2880,,,,,0
MSG,4,1,1,ABFDAF,1,2025/03/19,04:18:28.898,2025/03/19,04:18:28.928,,,437,138,,,-2176,,,,,0
MSG,7,1,1,A1244D,1,2025/03/19,04:18:28.899,2025/03/19,04:18:28.929,,10950,,,,,,,,,,
MSG,5,1,1,A58C29,1,2025/03/19,04:18:28.911,2025/03/19,04:18:28.931,,10375,,,,,,,0,,0,
MSG,3,1,1,ABFDAF,1,2025/03/19,04:18:28.917,2025/03/19,04:18:28.932,,18475,,,33.32707,-117.68406,,,0,,0,0
MSG,3,1,1,A1244D,1,2025/03/19,04:18:28.920,2025/03/19,04:18:28.976,,10950,,,33.45039,-117.99933,,,0,,0,0
MSG,7,1,1,A2E09A,1,2025/03/19,04:18:28.928,2025/03/19,04:18:28.977,,38000,,,,,,,,,,
MSG,8,1,1,A4E146,1,2025/03/19,04:18:29.255,2025/03/19,04:18:29.306,,,,,,,,,,,,0
MSG,7,1,1,A3DC34,1,2025/03/19,04:18:29.265,2025/03/19,04:18:29.308,,8750,,,,,,,,,,
MSG,8,1,1,AD9EDC,1,2025/03/19,04:18:29.266,2025/03/19,04:18:29.309,,,,,,,,,,,,0
MSG,8,1,1,A58C29,1,2025/03/19,04:18:29.266,2025/03/19,04:18:29.309,,,,,,,,,,,,0
MSG,3,1,1,AC56BA,1,2025/03/19,04:18:29.277,2025/03/19,04:18:29.311,,22525,,,33.04674,-117.65885,,,0,,0,0
MSG,8,1,1,A451CF,1,2025/03/19,04:18:29.284,2025/03/19,04:18:29.312,,,,,,,,,,,,0
MSG,7,1,1,0C20F6,1,2025/03/19,04:18:29.288,2025/03/19,04:18:29.313,,33000,,,,,,,,,,
MSG,4,1,1,A2E09A,1,2025/03/19,04:18:29.319,2025/03/19,04:18:29.362,,,371,320,,,-64,,,,,0
MSG,3,1,1,ABFDAF,1,2025/03/19,04:18:29.326,2025/03/19,04:18:29.363,,18450,,,33.32648,-117.68340,,,0,,0,0
MSG,5,1,1,A451CF,1,2025/03/19,04:18:29.331,2025/03/19,04:18:29.364,,37025,,,,,,,0,,0,
MSG,8,1,1,AA630B,1,2025/03/19,04:18:29.343,2025/03/19,04:18:29.366,,,,,,,,,,,,0
MSG,7,1,1,A3DC34,1,2025/03/19,04:18:29.346,2025/03/19,04:18:29.367,,8750,,,,,,,,,,
MSG,4,1,1,A3DC34,1,2025/03/19,04:18:29.370,2025/03/19,04:18:29.415,,,277,263,,,-256,,,,,0
MSG,3,1,1,0D0A21,1,2025/03/19,04:18:29.375,2025/03/19,04:18:29.416,,14650,,,33.60022,-117.14027,,,0,,0,0
```

This information describes characteristics of the incoming data. You will need to process messages in `MSG` format. Dates are not in [ISO 8601](https://www.iso.org/iso-8601-date-and-time-format.html) format, and there are distinct message generation and message logged timestamps. You will also need to handle numerous blank strings by storing them as null values.

The files in Cloud Storage are updated frequently, either every 10 minutes or upon reaching 10.24 MB, whichever occurs first. You will need to create a database connection for this process.

### Step 1 Understanding the data

Set up an [event sync](https://cloud.google.com/storage-transfer/docs/event-driven-transfers) to replicate data from the source bucket into a bucket in your project. The change data is currently published to this topic `projects/paul-leroy/topics/flightdata-gcs-eventstream`, which you can subscribe to in your project. You will also need to check that the data transfer service API is enabled and that the data transfer service account has consume access on Pub/Sub, Bucket Viewer and Object Admin roles on your bucket. BigQuery DTS requires that the data source and BigQuery Dataset are in the same region so be cognizant of this as BigQuery will be unable to load data from other regions outside the dataset region. A daily sync is also acceptable, you can use the following template to decide on mechanisms:

Configure event synchronization to replicate data from a source bucket into a bucket within your Google Cloud project.

1. **Enable the Data Transfer Service API**

    Ensure that the Data Transfer Service API is enabled in your Google Cloud project.

1. **Verify Data Transfer Service Account Permissions**

    Confirm that the Data Transfer Service account possesses the following Identity and Access Management (IAM) roles:

    - Pub/Sub Subscriber
    - Storage Object Viewer
    - Storage Object Admin

    These roles are necessary for the service account to consume data from Pub/Sub and administer objects within your bucket.

1. **Consider Regional Consistency for BigQuery Data Transfer Service (DTS)**
    
    For BigQuery DTS, the data source and the BigQuery dataset must reside in the same region. BigQuery cannot load data from regions outside of the dataset's specified region. This is an important consideration for data transfer operations.

1. **Subscribe to the Pub/Sub Topic**

    The change data is published to the Pub/Sub topic projects/paul-leroy/topics/flightdata-gcs-eventstream. You will need to subscribe to this topic within your project to receive data change notifications.

1. **Determine Data Transfer Frequency**

    A daily synchronization is acceptable given the data characteristics:

    - Data Volume: Approximately 5 GB per day.
    - Data Velocity: Roughly 3 MB per minute.
    - Reporting Frequency: Once per day, which is the primary factor determining the synchronization schedule.

### Step 2 Choose a method for data loading

You will need to make the table visible in BigQuery. This can be achieved by either using Data Transfer Service ([DTS](https://cloud.google.com/bigquery/docs/dts-introduction)) to schedule data loads or by utilizing [object tables](https://cloud.google.com/bigquery/docs/biglake-intro).

Consider the following sample table structure:

| MT  | TT | SID | AID | Hex    | FID | DMG         | TMG      | DML         | TML      | CS     | Alt  | GS   | Trk  | Lat  | Lng  | VR   | Sq   | Alrt | Emer | SPI | Gnd |
|-----|----|-----|-----|--------|-----|-------------|----------|-------------|----------|--------|------|------|------|------|------|------|------|------|------|-----|-----|
| MSG | 1  | 1   | 1   | 06A124 | 1   | 2025/03/10  | 0:22:59  | 2025/03/10  | 0:22:59  | QTR99Y | null | null | null | null | null | null | null | null | null | null| 0   |
| MSG | 1  | 1   | 1   | 0D07A8 | 1   | 2025/03/10  | 12:22:09 | 2025/03/10  | 12:22:09 | VOI3180| null | null | null | null | null | null | null | null | null | null| 0   |
| MSG | 1  | 1   | 1   | 0C210D | 1   | 2025/03/10  | 9:43:30  | 2025/03/10  | 9:43:30  | CMP473 | null | null | null | null | null | null | null | null | null | null| 0   |
| MSG | 1  | 1   | 1   | 0C210D | 1   | 2025/03/10  | 9:44:35  | 2025/03/10  | 9:44:35  | CMP473 | null | null | null | null | null | null | null | null | null | null| 0   |
| MSG | 1  | 1   | 1   | 0C210D | 1   | 2025/03/10  | 9:45:30  | 2025/03/10  | 9:45:30  | CMP473 | null | null | null | null | null | null | null | null | null | null| 0   |
| MSG | 1  | 1   | 1   | 0C210D | 1   | 2025/03/10  | 9:44:30  | 2025/03/10  | 9:44:30  | CMP473 | null | null | null | null | null | null | null | null | null | null| 0   |
| MSG | 1  | 1   | 1   | 06A124 | 1   | 2025/03/10  | 0:20:25  | 2025/03/10  | 0:20:25  | QTR99Y | null | null | null | null | null | null | null | null | null | null| 0   |
| MSG | 1  | 1   | 1   | 0C210D | 1   | 2025/03/10  | 9:46:26  | 2025/03/10  | 9:46:26  | CMP473 | null | null | null | null | null | null | null | null | null | null| 0   |
| MSG | 1  | 1   | 1   | 06A124 | 1   | 2025/03/10  | 0:23:29  | 2025/03/10  | 0:23:29  | QTR99Y | null | null | null | null | null | null | null | null | null | null| 0   |
| MSG | 1  | 1   | 1   | 06A19F | 1   | 2025/03/10  | 8:29:02  | 2025/03/10  | 8:29:02  | QTR56Y | null | null | null | null | null | null | null | null | null | null| 0   |

### Step 3 Clean and de-duplicate the data

You will need to clean the data using SQL. The dates in the provided sample are unformatted and contain additional characters, making them difficult to use. You can use the `CAST` and `SAFE_CAST` functions to convert the data types, and you will need to utilize BigQuery's [date functions](https://cloud.google.com/bigquery/docs/reference/standard-sql/date_functions) to properly format these date fields.

You should also implement a method to de-duplicate any data that may originate from multiple loggers. This will help ensure data accuracy and consistency.

You can implement these cleaning and de-duplication processes within a [view](https://cloud.google.com/bigquery/docs/views) or a [materialized view](https://cloud.google.com/bigquery/docs/materialized-views-intro) in BigQuery.

If your queries encounter errors related to column mismatches, it indicates issues with the incoming data. You will need to delete the offending file from the bucket; this will be addressed later using Dataflow.

| Row | MT  | TT | SID | AID | Hex    | FID | MG                  |  CS     | Alt  | GS   | Trk  | Geom | VR   | Sq   | Alrt | Emer | SPI | Gnd |
|---|-----|----|-----|-----|--------|-----|---------------------|--------|------|------|------|------|------|------|------|------|-----|-----|
| 1 | MSG | 1  | 1   | 1   | 06A124 | 1   | 2025-03-10T00:22:59 | QTR99Y | null | null | null | null | null | null | null | null | null| 0   |
| 2 | MSG | 1  | 1   | 1   | 0D07A8 | 1   | 2025-03-10T12:22:09 | VOI3180| null | null | null | null | null | null | null | null | null| 0   |
| 3 | MSG | 1  | 1   | 1   | 0C210D | 1   | 2025-03-10T09:43:30 | CMP473 | null | null | null | null | null | null | null | null | null| 0   |
| 4 | MSG | 1  | 1   | 1   | 0C210D | 1   | 2025-03-10T09:44:35 | CMP473 | null | null | null | null | null | null | null | null | null| 0   |
| 5 | MSG | 1  | 1   | 1   | 0C210D | 1   | 2025-03-10T09:45:30 | CMP473 | null | null | null | null | null | null | null | null | null| 0   |
| 6 | MSG | 1  | 1   | 1   | 0C210D | 1   | 2025-03-10T09:44:30 | CMP473 | null | null | null | null | null | null | null | null | null| 0   |
| 7 | MSG | 1  | 1   | 1   | 06A124 | 1   | 2025-03-10T00:20:25 | QTR99Y | null | null | null | null | null | null | null | null | null| 0   |
| 8 | MSG | 1  | 1   | 1   | 0C210D | 1   | 2025-03-10T09:46:26 | CMP473 | null | null | null | null | null | null | null | null | null| 0   |
| 9 | MSG | 1  | 1   | 1   | 06A124 | 1   | 2025-03-10T00:23:29 | QTR99Y | null | null | null | null | null | null | null | null | null| 0   |
| 10 | MSG | 1  | 1   | 1   | 06A19F | 1   | 2025-03-10T08:29:02 | QTR56Y | null | null | null | null | null | null | null | null | null| 0   |

### Step 4 Handle duplicate rows and remove irrelevant fields
You will need to address duplicate rows that may arise from overlapping receivers. While the generation date/time and data will be consistent across these duplicates, the logged date/time may vary depending on the specific logger that received the data. The granularity of this logging time is not sufficient for precise triangulation of aircraft, so you can decide how to best manage this field.

The `AID`, `FID`, and `SID` fields from the remote devices are currently misconfigured and do not provide relevant data or insight. You should remove these fields from your dataset.

Consider the following example of the cleaned data, where `MT`, `TT`, `Hex`, `MG`, `CS`, `Alt`, `GS`, `Trk`, `Geom`, `VR`, `Sq`, `Alrt`, `Emer`, `SPI`, and `Gnd` represent various data fields:

| Row | MT  | TT |  Hex    | MG                  |  CS     | Alt  | GS   | Trk  | Geom | VR   | Sq   | Alrt | Emer | SPI | Gnd |
|-----|-----|----|---------|---------------------|---------|------|------|------|------|------|------|------|------|-----|-----|
| 1  | MSG | 1  | 06A124 | 2025-03-10T00:22:59 | QTR99Y | null | null | null | null | null | null | null | null | null| 0   |
| 2  | MSG | 1  | 0D07A8 | 2025-03-10T12:22:09 | VOI3180| null | null | null | null | null | null | null | null | null| 0   |
| 3  | MSG | 1  | 0C210D | 2025-03-10T09:43:30 | CMP473 | null | null | null | null | null | null | null | null | null| 0   |
| 4  | MSG | 1  | 0C210D | 2025-03-10T09:44:35 | CMP473 | null | null | null | null | null | null | null | null | null| 0   |
| 5  | MSG | 1  | 0C210D | 2025-03-10T09:45:30 | CMP473 | null | null | null | null | null | null | null | null | null| 0   |
| 6  | MSG | 1  | 0C210D | 2025-03-10T09:44:30 | CMP473 | null | null | null | null | null | null | null | null | null| 0   |
| 7  | MSG | 1  | 06A124 | 2025-03-10T00:20:25 | QTR99Y | null | null | null | null | null | null | null | null | null| 0   |
| 8  | MSG | 1  | 0C210D | 2025-03-10T09:46:26 | CMP473 | null | null | null | null | null | null | null | null | null| 0   |
| 9  | MSG | 1  | 06A124 | 2025-03-10T00:23:29 | QTR99Y | null | null | null | null | null | null | null | null | null| 0   |
| 10 | MSG | 1  | 06A19F | 2025-03-10T08:29:02 | QTR56Y | null | null | null | null | null | null | null | null | null| 0   |


## Task 2. Transition to a Dataflow-oriented ETL Process
This task involves transitioning from a BigQuery-oriented ELT process to a Dataflow-oriented ETL process. This change enables data transformation during the loading phase, which facilitates the conversion of date/time fields into `datetime` or `timestamp` types upon loading.

### Step 1. Develop a Dataflow Job for BigQuery Data Loading
You will need to create a Dataflow job to load data into BigQuery from Cloud Storage. Utilizing [Workbenches](https://cloud.google.com/dataflow/docs/guides/interactive-pipeline-development) can expedite the development process for this job.

### Step 2. Implement Data Validation and Transformation
The data should be validated against a regular expression to ensure its structure conforms to the required input. This validation helps to address instances where inconsistent data is written into Cloud Storage, which might impact the data view in BigQuery. Dates and times can be combined into a single field, which you can then use for data partitioning. Empty fields within the `CSV` should be converted into null values. You can also use Geography data types for the `Latitude` and `Longitude` data.

### Step 3. Handle Non-conforming Data
If data does not match the regular expression, it should be written to a separate Cloud Storage bucket for review. This allows for evaluation of whether the data can be salvaged through improved ETL processes or if it can be safely discarded.

### Step 4. Remove Duplicate Data
Duplicate data, such as messages from a single aircraft received by two loggers, will require removal.

<!----
Initial request

Consolidate data from transactional databases and object storage into a single location. This will mean using BigQuery or Spanner for the transactional data and Cloud Storage for object storage. Students should explore tools like DTS and connections in BigQuery for performing this task. The goal here is not to fully analyze the data, but rather to just get everything into one place before further ETL

---->

## Task 3. Orchestrate the Data Pipeline
This task involves orchestrating the previously developed data pipeline to enable daily batch processing. The goal is to trigger the pipeline to move the previous day's data into the data warehouse.

### Step 1. Create a Dataflow Template for Scheduled Execution
You will need to create either a [dataflow template](https://cloud.google.com/dataflow/docs/concepts/dataflow-templates) or a [dataflow flex template](https://cloud.google.com/dataflow/docs/guides/templates/using-flex-templates#python) from your pipeline. This template will allow the pipeline to be parameterized and invoked periodically. You can choose to call this template from [Cloud Composer](https://cloud.google.com/composer/docs/composer-3/composer-overview) or [Cloud Scheduler](https://cloud.google.com/scheduler/docs).

For this project, using Cloud Scheduler may be more cost-effective. In a production environment, Cloud Composer offers advantages for managing multiple pipelines and scaling across various teams. A quickstart guide for building templates can be found  [here](https://cloud.google.com/dataflow/docs/guides/templates/using-flex-templates).

<!----
Initial request

Orchestrate the first two tasks via an orchestration tool such as Composer or Data Fusion. Ideally Composer here unless students want to go the Data Fusion route.

---->

## Task 4. Process Streaming Data with Pub/Sub and Dataflow

The Data Capture team has upgraded data collection to use Pub/Sub, enabling near real-time data analytics. You will explore this streaming data and write a Dataflow pipeline to parse the data and store it in BigQuery, ensuring data validity.

### Step 1. Ingest Data from Pub/Sub
The data structure remains consistent, but the data source is now an API rather than a Google Cloud Storage bucket. Your initial Dataflow step will need to be compatible with both Google Cloud Storage and Pub/Sub for batch and stream processing. The data is available on the Pub/Sub topic `projects/paul-leroy/topics/flight-transponder`. You will need to create a subscription in your project, or you can dynamically create the subscription when your pipeline starts. This is an implicit feature when using the PubsubIO handler to read from a topic.

### Step 2. Structure Data for Analysis
You now have access to a continuous stream of data. The next step involves restructuring this data to enable nesting of data per session. A session is defined as the period from when an aircraft is first detected to when it is last detected. For visualization purposes, the key fields are the Timestamp/DateTime, the aircraft's `ICAO24` identifier, altitude, and location (latitude and longitude). Aircraft may remain airborne past midnight, so the session logic should accommodate flights that span multiple days.

An example of the data structure, with chronological ordering, is provided below:

<!----
Initial request

Now visit streaming data via Pub/Sub and Dataflow. Explore the data (that has been written to a sink in GCS) and write a pipeline to properly parse the data and store it in BigQuery. Ensure that the data is valid.

---->

| Hex | SessionStart | Session.MG                     | Session.CS                     | Session.Alt | Session.GS | Session.Trk | Session.pt | Session.VR                 | Session.Sq | Session.Alrt | Session.Emer | Session.SPI | Session.Gnd |      |
| :-: | :----------: | :----------------------------: | :----------------------------: | :---------: | :--------: | :---------: | :--------: | :------------------------: | :--------: | :----------: | :----------: | :---------: | :---------: | :--: |
| 1   | 10207        | 2025-04-12 17:44:48.104000 UTC | 2025-04-12 18:44:48.104000 UTC | null        | null       | 182         | 247        | null                       | \-832      | null         | null         | null        | null        | 0    |
|     |              |                                | 2025-04-12 18:44:51.214000 UTC | null        | null       | 182         | 251        | null                       | \-768      | null         | null         | null        | null        | 0    |
|     |              |                                | 2025-04-12 18:44:51.961000 UTC | null        | 4450       | null        | null       | null                       | null       | null         | null         | null        | null        | null |
|     |              |                                | 2025-04-12 18:45:01.336000 UTC | null        | 4325       | null        | null       | null                       | null       | null         | null         | null        | null        | null |
| 2   | 10207        | 2025-04-12 17:46:29.147000 UTC | 2025-04-12 18:46:29.147000 UTC | null        | 3250       | null        | null       | null                       | null       | null         | null         | null        | null        | null |
|     |              |                                | 2025-04-12 18:46:58.448000 UTC | null        | null       | null        | null       | null                       | null       | 3564         | 0            | 0           | 0           | null |
|     |              |                                | 2025-04-12 18:47:47.082000 UTC | null        | 2150       | null        | null       | null                       | null       | null         | null         | null        | null        | null |
|     |              |                                | 2025-04-12 18:48:08.995000 UTC | null        | 1825       | null        | null       | null                       | null       | null         | null         | null        | null        | null |
| 3   | 0C218D       | 2025-04-12 17:50:49.803000 UTC | 2025-04-12 18:50:49.803000 UTC | null        | null       | 387         | 138        | null                       | 1728       | null         | null         | null        | null        | 0    |
|     |              |                                | 2025-04-12 18:50:56.118000 UTC | null        | 19775      | null        | null       | POINT(-117.89815 33.38121) | null       | null         | 0            | null        | 0           | 0    |
|     |              |                                | 2025-04-12 18:51:02.443000 UTC | null        | null       | 388         | 138        | null                       | 1728       | null         | null         | null        | null        | 0    |
|     |              |                                | 2025-04-12 18:51:06.314000 UTC | null        | 20050      | null        | null       | null                       | null       | null         | null         | null        | null        | null |
|     |              |                                | 2025-04-12 18:51:52.153000 UTC | null        | 21425      | null        | null       | null                       | null       | null         | null         | null        | null        | null |
|     |              |                                | 2025-04-12 18:51:59.474000 UTC | null        | 21625      | null        | null       | null                       | null       | null         | null         | null        | null        | null |
|     |              |                                | 2025-04-12 18:52:29.424000 UTC | null        | 22450      | null        | null       | null                       | null       | null         | null         | null        | null        | null |
| 4   | 0C218D       | 2025-04-12 17:53:55.736000 UTC | 2025-04-12 18:53:55.736000 UTC | null        | 24075      | null        | null       | POINT(-117.62092 33.1485)  | null       | null         | 0            | null        | 0           | 0    |
|     |              |                                | 2025-04-12 18:54:03.511000 UTC | null        | null       | 442         | 109        | null                       | 1344       | null         | null         | null        | null        | 0    |
| 5   | 0D0D92       | 2025-04-12 17:52:53.787000 UTC | 2025-04-12 18:52:53.787000 UTC | null        | null       | 329         | 279        | null                       | 0          | null         | null         | null        | null        | 0    |
|     |              |                                | 2025-04-12 18:53:22.777000 UTC | null        | 13950      | null        | null       | POINT(-117.36661 33.23584) | null       | null         | 0            | null        | 0           | 0    |
|     |              |                                | 2025-04-12 18:53:38.772000 UTC | null        | null       | 330         | 281        | null                       | 0          | null         | null         | null        | null        | 0    |
|     |              |                                | 2025-04-12 18:53:45.170000 UTC | null        | 13950      | null        | null       | null                       | null       | null         | null         | null        | null        | null |
|     |              |                                | 2025-04-12 18:53:49.552000 UTC | null        | null       | 330         | 281        | null                       | 0          | null         | null         | null        | null        | 0    |

## Task 5


In this task, you will be responsible for loading data from an external website into a Cloud SQL instance. This data will then be synchronized with BigQuery, enabling you to join it with the existing ADS-B data for comprehensive analysis. The primary goal is to integrate aircraft metadata from the OpenSky Network with the real-time flight data you've been working with.

### Step 1

**Provision a Cloud SQL PostgreSQL Instance**

Your first step is to set up a Cloud SQL PostgreSQL instance. This instance will serve as the initial repository for the aircraft metadata you'll be downloading.

**Instance configuration:**

*   **Region selection:** Choose a region that aligns with your project's requirements. Consider factors such as proximity to other resources and data residency needs.
*   **Instance type:** For this task, a sandbox instance is sufficient. You don't need a high-performance or production-grade instance. A small, cost-effective instance will suffice.
*   **Database version:** Select a supported PostgreSQL version. Ensure it's compatible with any tools or libraries you plan to use.
*   **Storage:** Allocate enough storage for the aircraft metadata. Since this is a sandbox instance, you can start with a minimal amount and scale up if needed.
*   **Connectivity:** Configure the instance for appropriate network access. You might need to allow connections from your local machine or other Google Cloud services.
*   **Security:** Set up strong credentials for the database user. Follow best practices for password management.

**Purpose:**

This Cloud SQL instance will act as a staging area for the OpenSky Network data. It will allow you to:

*   Store the data in a structured, relational format.
*   Perform initial data validation and transformation.
*   Prepare the data for synchronization with BigQuery.

**Considerations:**

*   **Cost:** Keep an eye on the cost of the instance. Since it's a sandbox, you can use a smaller instance type to minimize expenses.
*   **Scalability:** While you don't need to worry about scaling for this task, it's good to be aware of the scalability options available in Cloud SQL.
*   **Maintenance:** Be aware of any maintenance windows or updates that might affect the instance.

By carefully provisioning your Cloud SQL instance, you'll lay the groundwork for a successful data integration process.

### Step 2 

Download data from this [site](https://opensky-network.org/datasets/#metadata/), pick one of the files, preferrably last months one, and import it into a PostgreSQL Cloud SQL instance. 
The data use citation is [here](https://opensky-network.org/data/aircraft), make sure you add it to your dashboard.

### Step 3

Import the downloaded data into the Cloud SQL instance. This step requires careful consideration of the data schema to ensure that the columns are parsed correctly. The data from the OpenSky Network is provided in a CSV format, which is relatively straightforward to import into a relational database like PostgreSQL. However, you will need to define the table schema in PostgreSQL to match the structure of the CSV data.

Here are some key considerations for this step:

1.  **Schema definition**: Before importing, define the table schema in your PostgreSQL instance. This includes specifying the column names, data types (e.g., TEXT, INTEGER, REAL, TIMESTAMP), and any constraints (e.g., NOT NULL, PRIMARY KEY). The schema should accurately reflect the structure of the OpenSky Network data.
2.  **Data type mapping**: Ensure that the data types in your PostgreSQL schema are compatible with the data types in the CSV file. For example, numeric values should be mapped to INTEGER or REAL, and date/time values should be mapped to TIMESTAMP.
3.  **CSV import**: Use PostgreSQL's `COPY` command or a graphical tool like pgAdmin to import the CSV data into the defined table. The `COPY` command is efficient for large datasets and allows you to specify delimiters, null values, and other formatting options.
4.  **Data validation**: After importing, perform data validation to ensure that the data has been imported correctly. This can involve running SQL queries to check for data integrity, completeness, and accuracy.
5.  **Error handling**: Be prepared to handle potential errors during the import process. This might include data type mismatches, constraint violations, or formatting issues. You may need to clean or transform the data before importing it.
6.  **Indexing**: Consider adding indexes to columns that will be frequently used in queries. This can significantly improve query performance, especially for large datasets.
7. **Citation**: Make sure you add the citation to your dashboard as per the instructions.

By carefully planning and executing the data import process, you can ensure that the OpenSky Network data is accurately and efficiently stored in your Cloud SQL instance.

### Step 4 

Now that you have the aircraft metadata loaded into your Cloud SQL instance, the next step is to synchronize this data with BigQuery. This will allow you to join the metadata with the ADS-B data you've been working with, creating a richer dataset for analysis. To achieve this, you'll use Google Cloud Datastream, a serverless change data capture (CDC) and replication service.

Datastream will act as the bridge between your Cloud SQL instance and BigQuery. It will:

*   Capture changes in the Cloud SQL database (inserts, updates, deletes).
*   Transform these changes into a format suitable for BigQuery.
*   Stream the changes to BigQuery in near real-time.

Here's a breakdown of the steps and considerations:

1.  **Datastream configuration**: In the Google Cloud console, navigate to Datastream and create a new stream. You'll need to configure the source connection (your Cloud SQL instance) and the destination connection (BigQuery).
2.  **Source connection**: Provide the necessary credentials and connection details for your Cloud SQL instance. Datastream will use these to connect to the database and capture changes.
3.  **Destination connection**: Specify the BigQuery dataset where you want the data to be replicated. Datastream will create tables in this dataset that mirror the structure of your PostgreSQL tables.
4.  **Table selection**: Choose the specific table(s) in your PostgreSQL instance that you want to replicate. You can replicate entire tables or select specific columns.
5.  **Data replication**: Once configured, Datastream will start replicating data from your Cloud SQL instance to BigQuery. It will capture both initial data and ongoing changes (inserts, updates, deletes).
6.  **Data synchronization**: Datastream ensures that the data in BigQuery is kept in sync with the data in Cloud SQL. This is done through a process called Change Data Capture (CDC), which captures and replicates changes in real-time.

By setting up Datastream, you'll establish a robust and efficient pipeline for synchronizing your aircraft metadata with BigQuery, enabling powerful data analysis and visualization capabilities.


## Step 5

Validate that the data is loaded into BigQuery. You can run this query to check the data has been loaded. 

```sql
WITH
  t1 AS (
  SELECT
    LOWER(icao24) AS icao24,
    manufacturericao,
    MODEL
  FROM
    public.aircraft_metadata ),
  t2 AS (
  SELECT
    DISTINCT LOWER(Hex) AS icao24
  FROM
    flight_data.test_3 )
SELECT
  manufacturericao,
  MODEL,
  COUNT(*) AS planes
FROM
  t1
JOIN
  t2
USING
  (icao24)
GROUP BY
  ALL
ORDER BY
  planes desc
```
<!----
Initial request

Implement CDC on the transactional data using a product such as Datastream. Incorporate this into your DE workload.

---->

Aircraft Data Sourced from:
> Matthias Schäfer, Martin Strohmeier, Vincent Lenders, Ivan Martinovic, and Matthias Wilhelm.
> "Bringing Up OpenSky: A Large-scale ADS-B Sensor Network for Research".
> In Proceedings of the 13th IEEE/ACM International Symposium on Information Processing in Sensor Networks (IPSN), pages 83-94, April 2014.