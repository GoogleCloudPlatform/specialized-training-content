# Data Quality Management

## F-ATC Company Overview

![F-ATC Logo](images/logo.png)

Fictional Aircraft Tracking Company is a leading provider of flight tracking data analytics, dedicated to enhancing the safety of civil aviation worldwide. With a team of experienced aviation professionals and data scientists, we leverage advanced technologies to analyze vast amounts of flight data, providing critical insights to airlines, airports, and regulatory authorities.


Our mission is to revolutionize the way flight tracking data is utilized, empowering our partners to make informed decisions, optimize operations, and mitigate potential risks. By harnessing the power of data, Fictional Aircraft Tracking Company is committed to ensuring the highest standards of safety and efficiency in the global aviation industry.


The flight data is gathered from a distributed network of ADS-B receivers connected to small remote publishing edge compute platforms. These send all data received to pubsub. There are multiple sensors in each region. The busiest airspaces can have more than 2000 messages per second being received from over 100 aircraft. The messages are published to a pubsub topic for easy consumption and this is backed up to a Google Cloud Storage bucket.The flight data is collected through a network of ADS-B receivers, which are strategically distributed and linked to compact, remote edge computing platforms. These platforms are designed for efficient data processing at the source. Each receiver within the network plays a crucial role in capturing real-time data from aircraft within its coverage area.

Due to the dynamic nature of air traffic, the volume of data generated can be substantial. In densely populated airspace, the system can handle an influx of over 2000 messages per second, originating from more than 100 aircraft. To manage this high-velocity data stream, the messages are published to a pubsub topic. This approach ensures that the data is readily available for consumption by various applications and services. Additionally, the data is backed up to a Google Cloud Storage bucket, providing a durable and reliable storage solution for long-term retention and analysis.

The rough architecture of the system is shown below with the existing infrastructure on the left and the challenges for you as the Visualization Analyst on the right.

![Architecture](images/Architecture.svg)

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


