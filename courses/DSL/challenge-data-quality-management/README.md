# Data Quality Management

## F-ATC Company Overview

![F-ATC Logo](images/logo.png)

Fictional Aircraft Tracking Company is a leading provider of flight tracking data analytics, dedicated to enhancing the safety of civil aviation worldwide. With a team of experienced aviation professionals and data scientists, we leverage advanced technologies to analyze vast amounts of flight data, providing critical insights to airlines, airports, and regulatory authorities.


Our mission is to revolutionize the way flight tracking data is utilized, empowering our partners to make informed decisions, optimize operations, and mitigate potential risks. By harnessing the power of data, Fictional Aircraft Tracking Company is committed to ensuring the highest standards of safety and efficiency in the global aviation industry.


The flight data is gathered from a distributed network of ADS-B receivers connected to small remote publishing edge compute platforms. These send all data received to pubsub. There are multiple sensors in each region. The busiest airspaces can have more than 2000 messages per second being received from over 100 aircraft. The messages are published to a pubsub topic for easy consumption and this is backed up to a Google Cloud Storage bucket.The flight data is collected through a network of ADS-B receivers, which are strategically distributed and linked to compact, remote edge computing platforms. These platforms are designed for efficient data processing at the source. Each receiver within the network plays a crucial role in capturing real-time data from aircraft within its coverage area.

Due to the dynamic nature of air traffic, the volume of data generated can be substantial. In densely populated airspace, the system can handle an influx of over 2000 messages per second, originating from more than 100 aircraft. To manage this high-velocity data stream, the messages are published to a pubsub topic. This approach ensures that the data is readily available for consumption by various applications and services. Additionally, the data is backed up to a Google Cloud Storage bucket, providing a durable and reliable storage solution for long-term retention and analysis.

The rough architecture of the system is shown below with the existing infrastructure on the left and the challenges for you as the Visualization Analyst on the right.

![Architecture](images/Architecture.svg)

## Setup

1. Create the datasets.
    ```bash
    export PROJECT_ID=$DEVSHELL_PROJECT_ID
    export REGION=us-central1
    ```
    1. Cloud Storage<br>
        Copy yesterday's data for the static sets.
        ```bash
        gcloud storage buckets create \
            gs://$PROJECT_ID-flightdata-bucket \
            --location=$REGION
        
        gcloud storage cp \
            gs://flightdata-demo/flightdata_$(date --date="yesterday" +'%Y-%m-%d')T*.csv \
            gs://$PROJECT_ID-flightdata-bucket
        ```
    1. Pub/Sub<br>
        Subscribe to the live data stream.
        ```bash
        gcloud pubsub subscriptions create live-data-stream \
            --topic=projects/paul-leroy/topics/flightdata-gcs-eventstream \
            --ack-deadline=300 --message-retention-duration=1d
        ```
    1. BigQuery<br>
        Copy the data warehouse data.
        ```bash
        bq mk --location=$REGION \
            --dataset $PROJECT_ID:flight_data

        bq load --source_format=PARQUET \
            flight_data.transponderHistoric \
            gs://flightdata-demo-dsl/transponder*.parquet
        ```

## Task 1. Identify Data Issues
This task involves examining datasets for potential problems. Data is collected in two message formats from aircraft. One format sends multiple messages over the air, while the other sends a single message that is decoded into multiple messages upon receipt. Both formats utilize the same structure across BigQuery, Cloud Storage, and Pub/Sub. A common issue is that individual messages may contain only partial data.

You will need to query the raw data from Cloud Storage, the messages from the subscription, and the BigQuery table.

### Step 1. Investigate Data Coverage Gaps
Ground-based ADS-B systems have line-of-sight limitations, which can result in coverage gaps over oceans, mountainous regions, and at low altitudes.

You will need to write a SQL query to identify the largest gaps between the timestamps of the generated data. This will help in understanding data intermittency.

### Step 2. Analyze Missing or Incomplete Fields
Some aircraft do not transmit a complete set of data.

You will need to write a query to analyze the volume of missing data per aircraft. This will help in identifying which aircraft frequently transmit incomplete information.

### Step 3. Identify Transponder and Data Source Anomalies
Aircraft may broadcast incorrect transponder codes, such as default codes like "000000" or "123456." This can lead to misidentification or the appearance of multiple aircraft when only one is present.

Since the current data streams are exclusively from ADS-B, you can expect these to be the primary data quality issues requiring consideration.

## Task 2. Create a Data Mesh with Dataplex
You will create a data mesh with Dataplex to track different data sources and streams. You will use data profiling to identify potential issues in your datasets. This task involves creating the data lake and profiles for Cloud Storage. The Pub/Sub source will be addressed later in the challenge.

- **Lakes:** A Dataplex Lake, such as "FlightOperationsDataDomain," functions as the top-level logical container for flight-related data and metadata within the data mesh. It represents a business domain, unifying distributed data assets under a common governance umbrella.
- **Zones (Raw and Curated):** Within this lake, data is organized into Zones, which can represent sub-domains or stages of data processing.
    - **Raw Zones:** These zones are for the initial ingestion of flight data from various feeds (ADS-B, MLAT, airline schedules, etc.) into Cloud Storage. Data in raw zones is in its original, unprocessed format, aligning with the best practice of preserving source data before transformation. This raw data is considered "untrusted" until it undergoes validation and cleansing.
    - **Curated Zones:** Data that has been processed, validated, and cleansed is promoted to curated zones. These zones typically house structured data in BigQuery, ready for consumption by analytical tools and operational applications. Data in curated zones must conform to predefined schemas and meet established quality standards. The transition from a raw zone to a curated zone is not merely a change in data state but represents a data quality gating mechanism. Only data that successfully passes through the defined transformation and validation pipelines (e.g., Dataflow processing and Dataplex quality checks) is promoted to a curated zone. Access controls can be more stringent for curated zones, ensuring that downstream consumers primarily interact with data that has met these quality benchmarks.
- **Assets:** Physical storage resources, such as Cloud Storage buckets for raw data feeds and BigQuery datasets for curated flight information, are mapped as Assets within their respective zones. This links the logical data mesh structure defined in Dataplex to the underlying data storage, enabling centralized discovery, metadata management, and governance.

Some potential data issues you may encounter:

- **Out-of-range values:** Altitudes exceeding 73,000 feet, negative ground speeds, or latitudes outside the -90 to +90 range. There may be U2 aircraft in the feed (service ceiling of 73,000 ft) in addition to commercial aircraft.
- **Unexpected nulls:** Missing aircraft ICAO24 identifiers, timestamps, or positional data.
- **Cardinality anomalies:** An unexpectedly high number of unique aircraft types might indicate issues with aircraft type classification or data entry errors. The insights gleaned from data profiling are not merely informational; Dataplex can use these profiles to recommend potential data quality rules. This accelerates the rule definition process by providing data-driven suggestions. Data profiling should not be a static, one-time activity. Given the dynamic nature of flight data—with new aircraft, routes, and potential sensor error patterns emerging—continuous or regularly scheduled profiling of key datasets is essential. This proactive approach can help identify data drift or new quality issues before they significantly impact downstream systems or trigger widespread rule failures, allowing for timely adaptation of data quality rules and processes.
- Different countries have different minimum requirements for ADS-B data, so data from European and American regions may be more data-rich than from elsewhere.

### Step 1. Create a Dataplex Lake
You will need to create a Dataplex Lake named "FlightOperationsDataDomain".

### Step 2. Create Zones within the Lake
You will need to create two zones within your "FlightOperationsDataDomain" lake:

- A "Raw Zone" for unprocessed data.
- A "Curated Zone" for processed and validated data.

### Step 3. Add Assets to the Zones
You will need to map your Cloud Storage buckets (for raw data) and BigQuery datasets (for curated data) as Assets within their respective zones. This establishes the link between your logical data mesh and the physical data storage.

### Step 4. Configure Data Profiling
You will need to configure data profiling for your Cloud Storage assets. This will help you identify potential data quality issues, such as out-of-range values, unexpected nulls, and cardinality anomalies, and recommend data quality rules.

## Task 3. Define and Implement Data Quality Rules
This task involves defining and implementing data quality rules within the Google Cloud environment. You will translate general aviation data quality principles and domain-specific knowledge into executable checks.

### Step 1. Create Pub/Sub Topics
You will need to create two Pub/Sub topics. One topic will serve as the primary feed for your project, and the second will be a dead-letter queue for data that requires further review. You will also set the schema on the primary topic to match the expected output of your Dataflow pipeline.

### Step 2. Develop a Dataflow Pipeline
You will write a Dataflow pipeline to clean the data. The cleaned data will be written to the ingest topic. Any data that does not conform to the required structure will be output to the hospitalization topic.

### Step 3. Configure Alerts for Data Mismatches
You will set a pull subscription on the hospitalization topic. An alert will be configured on the number of unacknowledged messages on this topic, ensuring you are notified of any data mismatches.

### Stepp 4. Sink Data to BigQuery
You can directly sink data from the ingest topic into the BigQuery curated table.

## Task 4

<!---
Original ask
Create a data quality workflow in Dataplex to capture issues as they arise. Schedule tasks to run on a regular basis and alert you when there are issues.--->

You can add additional checks, some ideas are:

- **Implementing predefined Dataplex rules for common flight data checks**:
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
- **Crafting custom SQL rules in Dataplex for advanced validations**:
    For more complex or domain-specific checks that go beyond predefined rules, Dataplex allows the creation of custom SQL rules. These are powerful for encoding nuanced business logic.
    - **Row condition (evaluates per row, SQL expression in a WHERE clause)**:
        - `altitude < 1000 AND ground_speed > 150` (flag potential error: aircraft too fast at very low altitude, unless it's a specific known takeoff/landing phase for certain aircraft).
        - `ABS(vertical_rate) > 12000` (flag potentially erroneous extreme vertical speeds).
        - Check for consistency between reported flight phase (e.g., climb, cruise, descent) and telemetry (e.g., flight_phase = 'CRUISE' AND vertical_rate > 500).
        - Referential integrity for simple lookups: airport_code IN (`SELECT code FROM master_airport_list_table`) (though complex joins might be better handled in Dataflow or via pre-materialized views as Dataplex rules primarily focus on a single table 28).
    - **Aggregate SQL expression (evaluates once per table, SQL expression returns boolean)**:
        - `SELECT COUNT(*) = 0 FROM my_flight_data WHERE on_ground = TRUE AND altitude_ft > 1000` (ensure no aircraft reported as on ground are at significant altitude).
        - Referential integrity check: `(SELECT COUNT(DISTINCT f.aircraft_id) FROM flight_movements f WHERE f.aircraft_id NOT IN (SELECT DISTINCT a.aircraft_id FROM aircraft_master a)) = 0` (ensure all aircraft in movement logs exist in the master aircraft registry). 29 provides an example for checking UUID existence. While predefined rules cover many scenarios, the ability to define custom SQL rules allows domain experts to directly translate their specific knowledge of flight operations and data characteristics into executable quality checks, particularly for validations on already loaded and curated data.
- Employing Dataflow for Real-time Validation, Cleansing, and Enrichment:
While Dataplex excels at validating data at rest in BigQuery, Google Cloud Dataflow is the preferred service for performing complex, real-time validation, cleansing, and enrichment on streaming flight data as it arrives from Pub/Sub and before it lands in curated BigQuery tables.30 Dataflow pipelines, built using the Apache Beam SDK, can implement sophisticated logic:
    - **Complex data cleansing**:
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
    - **Writing to multiple BigQuery tables/datasets with varying schemas**: The outputs from conditional routing often need to be written to different BigQuery tables, potentially with different schemas (e.g., the quarantine table might have additional columns for error codes and descriptions).
        - **Raw ingested data**: It's a best practice to first land the raw, unmodified (or minimally processed for basic schema adherence) data from Pub/Sub into a "raw_flight_data" BigQuery table or Cloud Storage archive. This ensures no data is lost and allows for reprocessing if cleansing logic changes or errors are found in the initial processing.
        - **Transformed/curated data**: The primary output of the Dataflow pipeline – validated, cleansed, and enriched flight data – is written to "curated_flight_tracks" tables. These might be further specialized (e.g., "current_flight_positions," "completed_flight_summaries").
        - **Error/quarantine tables**: Problematic records are written to dedicated tables. Dataflow's BigQueryIO connector supports dynamic destinations, enabling a single Write transform to send records to different tables based on the content of each record (e.g., an event_type field in the data could determine the target table). This is highly useful for managing the diverse outputs of a DQM-focused pipeline.

<!---
Original ask
Some of the issues arising are happening with incoming streaming data. Implement controls on the Pub/Sub topic (such as schemas) and post-processing (using Dataflow or continuous queries) to clean data as it arrives for the data warehouse. Store both raw data and transformed data into different datasets. Update your data mesh with this in mind.--->

## Task 5. Modify Dataflow Pipeline
You will need to update your dataflow pipeline to filter flights and modify data fields.

### Step 1. Filter Flights
Modify the existing rule to exclude flights with an altitude exceeding 43,100 feet. You will need to apply this filter to the appropriate field in your data.

### Step 2. Concatenate and Drop Fields
Adjust the data structure requirements within your dataflow pipeline. You will need to concatenate the TMG and DMG fields into a new `DATETIME` field. Additionally, you will need to drop the `DML` and `TML` fields from the dataflow as you may get messages from two receivers picking up the same message. 

### Step 3. Update Pub/Sub Messages, Schema, and Quality Controls
Republish the Pub/Sub messages with the updated data. You will also need to modify the Pub/Sub schema to reflect the new `DATETIME` field and the removal of the `DML` and `TML` fields. Update your quality controls to align with these changes.

You are interested in only commercial airlines, change the rules to remove any flights above 43,100 feet. The upstream team are amending the data structure requirements to have the `TMG` and `DMG` field concatenated into a `DATETIME` field and drop the `DML` and `TML` fields. Update your dataflow pipeline that is republishing the Pub/Sub messages, the schema, and quality controls.

When running this you may end up with this error which indicates one of the receivers is appending garbage to the end of the line. Rather than fail the `int` conversion set it to null. `{'error': "Type conversion error: invalid literal for int() with base 10: '\\r'", 'data': {'MT': 'MSG', 'TT': '6', 'SID': '1', 'AID': '1', 'Hex': '39CF01', 'FID': '1', 'DMG': '2025-05-23', 'TMG': '09:28:19.864', 'DML': '2025-05-23', 'TML': '09:28:19.918', 'VR': '352', 'Sq': 6307, 'Alrt': 0, 'Emer': 0, 'SPI': 0, 'Gnd': '\r'}}`. Notice the `\r` in the `Ground` field, this means that the data is being added with a Windows style newline `\r\n` and PubSub will remove the `\n` but not the `\r`. If this field is not numeric it would be a good idea to null it rather than trigger an error.

Sample data going into the `hospitalization` topic:
```json
{"quality": "hex_format", "data": {"MT": "MSG", "TT": "3", "SID": "1", "AID": "1", "Hex": "~AB828A", "FID": "1", "DMG": "2025-05-23", "TMG": "10:02:21.366", "DML": "2025-05-23", "TML": "10:02:21.366", "Alt": 1800, "Lat": 51.423798, "Lng": -1.689668, "Alrt": 0, "SPI": 0}}
{"quality": "hex_format", "data": {"MT": "MSG", "TT": "3", "SID": "1", "AID": "1", "Hex": "~AB828A", "FID": "1", "DMG": "2025-05-23", "TMG": "10:02:21.366", "DML": "2025-05-23", "TML": "10:02:21.366", "Alt": 1800, "Lat": 51.42379, "Lng": -1.689682, "Alrt": 0, "SPI": 0}}
{"quality": "altitude", "data": {"MT": "MSG", "TT": "3", "SID": "1", "AID": "1", "Hex": "403321", "FID": "1", "DMG": "2025-05-23", "TMG": "10:07:49.614", "DML": "2025-05-23", "TML": "10:07:49.629", "Alt": -50, "Lat": 51.50377, "Lng": -0.76451, "Alrt": 0, "SPI": 0}}
{"quality": "altitude", "data": {"MT": "MSG", "TT": "3", "SID": "1", "AID": "1", "Hex": "508472", "FID": "1", "DMG": "2025-05-23", "TMG": "10:08:22.546", "DML": "2025-05-23", "TML": "10:08:22.561", "Alt": -75, "Lat": 51.5018, "Lng": -0.76726, "Alrt": 0, "SPI": 0}}
{"quality": "altitude", "data": {"MT": "MSG", "TT": "3", "SID": "1", "AID": "1", "Hex": "508472", "FID": "1", "DMG": "2025-05-23", "TMG": "10:10:30.546", "DML": "2025-05-23", "TML": "10:10:30.574", "Alt": -75, "Lat": 51.50194, "Lng": -0.76719, "Alrt": 0, "SPI": 0}}
{"quality": "altitude", "data": {"MT": "MSG", "TT": "7", "SID": "1", "AID": "1", "Hex": "508472", "FID": "1", "DMG": "2025-05-23", "TMG": "10:10:20.888", "DML": "2025-05-23", "TML": "10:10:20.908", "Alt": -75}}
{"quality": "altitude", "data": {"MT": "MSG", "TT": "7", "SID": "1", "AID": "1", "Hex": "508472", "FID": "1", "DMG": "2025-05-23", "TMG": "10:11:05.196", "DML": "2025-05-23", "TML": "10:11:05.200", "Alt": -75}}
{"quality": "altitude", "data": {"MT": "MSG", "TT": "7", "SID": "1", "AID": "1", "Hex": "508472", "FID": "1", "DMG": "2025-05-23", "TMG": "10:11:21.113", "DML": "2025-05-23", "TML": "10:11:21.146", "Alt": -75}}
{"quality": "altitude", "data": {"MT": "MSG", "TT": "3", "SID": "1", "AID": "1", "Hex": "508472", "FID": "1", "DMG": "2025-05-23", "TMG": "10:12:37.237", "DML": "2025-05-23", "TML": "10:12:37.276", "Alt": -100, "Lat": 51.50226, "Lng": -0.76748, "Alrt": 0, "SPI": 0}}
{"quality": "altitude", "data": {"MT": "MSG", "TT": "7", "SID": "1", "AID": "1", "Hex": "402EE4", "FID": "1", "DMG": "2025-05-23", "TMG": "10:12:37.652", "DML": "2025-05-23", "TML": "10:12:37.661", "Alt": -100}}
{"quality": "altitude", "data": {"MT": "MSG", "TT": "3", "SID": "1", "AID": "1", "Hex": "508472", "FID": "1", "DMG": "2025-05-23", "TMG": "10:12:38.197", "DML": "2025-05-23", "TML": "10:12:38.207", "Alt": -100, "Lat": 51.50223, "Lng": -0.76752, "Alrt": 0, "SPI": 0}}
{"quality": "altitude", "data": {"MT": "MSG", "TT": "7", "SID": "1", "AID": "1", "Hex": "402EE4", "FID": "1", "DMG": "2025-05-23", "TMG": "10:12:38.871", "DML": "2025-05-23", "TML": "10:12:38.914", "Alt": -100}}
{"quality": "altitude", "data": {"MT": "MSG", "TT": "7", "SID": "1", "AID": "1", "Hex": "402EE4", "FID": "1", "DMG": "2025-05-23", "TMG": "10:12:39.526", "DML": "2025-05-23", "TML": "10:12:39.570", "Alt": -100}}
```

You will also need to update the schema on pubsub to match your new structure. You can use this schema (but you'll need to make sure your data matches):

```json
{
  "type": "record",
  "name": "PubsubMessage",
  "fields": [
    {"name": "MT", "type": "string"},
    {"name": "TT", "type": "int"},
    {"name": "SID", "type": "int"},
    {"name": "AID", "type": "int"},
    {"name": "Hex", "type": "string"},
    {"name": "FID", "type": "int"},
    {"name": "MG", "type": "string"},
    {"name": "CS", "type": ["null", "string"]},
    {"name": "Alt", "type": ["null", "int"]},
    {"name": "GS", "type": ["null", "int"]},
    {"name": "Trk", "type": ["null", "int"]},
    {"name": "Lat", "type": ["null", "double"]},
    {"name": "Lng", "type": ["null", "double"]},
    {"name": "VR", "type": ["null", "double"]},
    {"name": "Sq", "type": ["null", "string"]},
    {"name": "Alrt", "type": ["null", "int"]},
    {"name": "Emer", "type": ["null", "string"]},
    {"name": "SPI", "type": ["null", "int"]},
    {"name": "Gnd", "type": ["null", "int"]}
  ]
}
```

Aircraft Data Sourced from:
> Matthias Schäfer, Martin Strohmeier, Vincent Lenders, Ivan Martinovic, and Matthias Wilhelm.
> "Bringing Up OpenSky: A Large-scale ADS-B Sensor Network for Research".
> In Proceedings of the 13th IEEE/ACM International Symposium on Information Processing in Sensor Networks (IPSN), pages 83-94, April 2014.