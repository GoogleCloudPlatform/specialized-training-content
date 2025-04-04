# Data Visualization and Reporting: Transform Data into Actionable Insights

## Setup:
Data spread across Cloud SQL/Spanner and BigQuery (clearly just lift and shift from a transactional DB) which will be needed for business use case
Preexisting Looker Studio dashboard built that isn't quite right/has very poor performance

## Task 1
Understand data across different sources and set up a connection between Cloud SQL/Spanner and BigQuery. Explore Looker Studio dashboard to identify why there are issues with the results and issues with the performance.

## Task 2
Create a new table (or tables) with appropriate schema to optimize query performance. Leverage repeated and nested fields where appropriate.  Create a scheduled query to repopulate this new table once per day.

## Task 3
Update the Looker Studio dashboard to incorporate the new table(s) and fix identified issues with queries. 

## Task 4
Performance is still slower than it should be. Create materialized views to improve the performance of your queries. Set up BI Engine and use it to further improve performance.

## Task 5
The business team who owns the dashboard has asked for you to add in additional metrics and visualizations to the dashboard. Revisit your work from the previous tasks to integrate these new asks into the dashboard.

