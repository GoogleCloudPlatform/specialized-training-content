# Enabling Cloud Trace & Content Logging on Cloud Run

When you deploy to **Agent Engine**, tracing and content logging are handled
automatically. On **Cloud Run** you need to wire up the OpenTelemetry pipeline
yourself. ADK >= 1.17.0 has built-in OTel support, so the changes are small.

---

## What Agent Engine gives you for free

| Capability | Agent Engine | Cloud Run (default) |
|---|---|---|
| Distributed tracing (Cloud Trace) | Automatic | Not configured |
| Content logging (LLM inputs/outputs) | Automatic | Not configured |
| Span labels (`invocation`, `agent_run`, `call_llm`, `execute_tool`) | Automatic | Requires OTel setup |

The goal is to close this gap with minimal changes.

---

## Step 1 — Add OpenTelemetry dependencies

Add these packages to `requirements.txt`:

```diff
 google-cloud-aiplatform==1.139.0
 google-adk[a2a]==1.26.0
 google-auth==2.48.0
 google-genai==1.65.0
 python-dotenv==1.2.1
+opentelemetry-exporter-gcp-trace
+opentelemetry-exporter-otlp-proto-grpc
+opentelemetry-instrumentation-google-genai>=0.4b0
```

- **`opentelemetry-exporter-gcp-trace`** — exports spans to Cloud Trace.
- **`opentelemetry-exporter-otlp-proto-grpc`** — required by ADK's built-in
  OTel pipeline for the OTLP gRPC protocol.
- **`opentelemetry-instrumentation-google-genai`** — auto-instruments Gemini
  API calls so they appear as spans with request/response content.

---

## Step 2 — Configure tracing in `agent.py`

Add an OpenTelemetry `TracerProvider` that exports to Cloud Trace. This block
should go **near the top of the file**, after imports and before the agent
definition.

```diff
 import os
 from functools import cached_property

 from dotenv import load_dotenv

 load_dotenv()

+from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
+from opentelemetry.sdk.trace import TracerProvider
+from opentelemetry.sdk.trace.export import BatchSpanProcessor
+
 from fastapi.openapi.models import (OAuth2, OAuthFlowClientCredentials,
                                     OAuthFlows)
 ...
```

Then, before `root_agent` is defined, initialize the tracer:

```diff
+# --- OpenTelemetry tracing to Cloud Trace ---
+_tracer_provider = TracerProvider()
+_tracer_provider.add_span_processor(
+    BatchSpanProcessor(
+        CloudTraceSpanExporter(project_id=PROJECT_ID)
+    )
+)

 # --- Agent definition ---
 root_agent = LlmAgent(
     model=Gemini3(model="gemini-3-flash-preview"),
     ...
 )
```

### Full modified `agent.py` (relevant sections only)

```python
import os
from functools import cached_property

from dotenv import load_dotenv

load_dotenv()

from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from fastapi.openapi.models import (OAuth2, OAuthFlowClientCredentials,
                                    OAuthFlows)
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from google.adk.agents.llm_agent import LlmAgent
from google.adk.auth.auth_credential import (AuthCredential,
                                             AuthCredentialTypes,
                                             ServiceAccount)
from google.adk.models import Gemini
from google.adk.tools.mcp_tool.mcp_session_manager import \
    StreamableHTTPConnectionParams
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset
from google.genai import Client, types
from vertexai import agent_engines

# --- Environment configuration ---
PROJECT_ID = os.environ["GOOGLE_CLOUD_PROJECT"]
HOST = os.environ["CLOUD_RUN_HOST"]

# --- OpenTelemetry tracing to Cloud Trace ---
_tracer_provider = TracerProvider()
_tracer_provider.add_span_processor(
    BatchSpanProcessor(
        CloudTraceSpanExporter(project_id=PROJECT_ID)
    )
)

# ... (BigQuery toolset, system prompt, Gemini3 class unchanged) ...

# --- Agent definition ---
root_agent = LlmAgent(
    model=Gemini3(model="gemini-3-flash-preview"),
    name="data_agent",
    description=(
        "Cymbal Meet data domain expert. Accepts natural language questions "
        "about customer engagement, translates to SQL, executes via BigQuery, "
        "returns structured results."
    ),
    instruction=DATA_AGENT_INSTRUCTION,
    tools=[_create_bigquery_mcp_toolset()],
)

app = agent_engines.AdkApp(
    agent=root_agent,
    enable_tracing=True,  # <-- ADD THIS
)
```

> **Key change**: pass `enable_tracing=True` to `AdkApp`. This tells ADK to
> use the active `TracerProvider` for its internal spans (`invocation`,
> `agent_run`, `call_llm`, `execute_tool`).

---

## Step 3 — Add environment variables to `deploy_to_run.sh`

These env vars enable content capture in the GenAI instrumentation spans:

```diff
 gcloud run deploy $AGENT_SERVICE_NAME \
     --port=8080 \
     --source=. \
     --allow-unauthenticated \
     --region="us-central1" \
     --project=$GOOGLE_CLOUD_PROJECT \
     --service-account $AGENT_SA \
     --set-env-vars=\
 GOOGLE_CLOUD_PROJECT=$GOOGLE_CLOUD_PROJECT,\
 GOOGLE_CLOUD_LOCATION=$GOOGLE_CLOUD_LOCATION,\
-GOOGLE_GENAI_USE_VERTEXAI=true
+GOOGLE_GENAI_USE_VERTEXAI=true,\
+OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED=true,\
+OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=true
```

| Variable | Purpose |
|---|---|
| `OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED` | Enables automatic OTel log correlation |
| `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT` | Captures the full LLM prompt/response text in spans (equivalent to Agent Engine's content logging) |

---

## Step 4 — Ensure the service account has permissions

The service account (`cymbal-agent`) used by the Cloud Run service needs:

- **`roles/cloudtrace.agent`** — to write traces to Cloud Trace

```bash
gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
    --member="serviceAccount:cymbal-agent@${GOOGLE_CLOUD_PROJECT}.iam.gserviceaccount.com" \
    --role="roles/cloudtrace.agent"
```

This is likely already granted if the SA has `roles/editor` or broad platform
access, but it's good to verify.

---

## Step 5 — No Dockerfile changes required

The existing Dockerfile doesn't need modification. The OTel packages are
pulled in via `requirements.txt`, and the tracing is initialized in Python
code at import time. No extra CLI flags or entrypoint changes are needed.

---

## Viewing traces

After deploying, traces appear in the Google Cloud Console:

1. Go to **Trace Explorer**: `console.cloud.google.com/traces`
2. Select your project (`jwd-atf-int`)
3. Filter by service name `data-agent`

You'll see spans labeled:
- **`invocation`** — the full request lifecycle
- **`agent_run`** — the agent's reasoning loop
- **`call_llm`** — each Gemini API call (with prompt/response content if
  `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=true`)
- **`execute_tool`** — each MCP tool invocation

---

## Summary of changes

| File | Change |
|---|---|
| `requirements.txt` | Add 3 OpenTelemetry packages |
| `agent.py` | Add OTel imports, create `TracerProvider` with `CloudTraceSpanExporter`, pass `enable_tracing=True` to `AdkApp` |
| `deploy_to_run.sh` | Add 2 env vars for content capture |
| IAM | Grant `roles/cloudtrace.agent` to the service account |
| `Dockerfile` | No changes |

---

## Alternative: `adk deploy cloud_run`

If you prefer not to manage the Dockerfile and deploy script yourself, ADK's
CLI can handle everything in one command:

```bash
adk deploy cloud_run \
    --project=$GOOGLE_CLOUD_PROJECT \
    --region=$GOOGLE_CLOUD_LOCATION \
    --trace_to_cloud \
    ./data_agent
```

This generates a Dockerfile with tracing baked in and deploys directly. The
trade-off is less control over the Cloud Run service configuration (e.g.,
`--allow-unauthenticated`, custom service account, etc.).
