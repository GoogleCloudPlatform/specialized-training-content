# Data Integration

## F-ATC Company Overview

![F-ATC Logo](images/logo.png)

Fictional Aircraft Tracking Company is a leading provider of flight tracking data analytics, dedicated to enhancing the safety of civil aviation worldwide. With a team of experienced aviation professionals and data scientists, we leverage advanced technologies to analyze vast amounts of flight data, providing critical insights to airlines, airports, and regulatory authorities.


Our mission is to revolutionize the way flight tracking data is utilized, empowering our partners to make informed decisions, optimize operations, and mitigate potential risks. By harnessing the power of data, Fictional Aircraft Tracking Company is committed to ensuring the highest standards of safety and efficiency in the global aviation industry.


The flight data is gathered from a distributed network of ADS-B receivers connected to small remote publishing edge compute platforms. These send all data received to pubsub. There are multiple sensors in each region. The busiest airspaces can have more than 2000 messages per second being received from over 100 aircraft. The messages are published to a pubsub topic for easy consumption and this is backed up to a Google Cloud Storage bucket.The flight data is collected through a network of ADS-B receivers, which are strategically distributed and linked to compact, remote edge computing platforms. These platforms are designed for efficient data processing at the source. Each receiver within the network plays a crucial role in capturing real-time data from aircraft within its coverage area.

Due to the dynamic nature of air traffic, the volume of data generated can be substantial. In densely populated airspace, the system can handle an influx of over 2000 messages per second, originating from more than 100 aircraft. To manage this high-velocity data stream, the messages are published to a pubsub topic. This approach ensures that the data is readily available for consumption by various applications and services. Additionally, the data is backed up to a Google Cloud Storage bucket, providing a durable and reliable storage solution for long-term retention and analysis. There is a sample service [here](https://skies-adsb-707366556769.europe-west2.run.app/) to visualize the realtime data. 

The rough architecture of the system is shown below with the existing infrastructure on the left and the challenges for you as the Visualization Analyst on the right.

![Architecture](images/Architecture.svg)

The critical challenges from a data engineering perspective beyond the potentially dirty data lie in the physical implementation of the system. In data engineering it is prerfered to have duplicate data rather than to lose data, however this means that the system must be designed to tolerate duplicate data throughout the pipeline. Duplication may occur at:

- The aircraft, it may send out the data twice but it should have the same generation time
- The logger, the logger may record receiving the data twice
- The logger also might send the data to pubsub twice
- Pubsub may deliver the message to each subscription more than once
- Dataflow and BigQuery may duplicate the data ingested in some specfic failure scenarios

![Representation of Challenges](images/Challenges.svg)

If data is going to be aggregated for each session the aircraft is seen then a session window will be required. Tumbling (fixed time) windows and hopping (sliding windows) will not aggregate the data correctly. A session window should be chosen that accurately reflects the validity of the data. If the window is too short then an aircraft's session may be closed if it enters a shadow which is a portion of the airspace that is tracked due to ground obstructions. This frequently happens when there is a building between the logger and the aircraft usually close to landing/take off are for aircraft near the maximum range of the loggers. If the session is too long it may join a previous flight with a current flight. This means the session should be shorter than the fastest turn around of a commercial airliner which is around 45 minutes. Another consideration is that the session is not emitted until after the final data is received so the longer the session, the longer it will take for the data to be available for analysis.

Another challenge is as the F-ATC logger network expands data from each aircraft may be received more than once. This is prefereable as it eliminates the shadows and gives better detail over a wider area. For each message

Below is a snapshot of the airspace over London Heathrow showing over flights (flights at high altitude just passing over), in holding (center left of the image, aircraft waiting to be brought into approach), aircraft on final (below center left) and aircraft taking off (center).

![Snapshot of real data from ADS-B showing holding and appraoching aircraft](images/Realtime.png)

## Setup:
Terraform script to deploy databases and load data into the following sources:
SQL Server on Cloud SQL
Postgres on AlloyDB or Spanner
Document storage on Firestore?
Log data in Cloud Storage
Data to be statically stored in AWS S3 buckets and Azure Blob Storage buckets for the project. Will need to think about managing this data and billing
Terraform script to deploy a small VM for streaming simulated data to Pub/Sub and writing transactions to Cloud SQL and/or AlloyDB/Spanner.

## Task 1
Consolidate data from transactional databases and object storage into a single location. This will mean using BigQuery or Spanner for the transactional data and Cloud Storage for object storage. Students should explore tools like DTS and connections in BigQuery for performing this task. The goal here is not to fully analyze the data, but rather to just get everything into one place before further ETL

## Task 2
Perform ETL on the consolidated batch data to transform the data into an appropriate form for the data warehouse. A specific use case will need to be defined for this to be viable.

## Task 3
Orchestrate the first two tasks via an orchestration tool such as Composer or Data Fusion. Ideally Composer here unless students want to go the Data Fusion route.

## Task 4
Now visit streaming data via Pub/Sub and Dataflow. Explore the data (that has been written to a sink in GCS) and write a pipeline to properly parse the data and store it in BigQuery. Ensure that the data is valid.

## Task 5
Implement CDC on the transactional data using a product such as Datastream. Incorporate this into your DE workload

