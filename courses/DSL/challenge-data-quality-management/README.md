# Data Quality Management

## F-ATC Company Overview

![F-ATC Logo](images/logo.png)

Fictional Aircraft Tracking Company is a leading provider of flight tracking data analytics, dedicated to enhancing the safety of civil aviation worldwide. With a team of experienced aviation professionals and data scientists, we leverage advanced technologies to analyze vast amounts of flight data, providing critical insights to airlines, airports, and regulatory authorities.


Our mission is to revolutionize the way flight tracking data is utilized, empowering our partners to make informed decisions, optimize operations, and mitigate potential risks. By harnessing the power of data, Fictional Aircraft Tracking Company is committed to ensuring the highest standards of safety and efficiency in the global aviation industry.


The flight data is gathered from a distributed network of ADS-B receivers connected to small remote publishing edge compute platforms. These send all data received to pubsub. There are multiple sensors in each region. The busiest airspaces can have more than 2000 messages per second being received from over 100 aircraft. The messages are published to a pubsub topic for easy consumption and this is backed up to a Google Cloud Storage bucket.The flight data is collected through a network of ADS-B receivers, which are strategically distributed and linked to compact, remote edge computing platforms. These platforms are designed for efficient data processing at the source. Each receiver within the network plays a crucial role in capturing real-time data from aircraft within its coverage area.

Due to the dynamic nature of air traffic, the volume of data generated can be substantial. In densely populated airspace, the system can handle an influx of over 2000 messages per second, originating from more than 100 aircraft. To manage this high-velocity data stream, the messages are published to a pubsub topic. This approach ensures that the data is readily available for consumption by various applications and services. Additionally, the data is backed up to a Google Cloud Storage bucket, providing a durable and reliable storage solution for long-term retention and analysis.

The rough architecture of the system is shown below with the existing infrastructure on the left and the challenges for you as the Visualization Analyst on the right.

![Architecture](images/Architecture.svg)

## Task 0 

1. Create the datasets
    ```bash
    export PROJECT_ID=$DEVSHELL_PROJECT_ID
    export REGION=us-central1
    ```
    1. Cloud Storage
        Copy yesterday's data for the static sets
        ```bash
        gcloud storage buckets create \
            gs://$PROJECT_ID-flightdata-bucket \
            --location=$REGION
        
        gcloud storage cp \
            gs://flightdata-demo/flightdata_$(date --date="yesterday" +'%Y-%m-%d')T*.csv \
            gs://$PROJECT_ID-flightdata-bucket
        ```
    1. PubSub
        Subscribe to the live data stream
        ```bash
        gcloud pubsub subscriptions create live-data-stream \
            --topic=projects/paul-leroy/topics/flightdata-gcs-eventstream \
            --ack-deadline=300 --message-retention-duration=1d
        ```
    1. BigQuery
        Copy the data warehouse data
        ```bash
        bq mk --location=$REGION \
            --dataset $PROJECT_ID:flight_data

        bq load --source_format=PARQUET \
            flight_data.transponderHistoric \
            gs://flightdata-demo-dsl/transponder*.parquet
        ```

## Task 1

Explore datasets and look for problems. Based on the way that data is collected there are two message formats the aircraft sends after the data is generated, the first sends multiple messages over the air, the other sends one message which is decoded into multiple messages on the receiver. Both formats the same structure in BigQuery, Cloud Storage and PubSub but the main issue is that each message maybe only have some of the data. You will need to query the raw data from cloud storage, the messages from the subscription and the bigquery table. 

- **Coverage Gaps & Intermittency**: Ground-based ADS-B, a primary source, is limited by line-of-sight, leading to coverage gaps over oceans, mountainous terrain, or at low altitudes. MLAT systems require signals to be received by multiple ground stations, making their coverage dependent on receiver density. Even satellite-based ADS-B coverage can be dynamic and not consistently available. Volunteer-based networks, like parts of OpenSky Network, can experience intermittent receiver availability or performance issues.
Positional Inaccuracies: Aircraft transponders can occasionally transmit random or incorrect positional data, leading to "ghost" tracks or erratic flight paths. For some older aircraft, positional data calibrated on the ground can drift during a long flight, resulting in apparent deviations, such as landing outside the runway.9 MLAT position calculations, while generally accurate, can sometimes produce errors in speed or altitude, especially if signal quality is poor.9 OpenSky Network also acknowledges that some aircraft transmit false or erroneous position reports.
- **Latency and Timeliness**: While the goal is real-time tracking, delays can be introduced at various points: data transmission from remote receivers, network latency, and processing time within the aggregation systems. For instance, some data sources integrated by Flightradar24, such as certain FAA feeds, can have inherent delays of up to five minutes. Timeliness, or temporal accuracy, is recognized as a critical data quality dimension by aviation authorities like ICAO.
- **Missing or Incomplete Fields**: Not all data sources provide a complete set of flight parameters. For example, FLARM systems, often used by gliders, may not always transmit altitude information.3 Furthermore, aircraft metadata databases, which link transponder signals to specific aircraft details (like type, registration, or operator), may contain missing or outdated information.11
- **Transponder and Data Source Anomalies**: Aircraft may broadcast incorrect transponder codes (e.g., default codes like "000000" or "123456"), leading to misidentification or the appearance of multiple aircraft where only one exists.9 Errors in other integrated data sources, such as radar feeds, can also introduce anomalies, like displaying an aircraft flying in the opposite direction of its actual travel.9 ADS-B signals themselves are susceptible to low Signal-to-Noise Ratios (SNR) and interference, which can result in bit errors during decoding.
Data Integrity Issues: Beyond simple inaccuracies, the corruption of critical aeronautical data, such as the precise coordinates of navigation aids or runway thresholds, can pose severe risks to flight safety. ICAO guidelines emphasize the importance of data integrity levels (critical, essential, routine) based on the potential risk of using corrupted data.

Since the current data streams are only ADS-B you can expect those to be the core data quality issues to consider.

## Task 2

Create a data mesh with Dataplex to better be able to track the different data sources and streams. Use data profiling to better understand where issues could arise in your datasets. You'll need to create the data lake and profiles for cloud storage. You'll work on the pubsub source a later in the challenge. 

- **Lakes**: A Dataplex Lake, such as "FlightOperationsDataDomain," acts as the top-level logical container for all flight-related data and metadata within the data mesh. It represents a distinct business domain, unifying distributed data assets under a common governance umbrella.
- **Zones (Raw and Curated)**: Within this lake, data is organized into Zones, which can represent sub-domains or stages of data processing.
    - **Raw Zones**: These zones are designated for the initial ingestion of flight data from various feeds (ADS-B, MLAT, airline schedules, etc.) into Cloud Storage. Data in raw zones is stored in its original, unprocessed format, aligning with the best practice of preserving source data before transformation. This raw data is considered "untrusted" until it undergoes validation and cleansing.
    - **Curated Zones**: Data that has been processed, validated, and cleansed is promoted to curated zones. These zones typically house structured data in BigQuery, ready for consumption by analytical tools and operational applications.14 Data in curated zones must conform to predefined schemas and meet established quality standards. The transition from a raw zone to a curated zone is not merely a change in data state but represents a critical data quality gating mechanism. Only data that successfully passes through the defined transformation and validation pipelines (e.g., Dataflow processing and Dataplex quality checks) earns promotion to a curated zone. Access controls can be more stringent for curated zones, ensuring that downstream consumers primarily interact with data that has met these quality benchmarks.
- **Assets**: Physical storage resources, such as Cloud Storage buckets for raw data feeds and BigQuery datasets for curated flight information, are mapped as Assets within their respective zones.19 This links the logical data mesh structure defined in Dataplex to the underlying data storage, enabling centralized discovery, metadata management, and governance.

Some potential data issues that you may encounter and 
- Out-of-range values: Altitudes exceeding 73,000 feet, negative ground speeds, or latitudes outside the -90 to +90 range. There may be U2 aircraft in the feed (service ceiling of 73000 ft) in addition to commercial aircraft.
- Unexpected nulls: Missing aircraft ICAO24 identifiers, timestamps, or crucial positional data.
- Cardinality anomalies: An unexpectedly high number of unique aircraft types might indicate issues with aircraft type classification or data entry errors. The insights gleaned from data profiling are not merely informational; Dataplex can use these profiles to recommend potential data quality rules. This accelerates the rule definition process by providing data-driven suggestions. Data profiling should not be a static, one-time activity. Given the dynamic nature of flight data – with new aircraft, routes, and potential sensor error patterns emerging – continuous or regularly scheduled profiling of key datasets is essential. This proactive approach can help identify data drift or new quality issues before they significantly impact downstream systems or trigger widespread rule failures, allowing for timely adaptation of data quality rules and processes.
- Different countries have different minimum requirements for ADS-B data, so expect data from the the Eropean and American regions to be more data rich than ones from elsewhere.

## Task 3

With a foundational understanding of the data's characteristics, the next step is to define and implement specific data quality rules. This involves translating general aviation data quality principles and domain-specific knowledge into executable checks within the GCP environment.

You'll need to create two pubsub topics, one for piping the primary feed into your project and the second a dead-letter queue for data hospitalization. Set the schema on the topic to match what you expect your dataflow pipeline to output. Write a dataflow pipeline to clean the data and write it to the ingest topic and any data that doesn't match the required structure output to the hospitalization topic. Set a pull subscription on the hospitalization topic and an alert on the number of unacked messages on that topic so you will be alerted of any data mismatches.

You can can sink data from the ingest topic directly into the BigQuery curated table.

## Task 4

<!---
Original ask
Create a data quality workflow in Dataplex to capture issues as they arise. Schedule tasks to run on a regular basis and alert you when there are issues.--->

You can add additional checks, some ideas are:

- **Implementing Predefined Dataplex Rules for Common Flight Data Checks**:
Dataplex offers a suite of predefined rule types that can be directly applied to BigQuery tables containing flight data 26:
    - **RangeExpectation (Range Check)**: Crucial for validating fundamental flight parameters. Examples:
        - Latitude between -90 and 90 degrees.
        - Longitude between -180 and 180 degrees.
        - Altitude (e.g., geometric or barometric) within plausible limits (e.g., -2,000 to 70,000 feet).
        - Ground speed or true airspeed (e.g., 0 to 800 knots).
        - Vertical rate within typical aircraft performance (e.g., -15,000 to +15,000 feet per minute).
    - **NonNullExpectation (Null Check)**: Ensures critical identifiers and measurements are present. Examples:
        - ICAO24 address, callsign, timestamp, latitude, longitude, altitude must not be null.
    - **SetExpectation (Set Check)**: Validates categorical data against a predefined list of allowed values. Examples:
        - Squawk codes against known emergency (7500, 7600, 7700) or standard operational codes.
        - Aircraft type codes (e.g., A320, B738) against an authoritative list of ICAO aircraft type designators.
        - `on_ground` flag must be TRUE or FALSE.
    - **RegexExpectation (Regular Expression Check)**: Validates the format of string-based identifiers. Examples:
        - Aircraft registration format (e.g., N123AB, G-ABCD).
        - Flight number format (e.g., BAW123, UAL4567).
    - **Uniqueness (Uniqueness Check)**: Ensures identifiers that should be unique are indeed unique within a given context. Example:
        - A combination of ICAO24 and timestamp for a specific position report should be unique.
        - Flight ID (if generated) should be unique for active flights.
    - **StatisticRangeExpectation (Statistic Check)**: Checks aggregated statistics against expected ranges. Example:
        -   The average number of position reports received per minute for an active flight should be within a defined range (e.g., 4 to 12, depending on the source like ADS-B).
- **Crafting Custom SQL Rules in Dataplex for Advanced Validations**:
    For more complex or domain-specific checks that go beyond predefined rules, Dataplex allows the creation of custom SQL rules.26 These are powerful for encoding nuanced business logic.
    - **Row Condition (evaluates per row, SQL expression in a WHERE clause)**:
        - `altitude < 1000 AND ground_speed > 150` (flag potential error: aircraft too fast at very low altitude, unless it's a specific known takeoff/landing phase for certain aircraft).
        - `ABS(vertical_rate) > 12000` (flag potentially erroneous extreme vertical speeds).
        - Check for consistency between reported flight phase (e.g., climb, cruise, descent) and telemetry (e.g., flight_phase = 'CRUISE' AND vertical_rate > 500).
        - Referential integrity for simple lookups: airport_code IN (`SELECT code FROM master_airport_list_table`) (though complex joins might be better handled in Dataflow or via pre-materialized views as Dataplex rules primarily focus on a single table 28).
    - **Aggregate SQL Expression (evaluates once per table, SQL expression returns boolean)**:
        - `SELECT COUNT(*) = 0 FROM my_flight_data WHERE on_ground = TRUE AND altitude_ft > 1000` (ensure no aircraft reported as on ground are at significant altitude).
        - Referential integrity check: `(SELECT COUNT(DISTINCT f.aircraft_id) FROM flight_movements f WHERE f.aircraft_id NOT IN (SELECT DISTINCT a.aircraft_id FROM aircraft_master a)) = 0` (ensure all aircraft in movement logs exist in the master aircraft registry). 29 provides an example for checking UUID existence. While predefined rules cover many scenarios, the ability to define custom SQL rules allows domain experts to directly translate their specific knowledge of flight operations and data characteristics into executable quality checks, particularly for validations on already loaded and curated data.
- Employing Dataflow for Real-time Validation, Cleansing, and Enrichment:
While Dataplex excels at validating data at rest in BigQuery, Google Cloud Dataflow is the preferred service for performing complex, real-time validation, cleansing, and enrichment on streaming flight data as it arrives from Pub/Sub and before it lands in curated BigQuery tables.30 Dataflow pipelines, built using the Apache Beam SDK, can implement sophisticated logic:
    - **Complex Data Cleansing**:
        - Decoding various ADS-B message formats or other proprietary sensor data.
        - Implementing algorithms for interpolating missing position reports for short durations, based on previous trajectory and speed.
        - Correcting known erroneous transponder codes.9
        - Flagging or attempting to smooth impossible flight maneuvers (e.g., instantaneous changes in position or speed that violate physical constraints or known aircraft performance). This addresses issues like transponder errors generating random positions or incorrect data due to calibration drift.9
        - Applying filters to remove test signals or ground vehicle transponder data that might be picked up by receivers.
    - Conditional Routing with Output Tags: A critical pattern in Dataflow for DQM is the use of output tags with ParDo transforms.31 This allows a single processing step to route elements to different PCollections based on validation outcomes:
        - **Valid, cleansed data**: Routed to a PCollection destined for the primary "curated_flights" BigQuery table.
        - **Data with minor, fixable errors (post-cleansing)**: Also routed to the "curated_flights" PCollection.
        - **Data with severe, unfixable anomalies or failing critical validation**: Routed to a separate PCollection for a "quarantined_flights" BigQuery table or a dead-letter queue (DLQ) in Cloud Storage. This quarantined data is invaluable for later analysis of error patterns and for refining DQ rules and cleansing logic.
        - **Messages with unknown or unparseable schemas**: Routed to a dedicated DLQ for schema-related issues.
    - **Writing to Multiple BigQuery Tables/Datasets with Varying Schemas**: The outputs from conditional routing often need to be written to different BigQuery tables, potentially with different schemas (e.g., the quarantine table might have additional columns for error codes and descriptions).
        - **Raw Ingested Data**: It's a best practice to first land the raw, unmodified (or minimally processed for basic schema adherence) data from Pub/Sub into a "raw_flight_data" BigQuery table or Cloud Storage archive.18 This ensures no data is lost and allows for reprocessing if cleansing logic changes or errors are found in the initial processing.
        - **Transformed/Curated Data**: The primary output of the Dataflow pipeline – validated, cleansed, and enriched flight data – is written to "curated_flight_tracks" tables. These might be further specialized (e.g., "current_flight_positions," "completed_flight_summaries").
        - **Error/Quarantine Tables**: Problematic records are written to dedicated tables. Dataflow's BigQueryIO connector supports dynamic destinations, enabling a single Write transform to send records to different tables based on the content of each record (e.g., an event_type field in the data could determine the target table).33 This is highly useful for managing the diverse outputs of a DQM-focused pipeline.

<!---
Original ask
Some of the issues arising are happening with incoming streaming data. Implement controls on the Pub/Sub topic (such as schemas) and post-processing (using Dataflow or continuous queries) to clean data as it arrives for the data warehouse. Store both raw data and transformed data into different datasets. Update your data mesh with this in mind.--->



## Task 5

You are interested in only commercial airlines, change the rules to remove any flights above 43,100ft. The upstream team are amending the data structure requirements to have the `TMG` and `DMG` field concateneated into a `DATETIME` field and drop the `DML` and `TML` fields. Update your dataflow pipeline that is republishing the pubsub messages, the schema and quality controls.

<!---
Original ask
You have been informed about upstream changes to incoming data from applications, including schema changes and business logic changes to permissible values. Update your data quality workflow across the different tools being used to incorporate these changes.--->


