# Queries you can use when testing data agent via A2A Inspector
- What tables are available in the cymbal_meet dataset?
- Describe the schema of the customers table, including any nested fields
- How many customers are in each segment?
- What is the average number of logins per licensed user for each customer in the last 30 days? Show the top 5 and bottom 5
- Show me all CRM interactions for Pinnacle in the last 60 days
- Which customers have average call quality scores below 3.5? Include their segment and the number of calls
- Show me week-over-week login trends for BrightPath over the last 7 weeks
- How many customers are in the Enterprise segment?
- Show me the login activity for the customer with the lowest contract value.

# Queries you can use when testing the intervention agent via A2A inspector

# Queries you can use when testing the improvement agent

- Please create interventions for customers with low login rates (works)
  - tried below 50%; we really want to use relative to segment, or very low in absolute terms
- Please deal with low call quality issues (works)
- Find customers with low calendar usage (works)
- please address enterprise customers with engagement issues
  - not finding call quality for quantum
- please find and address engagement issues of all kinds across all customers
  - only finds two
  - 