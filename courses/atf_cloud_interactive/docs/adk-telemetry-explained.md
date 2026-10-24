# ADK telemetry setup, explained

This guide compares two ways to turn on Google Cloud telemetry in an ADK agent. It defines every term before using it, walks through what the code does when it runs, and tells you which version to use where.

All claims come from the ADK 1.26.0 source, the version pinned in `agents/data_agent/requirements.txt`. The relevant files are `google/adk/telemetry/google_cloud.py` and `google/adk/telemetry/setup.py`.

## The two versions

**Version A** is the code in `agents/data_agent/agent.py`, lines 52 to 66:

```python
_gcp_creds, _gcp_project = google.auth.default(
    scopes=["https://www.googleapis.com/auth/cloud-platform"],
)
_gcp_exporters = get_gcp_exporters(
    enable_cloud_tracing=True,
    enable_cloud_logging=True,
    google_auth=(_gcp_creds, _gcp_project),
)
_gcp_resource = get_gcp_resource(project_id=PROJECT_ID)
maybe_set_otel_providers(
    otel_hooks_to_setup=[_gcp_exporters],
    otel_resource=_gcp_resource,
)
```

**Version B** is the shorter form from the ADK documentation:

```python
from google.adk.telemetry import google_cloud
from google.adk.telemetry.setup import maybe_set_otel_providers

hooks = google_cloud.get_gcp_exporters(
    enable_cloud_tracing=True, enable_cloud_metrics=True, enable_cloud_logging=True
)
maybe_set_otel_providers(otel_hooks_to_setup=[hooks])
```

Both call the same two ADK functions. They differ in what they pass in. The short answer is that Version A is what you want everywhere. Version B delivers logs but never traces, because the trace endpoint rejects its empty resource. The rest of this guide explains why.

A companion guide, [ADK telemetry setup on ADK 2.x](adk-telemetry-2x-changes.md), covers what changes on ADK 2.9.2.

## Vocabulary

Read these definitions first. The rest of the guide uses each term without re-explaining it.

### Telemetry

Telemetry is the data an application emits about its own behavior so that you can see what it did after the fact. There are three kinds:

| Kind | What it records | Example from an ADK agent |
|---|---|---|
| Trace | The timeline of one request, broken into steps | "Agent run took 3.2 s. The Gemini call took 2.8 s of that. The BigQuery tool call took 0.3 s." |
| Log | A single event with a message and a timestamp | "Tool `list_datasets` returned 4 rows." |
| Metric | A number measured over time | "Input tokens per minute: 1,400." |

### Span and trace

A **span** is one timed step inside a request. It has a name, a start time, an end time, and attributes such as the model name. A **trace** is the tree of spans for one request. In the example above, the agent run is the parent span, and the Gemini call and the tool call are child spans.

### OpenTelemetry (OTel)

OpenTelemetry, usually shortened to OTel, is an open standard and a set of libraries for producing telemetry. ADK uses the OTel Python library to record spans and logs. Because OTel is vendor-neutral, the same recorded data can be sent to Google Cloud, Datadog, Jaeger, or a file, depending on how you configure it.

### Exporter

An **exporter** is the component that sends recorded telemetry somewhere. ADK ships three Google Cloud exporters:

| Exporter | Sends | To |
|---|---|---|
| Span exporter | Traces | Cloud Trace |
| Log exporter | Logs | Cloud Logging |
| Metric exporter | Metrics | Cloud Monitoring |

Exporters batch data and send it in the background, so they don't slow down the agent's request handling.

### OTLP

OTLP stands for OpenTelemetry Protocol. It's the wire format that OTel exporters use to send data over HTTP or gRPC. ADK's span exporter sends OTLP over HTTP to `https://telemetry.googleapis.com/v1/traces`, which is Google's endpoint that accepts OTLP directly. You don't need to know the format. You only need to know that "OTLP exporter" means "the standard OTel exporter, not a Google-specific one."

### Provider

A **provider** is the OTel object that owns the exporters for one kind of telemetry. There is a `TracerProvider`, a `MeterProvider`, and a `LoggerProvider`. Each process has one global provider per kind. Setting a provider is how you say "from now on, send all spans to these exporters." ADK's `maybe_set_otel_providers` function sets these global providers for you.

The "maybe" in the name means the function does nothing for a telemetry kind if a provider for that kind was already set. So if your web framework already set up tracing, ADK won't override it.

### Hooks

In ADK, `OTelHooks` is a small container that holds a list of span exporters, metric exporters, and log exporters. The function `get_gcp_exporters` returns one `OTelHooks` object. You pass a list of these to `maybe_set_otel_providers`, which unpacks them into the providers.

### Resource

An OTel **resource** is a set of key-value labels that describe the process emitting the telemetry. Every span, log, and metric from the process carries these labels. Examples:

```
service.name    = data-agent
cloud.platform  = gcp_cloud_run
cloud.region    = us-central1
faas.name       = data-agent
faas.version    = data-agent-00012-abc
gcp.project_id  = my-project
```

The resource is what lets you filter in the Cloud console by "show me only logs from the `data-agent` service in `us-central1`."

### Resource detector

A **resource detector** is code that inspects the environment and fills in resource labels automatically. Two detectors matter here:

- **OTELResourceDetector** reads the environment variables `OTEL_SERVICE_NAME` and `OTEL_RESOURCE_ATTRIBUTES`. It only knows what you tell it.
- **GoogleCloudResourceDetector** checks whether the process is running on Compute Engine, Kubernetes Engine, Cloud Run, or Cloud Functions, and fills in the platform-specific labels. On Cloud Run it detects the platform from the built-in `K_CONFIGURATION` environment variable, reads the service name and revision from `K_SERVICE` and `K_REVISION`, and queries the metadata server for the region and instance ID.

### Monitored resource

Google Cloud has its own concept called a **monitored resource**, which is the thing a log or metric is "about." Google keeps a fixed catalog of resource types, and each type has a fixed set of label keys:

| Type | Meant for | Label keys |
|---|---|---|
| `cloud_run_revision` | A Cloud Run revision | project_id, location, service_name, revision_name, configuration_name |
| `gce_instance` | A Compute Engine VM | project_id, zone, instance_id |
| `generic_task` | An application process with no better-fitting type | project_id, location, namespace, job, task_id |
| `generic_node` | A machine or compute resource with no better-fitting type | project_id, location, namespace, node_id |

The two generic types are catch-alls. A node is a place something runs. A task is a thing that runs.

The Google Cloud exporters translate OTel resource attributes into one of these types. Compute Engine and Kubernetes have explicit rules. Everything else, Cloud Run included, goes through a fallback rule: if the OTel resource has a service name (`service.name` or `faas.name`) and an instance ID (`service.instance.id` or `faas.instance`), the entry becomes a `generic_task`. Otherwise it becomes a `generic_node`.

Once the type is chosen, the exporter writes every label key in that type's schema. A key that no OTel attribute feeds gets an empty string, except `location`, which gets the literal value `global`.

### Credentials, tokens, and scopes

To call any Google API, the process must prove who it is. The pieces are:

- **Credentials** are the long-lived identity, such as a service account or a signed-in user.
- An **access token** is a short-lived string, valid for about an hour, that the process attaches to each API request. "Minting a token" means using the credentials to get a fresh access token from Google's token service.
- **Scopes** are permission categories a token is allowed to cover. `https://www.googleapis.com/auth/cloud-platform` is the broad scope that covers all Google Cloud APIs.

### Application Default Credentials (ADC)

ADC is Google's rule for finding credentials without hard-coding them. The function `google.auth.default()` runs this search and returns two things: a credentials object and a project ID. The search order is:

1. The file named by the `GOOGLE_APPLICATION_CREDENTIALS` environment variable, usually a service account key file.
2. The credentials saved by `gcloud auth application-default login` on a developer machine.
3. The metadata server on Google Cloud compute, which hands out tokens for the attached service account. This is what runs on Cloud Run.

Scopes behave differently in each case:

| Credential source | What scopes do |
|---|---|
| Service account key file | Required. Without scopes, the credentials can't mint a token and API calls fail. |
| `gcloud` developer login | Already carries `cloud-platform`. Passing scopes is harmless. |
| Cloud Run metadata server | Ignored. The token comes pre-scoped. |

## What happens when the code runs

Both versions run at import time, before the agent handles any request. Here is what each ADK function does, in order.

### Step 1: `get_gcp_exporters` builds the exporters

1. It resolves credentials and a project ID. If you passed the `google_auth` tuple, it uses that. Otherwise it calls `google.auth.default()` with no scopes.
2. If the project ID is empty, it logs a warning and returns an empty `OTelHooks`. Telemetry is then silently off. This happens on a developer machine when `gcloud` has no default project configured.
3. If `enable_cloud_tracing` is true, it builds a span exporter. This is the only exporter that receives the credentials object. It wraps them in an authorized HTTP session and points it at the Google OTLP trace endpoint.
4. If `enable_cloud_metrics` is true, it builds a metric exporter that pushes to Cloud Monitoring every 5 seconds. This exporter receives only the project ID and finds its own credentials through ADC.
5. If `enable_cloud_logging` is true, it builds a log exporter for Cloud Logging. It also receives only the project ID. Logs land in a log named `adk-otel` unless you set the `GOOGLE_CLOUD_DEFAULT_LOG_NAME` environment variable.

### Step 2: `get_gcp_resource` builds the resource (Version A only)

1. It starts with one label, `gcp.project_id`, set to whatever you passed.
2. It merges in labels from `OTELResourceDetector`, so `OTEL_SERVICE_NAME` and friends apply.
3. It merges in labels from `GoogleCloudResourceDetector`. On Cloud Run, this adds the platform, region, service name, revision, and instance labels shown in the resource example above.

Later labels override earlier ones. If `OTEL_RESOURCE_ATTRIBUTES` sets `gcp.project_id`, that wins over the argument.

### Step 3: `maybe_set_otel_providers` installs the providers

1. If you didn't pass `otel_resource`, it builds one using `OTELResourceDetector` only. Note the difference from step 2: no Google Cloud detection.
2. It checks the standard OTel environment variables such as `OTEL_EXPORTER_OTLP_ENDPOINT`. If any are set, it adds generic OTLP exporters alongside yours. This lets you also ship telemetry to a non-Google backend without code changes.
3. For each kind of telemetry that has at least one exporter, it creates the provider with the resource, attaches the exporters, and sets it as the global provider.
4. When logging is on, it also installs an event logger provider. ADK core doesn't use it directly. It exists so that the optional `opentelemetry-instrumentation-google-genai` package, described under difference 3, can write structured `gen_ai` events as log records.

## The differences, one at a time

### Difference 1: explicit credentials with scopes

Version A calls `google.auth.default(scopes=[...])` itself and hands the result to `get_gcp_exporters`. Version B lets ADK call `google.auth.default()` with no scopes.

**Why it matters.** Only the span exporter uses the credentials object. The log and metric exporters find credentials on their own. So this difference affects traces only, and only when ADC resolves to a service account key file. In that case, Version B's unscoped credentials can't mint a token, the trace exporter fails on every batch, and you see no traces. Version A works with all three credential sources.

**Example.** A student runs the agent locally with `GOOGLE_APPLICATION_CREDENTIALS` pointing at a downloaded key. With Version B, logs arrive in Cloud Logging but Cloud Trace stays empty, and the only clue is a background error from the exporter thread. With Version A, both arrive.

**Verified.** This was tested on September 21, 2026 with ADK 1.26.0, a fresh service account key, and one span plus one log record per version. The credentials object handed to the span exporter looked like this:

| | Version A | Version B |
|---|---|---|
| `credentials.scopes` | `['https://www.googleapis.com/auth/cloud-platform']` | `None` |
| `credentials.requires_scopes` | `False` | `True` |

Version B's span export failed inside the exporter's background thread with this error, and nothing else in the program noticed:

```
Exception while exporting Span.
google.auth.exceptions.RefreshError: ('invalid_scope: Invalid OAuth scope or
ID token audience provided.', {'error': 'invalid_scope', ...})
```

Reading the data back afterward with a separate account confirmed the outcome:

| Backend | Version A | Version B |
|---|---|---|
| Cloud Logging (`adk-otel` log) | Entry present | Entry present |
| Cloud Trace | Span present | Nothing |

The log exporter succeeded in both versions because it builds its own client and never touches the credentials object passed to `get_gcp_exporters`.

### Difference 2: the OTel resource

Version A builds a resource with `get_gcp_resource` and passes it in. Version B passes nothing, so `maybe_set_otel_providers` uses `OTELResourceDetector` alone.

**Why it matters.** This is the largest practical difference, and it has two parts.

The first part is that traces never arrive. The trace exporter posts to `telemetry.googleapis.com`, and that endpoint rejects any payload whose resource lacks `gcp.project_id`. Only `get_gcp_resource` sets that attribute. Without it, every span batch gets HTTP 400 with the body `Resource is missing required attribute "gcp.project_id"`, and the only trace of the failure is a background log line. This holds on a laptop and on Cloud Run alike. Setting `OTEL_RESOURCE_ATTRIBUTES=gcp.project_id=YOUR_PROJECT_ID` is enough to fix it, since `maybe_set_otel_providers` reads that variable even when you pass no resource.

The second part is about logs, which on 1.26.0 use a different exporter and do arrive. Without `GoogleCloudResourceDetector`, the resource has no labels at all. The log exporter then files every entry under `generic_node` with location `global` and blank labels.

**Example.** With Version A, a log entry in Logs Explorer shows the Cloud Run service name, region, and instance ID, and you can filter to one service while debugging. With Version B, the same entry shows up under a generic node with location `global`, and the only way to find it is by the log name `adk-otel`. Two agents deployed to the same project produce entries with identical resource blocks.

**Verified.** This was tested on September 21, 2026 with ADK 1.26.0 on Cloud Run. Two services were deployed in `us-central1`, each with a Version B revision and a Version A revision, and each revision emitted one log record. The resource block on each entry, read back from Cloud Logging:

| Label | Version A (`generic_task`) | Version B (`generic_node`) | Fed by |
|---|---|---|---|
| `job` | `adk-otel-test-one` | Key not in this type's schema | `faas.name` |
| `task_id` | Cloud Run instance ID | Key not in this type's schema | `faas.instance` |
| `node_id` | Key not in this type's schema | `""` | `host.id` or `host.name`, which nothing set |
| `namespace` | `""` | `""` | `service.namespace`, which nothing set |
| `location` | `us-central1` | `global` | `cloud.region`, with `global` as the fallback |
| `project_id` | `jwd-gcp-demos` | `jwd-gcp-demos` | The exporter's project ID |

"Key not in this type's schema" means the label can't appear on that entry at all, because the resource type doesn't define it. An empty string means the type defines the key but no OTel attribute supplied a value.

Version A became a `generic_task` because the resource detector supplied both `faas.name` and `faas.instance`. Version B's resource was empty, so it fell through to `generic_node`. The two Version B entries, from two different services, had byte-for-byte identical resource blocks. A filter on `resource.labels.job="adk-otel-test-one"` returned only the Version A entry from that service.

One limit to note: the Cloud Run revision name is not on the log entry in either version. The resource detector puts it on the OTel resource as `faas.version`, but neither generic type has a label for it, and this exporter version has no mapping to `cloud_run_revision`, the type Cloud Run's own system logs use. To filter by revision you would need to add it yourself, for example through `OTEL_RESOURCE_ATTRIBUTES` or a log attribute.

### Difference 3: metrics on or off

Version B turns on `enable_cloud_metrics`. Version A leaves it off.

**Why it matters.** Turning metrics on installs a `MeterProvider` that pushes to Cloud Monitoring every 5 seconds. But ADK 1.26 itself never records a metric. The `google.adk` package contains no call to `get_meter`. Metrics only appear if you also install the `google-adk[otel-gcp]` extra, which adds the `opentelemetry-instrumentation-google-genai` package. That package records token counts and latency for each Gemini call.

The data agent's `requirements.txt` doesn't install that extra. With the current dependencies, enabling metrics would create an idle exporter that has nothing to send. Leaving it off is the correct choice unless you add the extra.

### Difference 4: import style

Version A imports the two functions directly. Version B imports the `google_cloud` module and calls `google_cloud.get_gcp_exporters`. This is a style choice with no runtime effect.

## Which version to use

| Situation | Use | Reason |
|---|---|---|
| Any environment, you want traces | Version A | Only `get_gcp_resource` puts `gcp.project_id` on the resource, and the trace endpoint refuses payloads without it. |
| Running locally with a service account key file | Version A | Scoped credentials keep the trace exporter working. |
| Deployed to Cloud Run, GKE, or Compute Engine | Version A | The resource labels tie logs to the service, region, and instance. |
| You installed `google-adk[otel-gcp]` and want token metrics | Version A, plus `enable_cloud_metrics=True` | Metrics need both the extra and the flag. |
| You only want logs, and only on a laptop | Version B is enough | The 1.26.0 log exporter does not need the resource or the credentials object. |

If you keep Version B for any reason, set `OTEL_RESOURCE_ATTRIBUTES=gcp.project_id=YOUR_PROJECT_ID` in the environment so traces can be accepted.

## Two optional refinements to Version A

Neither of these is a bug fix. Both make the setup more predictable.

**Pass `PROJECT_ID` into the credentials tuple.** Version A takes the project ID for the exporters from `google.auth.default()`, but the project ID for the resource from the `PROJECT_ID` environment variable. If ADC has no default project, the exporters return empty hooks and telemetry is off with only a warning to show for it. Using the environment variable in both places removes that failure:

```python
_gcp_creds, _ = google.auth.default(
    scopes=["https://www.googleapis.com/auth/cloud-platform"],
)
_gcp_exporters = get_gcp_exporters(
    enable_cloud_tracing=True,
    enable_cloud_logging=True,
    google_auth=(_gcp_creds, PROJECT_ID),
)
```

**Set `OTEL_SERVICE_NAME`.** The Google Cloud detector fills in `faas.name` on Cloud Run, but the generic `service.name` label stays empty unless you set this environment variable. Many Cloud console views and third-party tools group by `service.name`. Setting it in the Cloud Run service configuration costs nothing and applies to both versions.

## Where these facts come from

| Claim | Source |
|---|---|
| Credentials go only to the span exporter | `google_cloud.py`, `_get_gcp_span_exporter` takes `credentials`; the log and metric builders take `project_id` only |
| Empty project ID disables telemetry with a warning | `google_cloud.py`, `get_gcp_exporters`, the `if not project_id` branch |
| Metrics export every 5 seconds | `google_cloud.py`, `export_interval_millis=5000` |
| Default log name is `adk-otel` | `google_cloud.py`, `_DEFAULT_LOG_NAME` |
| Default resource uses `OTELResourceDetector` only | `setup.py`, `_get_otel_resource` |
| Providers aren't overridden if already set | `setup.py`, comments above each `set_*_provider` call |
| Cloud Run labels from the detector | `opentelemetry/resourcedetector/gcp_resource_detector/__init__.py`, `_cloud_run_resource` |
| Cloud Run maps to `generic_task` | `opentelemetry/resourcedetector/gcp_resource_detector/_mapping.py`, `get_monitored_resource` fallback branch |
| ADK 1.26 records no metrics itself | No `get_meter` call anywhere under `google/adk` |
| Metrics come from the `otel-gcp` extra | `google_adk-1.26.0.dist-info/METADATA`, `Requires-Dist` for `opentelemetry-instrumentation-google-genai` |
