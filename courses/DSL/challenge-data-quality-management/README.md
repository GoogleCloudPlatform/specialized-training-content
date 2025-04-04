# Data Quality Management

## Task 1
Explore datasets and look for problems. Based on the scenario summary, students should already have some ideas of where to look for issues, but they should also search for additional issues.

## Task 2
Create a data mesh with Dataplex to better be able to track the different data sources and streams. Use data profiling to better understand where issues could arise in your datasets.

## Task 3
Some of the issues arising are happening with incoming streaming data. Implement controls on the Pub/Sub topic (such as schemas) and post-processing (using Dataflow or continuous queries) to clean data as it arrives for the data warehouse. Store both raw data and transformed data into different datasets. Update your data mesh with this in mind.

## Task 4
Create a data quality workflow in Dataplex to capture issues as they arise. Schedule tasks to run on a regular basis and alert you when there are issues.

## Task 5
You have been informed about upstream changes to incoming data from applications, including schema changes and business logic changes to permissible values. Update your data quality workflow across the different tools being used to incorporate these changes.


