# Enabling Cloud Trace & Content Logging on Cloud Run

When you deploy to **Agent Engine**, tracing and content logging are handled
automatically. On **Cloud Run** with `to_a2a()`, you need to wire up the
OpenTelemetry pipeline yourself.

---

## Background: how ADK tracing works

ADK's internal tracing (`invocation`, `agent_run`, `call_llm`, `execute_tool`
spans) comes from a **module-level tracer** in `google.adk.telemetry.tracing`:

```python
# inside ADK internals
tracer = trace.get_tracer("gcp.vertex.agent", ...)
```

This uses whatever `TracerProvider` is **globally registered** via
`trace.set_tracer_provider()`. If no global provider is set, spans are
silently discarded.

### What doesn't work: manual `GoogleGenAiSdkInstrumentor`

Calling `GoogleGenAiSdkInstrumentor().instrument()` directly wraps GenAI SDK
response objects with instrumentation proxies. This **breaks the A2A part
converter** — it can no longer access `part.text`, `part.function_call`, etc.
on the wrapped objects, causing:

```
a2a_parts = part_converter(part)
Error on session runner task: unhandled errors in a TaskGroup (1 sub-exception)
```

The agent then hangs indefinitely.

### What works: ADK's built-in telemetry helpers

ADK provides its own telemetry setup functions that configure tracing without
conflicting with the A2A pipeline:

- `google.adk.telemetry.google_cloud.get_gcp_exporters()` — returns
  Cloud Trace span processors wrapped in an `OTelHooks` dataclass
- `google.adk.telemetry.google_cloud.get_gcp_resource()` — creates an
  OTel `Resource` with GCP-specific attributes (project ID, Cloud Run
  environment detection)
- `google.adk.telemetry.setup.maybe_set_otel_providers()` — safely
  registers the `TracerProvider` globally (calls
  `trace.set_tracer_provider()` internally)

These functions set up the global provider that ADK's internal tracer uses,
without monkey-patching the GenAI SDK response types.

---

## What Agent Engine gives you for free

| Capability                                                          | Agent Engine | Cloud Run (default) |
| ------------------------------------------------------------------- | ------------ | ------------------- |
| Distributed tracing (Cloud Trace)                                   | Automatic    | Not configured      |
| Content logging (LLM inputs/outputs)                                | Automatic    | Not configured      |
| Span labels (`invocation`, `agent_run`, `call_llm`, `execute_tool`) | Automatic    | Requires OTel setup |

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
+opentelemetry-sdk
```

- **`opentelemetry-exporter-gcp-trace`** — provides `CloudTraceSpanExporter`,
  used internally by `get_gcp_exporters()`.
- **`opentelemetry-sdk`** — provides `TracerProvider`, `BatchSpanProcessor`,
  and `Resource`.

> **Note:** Do NOT add `opentelemetry-instrumentation-google-genai`. The
> `GoogleGenAiSdkInstrumentor` it provides is incompatible with `to_a2a()`.

---

## Step 2 — Configure tracing in `agent.py`

Add ADK's telemetry setup **before** the agent definition and `to_a2a()`
call. The key is using ADK's own helpers rather than raw OTel APIs.

### Imports to add

```diff
+from google.adk.telemetry.google_cloud import get_gcp_exporters, get_gcp_resource
+from google.adk.telemetry.setup import maybe_set_otel_providers
```

### Tracing initialization block

Place this after `PROJECT_ID` is set and before the agent definition:

```python
# --- OpenTelemetry tracing to Cloud Trace ---
_gcp_exporters = get_gcp_exporters(enable_cloud_tracing=True)
_gcp_resource = get_gcp_resource(project_id=PROJECT_ID)
maybe_set_otel_providers(
    otel_hooks_to_setup=[_gcp_exporters],
    otel_resource=_gcp_resource,
)
```

### Full `agent.py` (relevant sections)

```python
import os
from functools import cached_property

from dotenv import load_dotenv

load_dotenv()

from fastapi.openapi.models import (OAuth2, OAuthFlowClientCredentials,
                                    OAuthFlows)
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from google.adk.agents.llm_agent import LlmAgent
from google.adk.auth.auth_credential import (AuthCredential,
                                             AuthCredentialTypes,
                                             ServiceAccount)
from google.adk.models import Gemini
from google.adk.telemetry.google_cloud import get_gcp_exporters, get_gcp_resource
from google.adk.telemetry.setup import maybe_set_otel_providers
from google.adk.tools.mcp_tool.mcp_session_manager import \
    StreamableHTTPConnectionParams
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset
from google.genai import Client, types

# --- Environment configuration ---
PROJECT_ID = os.environ["GOOGLE_CLOUD_PROJECT"]

# --- OpenTelemetry tracing to Cloud Trace ---
_gcp_exporters = get_gcp_exporters(enable_cloud_tracing=True)
_gcp_resource = get_gcp_resource(project_id=PROJECT_ID)
maybe_set_otel_providers(
    otel_hooks_to_setup=[_gcp_exporters],
    otel_resource=_gcp_resource,
)

# --- BigQuery MCP toolset ---
# ... (unchanged) ...

# --- Agent definition ---
root_agent = LlmAgent(
    model=Gemini3(model="gemini-3-flash-preview"),
    name="data_agent",
    # ... (unchanged) ...
)

a2a_app = to_a2a(
    root_agent,
    agent_card="agent_card.json",
)
```

### What this does

- `get_gcp_exporters(enable_cloud_tracing=True)` — creates a
  `BatchSpanProcessor` wrapping a `CloudTraceSpanExporter`. Uses ADC
  (`google.auth.default()`) to authenticate. Returns an `OTelHooks`
  dataclass.
- `get_gcp_resource(project_id=PROJECT_ID)` — creates an OTel `Resource`
  with `gcp.project_id` set, and auto-detects Cloud Run environment
  attributes (service name, revision, etc.) via `GoogleCloudResourceDetector`.
- `maybe_set_otel_providers(...)` — creates a `TracerProvider` with the
  resource and span processors, then calls `trace.set_tracer_provider()` to
  register it globally. ADK's module-level tracer immediately picks it up.

### What this does NOT do

- Does NOT monkey-patch GenAI SDK response objects
- Does NOT wrap `Part` types with instrumentation proxies
- Does NOT conflict with the A2A `part_converter`

ADK's internal spans (`invocation`, `agent_run`, `call_llm`, `execute_tool`)
are still emitted because they come from ADK's own tracer, which now has a
real provider behind it. The LLM request/response content is captured in the
`call_llm` span attributes by ADK's own `trace_call_llm()` function — no
external instrumentor needed.

---

## Step 3 — Add environment variables to `deploy_to_run.sh`

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
+OTEL_SERVICE_NAME=data-agent
```

| Variable            | Purpose                                                                                                                                       |
| ------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| `OTEL_SERVICE_NAME` | Sets the service name on trace spans, making them filterable in Trace Explorer. Picked up by `get_gcp_resource()` via `OTELResourceDetector`. |

> Content logging: ADK's `trace_call_llm()` captures LLM request/response
> content directly in span attributes. This is controlled by the
> `ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS` env var (defaults to `false` for
> privacy). Set it to `true` if you want full prompt/response content in
> Cloud Trace:
>
> ```
> ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS=true
> ```

---

## Step 4 — Ensure the service account has permissions

The service account (`cymbal-agent`) needs:

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
  `ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS=true`)
- **`execute_tool`** — each MCP tool invocation

---

## Summary of changes

| File               | Change                                                                                             |
| ------------------ | -------------------------------------------------------------------------------------------------- |
| `requirements.txt` | Add `opentelemetry-exporter-gcp-trace` and `opentelemetry-sdk`                                     |
| `agent.py`         | Add 3-line tracing setup using `get_gcp_exporters`, `get_gcp_resource`, `maybe_set_otel_providers` |
| `deploy_to_run.sh` | Add `OTEL_SERVICE_NAME` env var (optionally `ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS`)                |
| IAM                | Grant `roles/cloudtrace.agent` to the service account                                              |
| `Dockerfile`       | No changes                                                                                         |
