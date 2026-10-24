# ADK telemetry setup on ADK 2.x

This guide is a companion to [ADK telemetry setup, explained](adk-telemetry-explained.md). That guide covers ADK 1.26.0, the version pinned in `agents/data_agent/requirements.txt`. This one covers what changes when you move the same code to ADK 2.9.2, the latest release on PyPI as of September 22, 2026.

Read the first guide before this one. It defines the terms used here, such as exporter, OTLP, provider, resource, and monitored resource. The two setup versions are the same as in that guide:

- **Version A** is the code in `agents/data_agent/agent.py`. It passes scoped credentials and a resource built by `get_gcp_resource`.
- **Version B** is the short form that calls `get_gcp_exporters` with flags only and `maybe_set_otel_providers` with hooks only.

## Summary

Version A works on ADK 2.9.2 without any code change. Two things around it do change.

1. **Install the `gcp` extra.** A plain `pip install google-adk` no longer includes the OTLP exporter package. Version A crashes at import time with `ModuleNotFoundError` until you install `google-adk[gcp]`.
2. **Version B is now broken everywhere.** All three signals go over OTLP to `telemetry.googleapis.com`, and that endpoint rejects any payload whose resource lacks the `gcp.project_id` attribute. Only `get_gcp_resource` sets it. On 1.26.0 this already broke Version B's traces. On 2.9.2 it also breaks logs and metrics.

There is also one upside. ADK 2.x records its own metrics, so `enable_cloud_metrics=True` now produces data without any extra instrumentation package.

## What changed in the code

The table compares `google/adk/telemetry/google_cloud.py` and `setup.py` between the two versions. The source of each claim is listed at the end of this guide.

| Area | ADK 1.26.0 | ADK 2.9.2 |
|---|---|---|
| Packages installed by default | OTLP exporter, GCP exporters, and GCP resource detector are hard dependencies | All of them moved to the `gcp` extra. `google-adk[gcp]` restores them |
| Trace export | OTLP over HTTP to `telemetry.googleapis.com/v1/traces`, using the credentials object | Same |
| Log export | `CloudLoggingExporter` from the google-cloud-logging library, finding its own credentials | OTLP over HTTP to `telemetry.googleapis.com/v1/logs`, using the credentials object |
| Metric export | `CloudMonitoringMetricsExporter`, finding its own credentials | OTLP over HTTP to `telemetry.googleapis.com/v1/metrics`, using the credentials object |
| Metrics recorded by ADK itself | None | Agent and tool durations, call counts, token counts. See the list under "Metrics" |
| Log name environment variable | `GOOGLE_CLOUD_DEFAULT_LOG_NAME` | `GCP_DEFAULT_LOG_NAME`. Default is still `adk-otel` |
| Resource from `get_gcp_resource` | `gcp.project_id` plus detector output | Adds `service.instance.id` (a random ID plus the process ID) and `cloud.account.id`. Detects Vertex AI Agent Engine when its environment variables are present |
| Log record processing | Plain batch processor | A subclass that sets a `gcp.log_name` attribute, copies `service.version` to a label, and handles Agent Engine log naming |
| Event logger provider | Installed alongside the logger provider | Removed |
| Mutual TLS | Not supported | Supported through the `GOOGLE_API_USE_CLIENT_CERTIFICATE` and `GOOGLE_API_USE_MTLS_ENDPOINT` variables |
| Meter provider shutdown | Default | `shutdown_on_exit=False`, so the final flush at process exit is skipped |
| Hooks list handling | Appended the env-var exporters to the caller's list, mutating it | Copies the list first |

### The `gcp` extra

A pip "extra" is an optional group of dependencies you request with square brackets. On 2.9.2 the telemetry packages sit behind two extras:

| Extra | Adds |
|---|---|
| `gcp` | OTLP HTTP exporter, GCP trace, logging, and monitoring exporters, and the GCP resource detector |
| `otel-gcp` | The Gemini, gRPC, and httpx instrumentation libraries |

For Version A you need `gcp`. The `otel-gcp` extra adds per-request instrumentation on top of the metrics ADK now records itself.

### Why the log path change matters

On 1.26.0 the log exporter built its own client and never touched the credentials you passed. That is why, in the first guide's test, Version B still delivered logs when its traces failed on an unscoped service account key. On 2.9.2 the log exporter uses the same authorized session pattern as the trace exporter, so the same credential problem now takes out logs too.

## What changed in behavior

Each item below was tested on September 22, 2026 against ADK 2.9.2, using the same procedure as the first guide.

### A bare install crashes at setup

With `pip install google-adk==2.9.2` and nothing else, calling `get_gcp_exporters(enable_cloud_tracing=True)` fails before any exporter is built:

```
ModuleNotFoundError: No module named 'opentelemetry.exporter'
```

The trace exporter imports the OTLP package without a guard. The log and metric exporters do have guards and would log a warning and return nothing instead. After `pip install "google-adk[gcp]==2.9.2"` the import succeeds.

### Service account key file, local run

Setup: `GOOGLE_APPLICATION_CREDENTIALS` pointing at a fresh service account key, one span and one log record per version, then read back with a separate account.

| | Version A | Version B |
|---|---|---|
| Span exporter | `OTLPSpanExporter`, scoped credentials | `OTLPSpanExporter`, unscoped credentials |
| Log exporter | `OTLPLogExporter`, scoped credentials | `OTLPLogExporter`, unscoped credentials |
| Trace arrived in Cloud Trace | Yes | No |
| Log entry arrived in Cloud Logging | Yes | No |

Version B failed with the same `invalid_scope` error as on 1.26.0, but this time for both exporters:

```
Exception while exporting Span.
google.auth.exceptions.RefreshError: ('invalid_scope: Invalid OAuth scope or
ID token audience provided.', ...)

Exception while exporting Log.
google.auth.exceptions.RefreshError: ('invalid_scope: ...', ...)
```

The log error printed only when the log exporter ran on its own. In the combined run only the span error printed, yet the log record was still lost. Do not rely on the console to tell you logs are failing.

### Cloud Run

Setup: two Cloud Run services in `us-central1`, each with a Version B revision and then a Version A revision, running with the metadata server's credentials. Each revision emitted one span and one log record.

| | Version A | Version B |
|---|---|---|
| Trace arrived in Cloud Trace | Yes | No |
| Log entry arrived in Cloud Logging | Yes | No |
| Container stderr | Clean | `Failed to export span batch code: 400` and `Failed to export logs batch code: 400` |

Version B's OTel resource was empty, exactly as on 1.26.0. The difference is that on 2.9.2 the log exporter also goes to the endpoint that rejects it.

The Version A log entries look different from 1.26.0:

| Field | ADK 1.26.0 | ADK 2.9.2 |
|---|---|---|
| `resource.type` | `generic_task` | `generic_task` |
| `resource.labels.job` | Service name | Service name |
| `resource.labels.location` | `us-central1` | `us-central1` |
| `resource.labels.task_id` | Cloud Run instance ID, from `faas.instance` | ADK's `service.instance.id`, a random ID plus process ID |
| `resource.labels.namespace` | Empty string | Key absent |
| Revision name | Absent | Absent |

Two things explain the differences. First, `get_gcp_resource` now sets `service.instance.id`, and the task ID mapping prefers that over `faas.instance`. Second, the mapping now happens on Google's side of the OTLP endpoint rather than in the exporter library, and the server omits empty label keys instead of writing empty strings.

### The 400 is about `gcp.project_id`

To isolate the cause, the same Version B setup was run locally with a user login, which has no scope problem, while capturing the response body:

| OTel resource | HTTP status | Response body |
|---|---|---|
| Empty | 400 | `Resource is missing required attribute "gcp.project_id"` |
| `service.name` only | 400 | Same |
| `gcp.project_id` only | 200 | Empty |

Both the trace and log exporters returned the same result in each row. So Version B works on 2.9.2 if, and only if, something else puts `gcp.project_id` on the resource. The cheapest way is the standard OTel environment variable:

```
OTEL_RESOURCE_ATTRIBUTES=gcp.project_id=YOUR_PROJECT_ID
```

Replace `YOUR_PROJECT_ID` with the project that should receive the telemetry. `maybe_set_otel_providers` reads this variable even when you pass no resource.

### This also applies to ADK 1.26.0 traces

The same local experiment on 1.26.0 gave the same 400 for the trace exporter, and the earlier Cloud Run test on 1.26.0 shows no Version B spans in Cloud Trace. The first guide's claim that Version B "works on a laptop" was wrong for traces on both versions. It was right only for 1.26.0 logs, which used a different exporter. The first guide has been corrected.

## Metrics

ADK 2.9.2 creates a meter named `gcp.vertex.agent` and records these instruments during agent runs:

| Instrument | Kind |
|---|---|
| `gen_ai.invoke_agent.duration` | Histogram, seconds |
| `gen_ai.invoke_workflow.duration` | Histogram, seconds |
| `gen_ai.execute_tool.duration` | Histogram, seconds |
| `gen_ai.invoke_agent.inference_calls` | Histogram |
| `gen_ai.invoke_agent.tool_calls` | Histogram |
| `adk.experimental.invoke_agent.input_tokens`, `output_tokens`, `total_tokens`, `cache_read.input_tokens`, `reasoning.output_tokens`, `tool.input_tokens` | Histograms |
| `adk.experimental.invoke_workflow.*` | The same set for workflows |
| `adk.experimental.skill.loads`, `adk.experimental.skill.script.executions` | Counters |

The `gen_ai.*` names follow the OpenTelemetry semantic conventions for generative AI. The `adk.experimental.*` names may change.

Metrics are recorded from the runner, the base agent, and the LLM flow, so ADK's own instruments appear only when an agent actually runs. Delivery of the metric pipeline itself was tested on September 22, 2026 by recording one hand-made counter and flushing, on a laptop with a user login:

| Setup | ADK 1.26.0 | ADK 2.9.2 |
|---|---|---|
| Exporter | `CloudMonitoringMetricsExporter` | `OTLPMetricExporter` to `telemetry.googleapis.com/v1/metrics` |
| Empty or env-only resource | Arrived, as `generic_node` under `workload.googleapis.com/` | HTTP 400, `Resource is missing required attribute "gcp.project_id"` |
| Plus `gcp.project_id` | Not needed | HTTP 400, `prometheus_target resource type must have an instance specified` |
| Plus `service.instance.id` | Not needed | HTTP 400, `Unrecognized region or location` |
| Plus `cloud.region` | Not needed | HTTP 200. Arrived as `prometheus_target` under `prometheus.googleapis.com/`, with a `/counter` suffix on the name |

So on 2.9.2 the metrics endpoint needs three resource attributes: `gcp.project_id`, `service.instance.id`, and a region. `get_gcp_resource` supplies the first two everywhere, and the GCP resource detector supplies the region on Cloud Run, GKE, and Compute Engine. On a laptop, Version A with metrics enabled fails until you add `OTEL_RESOURCE_ATTRIBUTES=cloud.region=us-central1` or similar. Delivery from Cloud Run was not tested, and is inferred from the detector's output seen in the Cloud Run log test.

The storage change matters for dashboards. On 1.26.0 a counter named `my_counter` is stored as `workload.googleapis.com/my_counter` on a generic resource. On 2.9.2 it becomes `prometheus.googleapis.com/my_counter/counter` on a `prometheus_target` resource, whose `job` label comes from `service.name` and `instance` label from `service.instance.id`. Any Cloud Monitoring query or alert written against the 1.x names has to be rewritten.

One related setting: `ADK_TELEMETRY_SCHEMA_VERSION_OPT_IN=2` switches from the legacy span layout to one aligned with the semantic conventions, replacing the top-level `invocation` span with an `invoke_workflow` span and duration metric. The default is the legacy layout everywhere except Agent Engine.

## The three documentation snippets

The ADK documentation shows one snippet per signal. Each enables a single flag, sets `OTEL_SERVICE_NAME` and `OTEL_RESOURCE_ATTRIBUTES` through `os.environ`, and calls `maybe_set_otel_providers` with no resource:

```python
gcp_exporters = get_gcp_exporters(
  enable_cloud_logging = True,   # or enable_cloud_tracing, or enable_cloud_metrics
)
os.environ["OTEL_SERVICE_NAME"] = "your-adk-agent"
os.environ["OTEL_RESOURCE_ATTRIBUTES"] = "key1=value1,key2=value2"
maybe_set_otel_providers([gcp_exporters])
```

The environment variables reach the resource because `maybe_set_otel_providers` runs the OTel environment detector when called. Setting them before that call is what matters. Each snippet was run as written on September 22, 2026, on a laptop with a user login, and the results read back:

| Snippet | ADK 1.26.0 | ADK 2.9.2 as written | ADK 2.9.2 with attributes added |
|---|---|---|---|
| Logging | Arrives | 400 | Arrives after adding `gcp.project_id` |
| Tracing | 400 | 400 | Arrives after adding `gcp.project_id` |
| Metrics | Arrives | 400 | Arrives after adding `gcp.project_id`, `service.instance.id`, and `cloud.region` |

Two details from those runs:

- The `key1` and `key2` attributes never appeared on any log entry or time series. Neither exporter route turns arbitrary resource attributes into labels. Only attributes with a known mapping, such as `service.name`, `service.instance.id`, `service.namespace`, `cloud.region`, and `gcp.project_id`, have any effect.
- `OTEL_SERVICE_NAME` alone does not get the service name onto a log entry. The mapping to `generic_task` needs an instance ID as well. Without one, the entry is a `generic_node` and the name is dropped.

The tracing snippet fails on both versions. It appears to work in documentation because the failure is a background log line, and the logging and metrics snippets on 1.x cover the same missing attribute by using exporters that don't check for it.

### A snippet-style setup that works on both versions

This keeps the documentation style, no `get_gcp_resource` and no credentials tuple, and adds the three attributes the endpoints require. It was run on ADK 1.26.0 on September 22, 2026 with all three flags on, and the span, log entry, and counter all arrived. The log entry and time series were filed as `generic_task` with the job, location, and instance labels filled in.

```python
import os

from google.adk.telemetry.google_cloud import get_gcp_exporters
from google.adk.telemetry.setup import maybe_set_otel_providers

PROJECT_ID = os.environ["GOOGLE_CLOUD_PROJECT"]

# These must be set before maybe_set_otel_providers runs. gcp.project_id is what the
# trace endpoint requires on both versions. The other two are ignored by the 1.x log
# and metric exporters but required by the 2.x ones, so the same code survives an upgrade.
os.environ.setdefault("OTEL_SERVICE_NAME", "your-adk-agent")
os.environ.setdefault(
    "OTEL_RESOURCE_ATTRIBUTES",
    f"gcp.project_id={PROJECT_ID},service.instance.id={os.getpid()},cloud.region=us-central1",
)

gcp_exporters = get_gcp_exporters(
    enable_cloud_tracing=True,
    enable_cloud_metrics=True,
    enable_cloud_logging=True,
)
maybe_set_otel_providers([gcp_exporters])
```

Replace `us-central1` with the region you deploy to. The process ID is a good enough instance ID on a laptop. On Cloud Run, the `K_REVISION` environment variable plus the process ID is more useful.

This still relies on `google.auth.default()` finding credentials that don't need scopes. With a service account key file, use the Version A form and pass scoped credentials.

## What to change when upgrading the data agent

1. In `requirements.txt`, replace `google-adk[a2a]==1.26.0` with `google-adk[a2a,gcp]==2.9.2`. Without `gcp` the telemetry block crashes at import.
2. Keep the Version A telemetry block as it is. It passes scoped credentials and a resource with `gcp.project_id`, which is exactly what 2.9.2 requires.
3. Optional: add `enable_cloud_metrics=True` to the `get_gcp_exporters` call. On 1.26.0 this was pointless without an extra package. On 2.9.2 it exports the metrics listed above. Give the runtime service account the Monitoring Metric Writer role. On Cloud Run the resource detector supplies the region the metrics endpoint requires. For local runs, also set `OTEL_RESOURCE_ATTRIBUTES=cloud.region=us-central1` or the export fails with `Unrecognized region or location`.
4. If anything reads `GOOGLE_CLOUD_DEFAULT_LOG_NAME`, rename it to `GCP_DEFAULT_LOG_NAME`.
5. Drop the explicit pins on `opentelemetry-exporter-gcp-trace`, `opentelemetry-exporter-gcp-logging`, and `opentelemetry-sdk`. The `gcp` extra pins compatible versions, and 2.9.2 caps the SDK at 1.42.1.

The two optional refinements from the first guide still apply. Passing `PROJECT_ID` into the credentials tuple is now more valuable, because on 2.9.2 the exporters, the resource, and the endpoint's project check all need to agree on the same project.

## A note on `adk web --otel_to_cloud`

The ADK CLI's own telemetry setup on 2.9.2 calls `google.auth.default()` with no scopes, passes the result to `get_gcp_exporters` with all three signals enabled, and passes `get_gcp_resource(project_id)`. That is Version A's resource handling with Version B's credential handling. From the source, running the CLI with a service account key file would hit the `invalid_scope` failure. This was not tested.

## Where these facts come from

| Claim | Source |
|---|---|
| Telemetry packages moved to the `gcp` extra | `google_adk-2.9.2.dist-info/METADATA`, `Requires-Dist` lines with `extra == "gcp"` |
| Bare install crashes on the trace exporter import | Test output above. `google_cloud.py`, `_get_gcp_span_exporter`, has no import guard |
| Logs and metrics now use OTLP with the credentials object | `google_cloud.py`, `_get_gcp_logs_exporter` and `_get_gcp_otlp_metric_exporter` build an `AuthorizedSession` |
| Endpoint URLs | `google_cloud.py`, the `_DEFAULT_TELEMETRY_*_ENDPOINT` constants |
| Log name variable renamed | `google_cloud.py`, `_GCP_DEFAULT_LOG_NAME = "GCP_DEFAULT_LOG_NAME"` |
| `service.instance.id` and `cloud.account.id` on the resource | `google_cloud.py`, `get_gcp_resource` |
| Log processor rewrites | `google_cloud.py`, `GCPBatchLogRecordProcessor.on_emit` |
| Event logger provider removed | `setup.py` diff, the `_events` imports and calls are gone |
| Metric export interval | `_agent_engine_metric_exporter.py`, `MIN_EXPORT_INTERVAL_MS = 5000.0` |
| Metric instrument names | `telemetry/_metrics.py` |
| Where metrics are recorded | `runners.py`, `agents/base_agent.py`, and `flows/llm_flows/base_llm_flow.py` import `telemetry/_instrumentation.py` |
| Schema version opt-in | `telemetry/_schema_version.py`, `resolve_schema_version` |
| CLI telemetry wiring | `cli/api_server.py`, the block calling `get_gcp_exporters` |
| 400 response body | Test output above, captured by wrapping each exporter's `_export` method |
| 2.9.0 and 2.9.2 telemetry source are the same except one comment and one condition in the log processor | `diff` of `google_cloud.py` and `setup.py` between the two installs |
