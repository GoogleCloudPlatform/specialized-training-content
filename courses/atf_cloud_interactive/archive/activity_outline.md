# Task 1 - Reviewing architecture and infrastructure

## 1.1 Evaluate architecture

1. Review architecture diagram
2. Take notes with questions, challenges, recommendations

<hr>

## 1.2 Explore pre-configured infrastructure

1. Verify the services enabled
2. Check to see what service accounts were created
   1. Note which is used by what
3. Check to see IAM roles assignments
   1. Note which are used for what
4. Check to see that the buckets were created
5. Confirm that the Vertex AI Search data was created
   1. Review each document indexed
6. Review the BigQuery data set
   1. Note the tables, the table contents
7. Confirm the deployed MCP server
   1. Test with MCP inspector

## 1.3 Review

### Questions for attendees
1. What roles are assigned to the agent service account and why?
2. Does it make sense to use a single service account for all three agents?
3. Why does the GCS MCP server use signed URLs?

### Questions from attendees
1. Questions about scenario
2. Questions about architecture
3. Questions about pre-configured infrastructure?


## Task 2: Implementing and testing the data agent

### 2.1 Understanding the agent
1. Read through the prompt
2. Review the Gemini3 class
3. Note the telemetry plumbing placeholders
4. Note the MCP plumbing placeholders
5. Note the A2A plumbing placeholders
6. Note the Model Armor plumbing

### 2.2 Implementing MCP client functionality
1. Specify the MCP endpoint and scopes
2. Specify the McpToolset connection parameters
3. Specify the McpToolset auth_schema and auth_credential
4. Add the McpToolset to the agent

### 2.3 Implementing the Open Telemetry functionality
1. Create the credentials object for use with exporters
2. Create configured exporters
3. Set up the Open Telemetry providers

### 2.4 Implementing Model Armor functionality
1. Explore and understand the Model Armor plugin
2. Create a runner object with the plugin registered

### 2.5 Implementing A2A functionality
1. Review the agent card
2. Create the A2A application

### 2.6 Test the agent locally
1. Install A2A inspector
2. Run the data agent locally
3. Connect to the agent using inspector
4. Run test queries and confirm behavior

### 2.7 Deploy and test on Cloud Run
1. Update agent card
2. Run deployment script
3. Review configuration of deployed agent in Cloud Run
4. Use A2A inspector to validate deployed agent
5. Review what's recorded in telemetry

## 2.8 Review

### Questions for attendees
1. What were the 2-3 most important/interesting new things you learned performing this task?
2. What are the implications of using the agent service account to authentication to the BigQuery MCP server?
3. Do you have any ideas for implementing differently?
4. Review what's recorded in telemetry

### Questions from attendees
1. Questions about MCP?
2. Questions about Model Armor?
3. Questions about Telemetry?
4. Questions about A2a?

## Task 3: Implementing and testing the improvement agent

### 3.1 Understanding the agent
1. Read through the prompt
   1. Note that the current prompt only references the data agent
   2. The remainder will be implemented in Task 4
2. Review the authentication class that will be used to talk to secure Cloud Run agents
3. Note the absence of telemetry plumbing, A2A plumbing and MCP plumbing

### 3.2 Creating the Remote data agent
1. Create the http client with Cloud Run authentication
2. Create the remote agent using Remote A2aAgent

### 3.3 Set up Agent Tools
1. Wrap the remote agent as AgentTool 
2. Update agent definition to use the tool

### 3.4 Test agent locally
1. Run the agent using ADK Web
2. Test functionality

### 3.5 Deploy agent to Agent Engine
1. Deploy to Agent Engine

### 3.6 Create Gemini Enterprise application
1. Enable Gemini Enterprise
2. Configure identity
3. Test application

### 3.7 Deploy and test Agent Engine agent with Gemini Enterprise
1. Add Agent Engine Agent
2. Test 

## 3.8 Review

### Questions/thoughts from attendees
1. Overall impressions
2. 2-3 most important/interesting things you learned?
3. Anything you'd do different?
4. Questions

## Task 4: Challenge: Implement the Intervention Agent

### 4.1 Completing the agent based on techniques learned with data agent task
1. Set up telemetry exporters
2. Set up McpToolset for GCS MCP server
3. Add the toolset to your agent
4. Create an A2A application object

### 4.2 Add additional tools
1. Review documentation, and add a VertexAiSearchTool
2. Add the generate_pdf_from_template tool

### 4.3 Test locally based on techniques learned with data agent asks
1. Run A2A inspector
2. Connect to locally running agent
3. Run 1-2 conversations
4. Check to see everything is working

### 4.4 Deploy and test on Cloud Run
1. Create the deployment script based
2. Populate environment variables run run script
3. Validate deployment
4. Test Cloud Run hosted agent

### 4.5 Complete the Improvement script and test
1. Complete the prompt
2. Based on what you did in Task 3, create
   1. The http client
   2. The remote agent
   3. The agent tool
3. Add the tool to the agent
4. Deploy the agent to agent engine
5. Test the whole workflow

## 4.6 Review

### Questions/thoughts from attendees
1. Overall impressions
2. 2-3 most important/interesting things you learned?
3. Anything you'd do different?
4. Questions