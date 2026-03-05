# Model Armor Email Redaction — Implementation Options

## Problem

The Data Agent returns BigQuery results that may contain full email addresses.
These flow through the Improve Engagement Agent to the user unredacted. We want
to use [Model Armor](https://cloud.google.com/security/products/model-armor) to
ensure email addresses are never exposed in agent responses.

---

## Option A: Model Armor via Vertex AI `generateContent` Integration

Model Armor can be attached directly to Gemini API calls in Vertex AI using
template references. This is the simplest integration path — no custom code to
call the sanitize API yourself.

### How it works

1. **Create a Sensitive Data Protection inspect template** that targets
   `EMAIL_ADDRESS` (and optionally other infoTypes like `PHONE_NUMBER`).
2. **Create a Sensitive Data Protection de-identify template** that replaces
   detected emails with `[REDACTED]`.
3. **Create a Model Armor template** that references both SDP templates under
   its Advanced sensitive data settings, with enforcement mode
   `INSPECT_AND_BLOCK` (or a de-identify action).
4. **Attach the template** to Gemini calls via the `model_armor_config`
   parameter on `generateContent`:

```python
"model_armor_config": {
    "prompt_template_name": "projects/PROJECT_ID/locations/LOCATION/templates/PROMPT_TEMPLATE",
    "response_template_name": "projects/PROJECT_ID/locations/LOCATION/templates/RESPONSE_TEMPLATE"
}
```

### Where to integrate

The most natural place is the **Improve Engagement Agent's Gemini model
configuration** — the `Gemini3` subclass in `agent.py`. If ADK's `Gemini`
class supports passing `model_armor_config` through to `generateContent`, you
can set the response template there so that every response from the root agent
is automatically sanitized before reaching the user.

If ADK doesn't expose `model_armor_config` directly, you may need to extend the
`Gemini3` class to inject it into the underlying `generate_content` call.

### Pros

- **Minimal code** — configuration-driven, no explicit API calls
- **Applies to all responses** from the root agent automatically
- **Google-managed** — leverages the same SDP engine used across GCP

### Cons

- Depends on ADK exposing the `model_armor_config` parameter (may require a
  custom `Gemini` subclass override)
- The Vertex AI integration docs note that "Sensitive Data Protection redaction
  for de-identify template is not supported" in some contexts — would need to
  verify this works for response-side de-identification
- Redaction happens at the Gemini API boundary, so intermediate agent-to-agent
  messages (Data Agent → Improve Engagement Agent) still contain raw emails

---

## Option B: Model Armor `sanitizeModelResponse` as an ADK Callback

Call the Model Armor sanitize API explicitly via an ADK
[callback or plugin](https://google.github.io/adk-docs/safety/), intercepting
the Data Agent's responses before the Improve Engagement Agent processes them.

### How it works

1. **Create Model Armor template** (same SDP inspect + de-identify templates
   as Option A).
2. **Install the client library**: `pip install google-cloud-modelarmor`
3. **Write a callback/plugin** that calls `sanitizeModelResponse` on every
   response from `data_agent`:

```python
from google.cloud import modelarmor_v1
from google.api_core.gapic_v1 import client_options as grpc_client_options

LOCATION = "us-central1"
TEMPLATE_ID = "email-redaction-template"

_ma_client = modelarmor_v1.ModelArmorClient(
    transport="rest",
    client_options=grpc_client_options.ClientOptions(
        api_endpoint=f"modelarmor.{LOCATION}.rep.googleapis.com"
    ),
)

def sanitize_data_response(response_text: str) -> str:
    """Run Model Armor redaction on Data Agent output."""
    request = modelarmor_v1.SanitizeModelResponseRequest(
        name=f"projects/{PROJECT_ID}/locations/{LOCATION}/templates/{TEMPLATE_ID}",
        model_response_data=modelarmor_v1.DataItem(text=response_text),
    )
    result = _ma_client.sanitize_model_response(request=request)
    # Return the sanitized (de-identified) text
    return result.sanitization_result.sanitized_model_response_data.text
```

4. **Wire it into ADK** as a callback on the `data_agent` tool or as a
   before-model plugin on the root agent. ADK's safety documentation describes
   plugins that "query the Model Armor API to check for potential content safety
   violations at specified points of agent execution."

### Where to integrate

Two sub-options:

- **On the Data Agent's output** — intercept results right after they come back
  from the A2A call, before the Improve Engagement Agent's LLM sees them. This
  is the most secure placement because emails never enter the orchestrating
  agent's context.
- **On the root agent's final response** — sanitize only the user-facing
  output. Simpler to wire up but the LLM still sees raw emails internally.

### Pros

- **Full control** over exactly what gets sanitized and when
- **Works at the data boundary** — can redact emails before they ever reach the
  orchestrating LLM's context window
- **No dependency** on ADK's Gemini class supporting `model_armor_config`
- Aligns with ADK's documented plugin/callback architecture for security

### Cons

- More code to write and maintain
- Adds latency (an extra API call per Data Agent response)
- Need to handle the `google-cloud-modelarmor` dependency and its
  authentication (service account needs `modelarmor.templates.use` permission)

---

## Recommendation

**Start with Option B** (explicit `sanitizeModelResponse` callback). It gives
you precise control over where redaction happens, works regardless of ADK's
Gemini integration surface, and — critically — lets you redact at the data
boundary so emails never enter the orchestrating agent's context at all.

Option A is cleaner long-term but depends on ADK fully supporting
`model_armor_config` pass-through and on SDP de-identification being supported
for response templates in the Vertex AI integration path, both of which carry
some uncertainty today.

---

## Setup Steps (Common to Both Options)

```bash
# 1. Enable APIs
gcloud services enable modelarmor.googleapis.com
gcloud services enable dlp.googleapis.com

# 2. Create SDP inspect template targeting EMAIL_ADDRESS
#    Console: Security > Sensitive Data Protection > Inspect > Create Template
#    Select infoType: EMAIL_ADDRESS

# 3. Create SDP de-identify template
#    Console: Security > Sensitive Data Protection > De-identify > Create Template
#    Transformation: Replace with "[REDACTED]"

# 4. Create Model Armor template referencing both SDP templates
#    Console: Security > Model Armor > Create Template
#    Advanced > Sensitive Data Protection > link inspect + de-identify templates

# 5. Grant the agent's service account permission
gcloud projects add-iam-policy-binding PROJECT_ID \
    --member="serviceAccount:cymbal-agent@PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/modelarmor.user"
```

## References

- [Model Armor overview](https://cloud.google.com/security/products/model-armor)
- [Model Armor + Vertex AI integration](https://docs.cloud.google.com/model-armor/model-armor-vertex-integration)
- [ADK Safety — Callbacks and Plugins](https://google.github.io/adk-docs/safety/)
- [Securing AI Applications codelab](https://codelabs.developers.google.com/codelabs/production-ready-ai-with-gc/4-securing-ai-applications/securing-ai-applications)
- [Mete Atamel's Model Armor walkthrough](https://atamel.dev/posts/2025/08-11_secure_llm_model_armor/)
