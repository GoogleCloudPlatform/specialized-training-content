import logging
import os
from typing import Any

from dotenv import load_dotenv

load_dotenv()

# Debug print to confirm module load
logging.info("DEBUG: model_armor_plugin module loaded")

from google.adk.agents import invocation_context
from google.adk.models import llm_response
from google.adk.plugins import base_plugin
from google.adk.tools import base_tool, tool_context
from google.api_core.client_options import ClientOptions
from google.cloud import modelarmor_v1
from google.genai import types

InvocationContext = invocation_context.InvocationContext
CallbackContext = base_plugin.CallbackContext
ToolContext = tool_context.ToolContext
BasePlugin = base_plugin.BasePlugin
BaseTool = base_tool.BaseTool
LlmResponse = llm_response.LlmResponse

# Util function defined here to avoid extra dependency files
def parse_model_armor_response(
    response: (
        modelarmor_v1.SanitizeUserPromptResponse
        | modelarmor_v1.SanitizeModelResponseResponse
    ),
) -> list[tuple[str, Any]]:
    """Parses the Model Armor response."""
    filter_match_state = modelarmor_v1.FilterMatchState.MATCH_FOUND
    if (
        response.sanitization_result.filter_match_state == filter_match_state
        and response.sanitization_result.filter_results
    ):
        return [
            (
                filter_id,
                filter_result,
            )
            for filter_id, filter_result in response.sanitization_result.filter_results.items()
        ]
    return []

_MODEL_RESPONSE_REMOVED_MESSAGE = (
    "FAILED: Unsafe model response detected."
)

class ModelArmorSafetyFilterPlugin(BasePlugin):
    """Guardian plugin to run Model Armor on user prompts and model responses in ADK."""

    def __init__(
        self,
        project_id: str = os.environ.get("GOOGLE_CLOUD_PROJECT", ""),
        location_id: str = os.environ.get("MODEL_ARMOR_LOCATION", ""),
        template_id: str = os.environ.get("MODEL_ARMOR_TEMPLATE", ""),
    ) -> None:
        """Initializes the ModelArmorPlugin."""
        super().__init__(name="ModelArmorPlugin")
        self._project_id = project_id
        self._location_id = location_id
        if not self._location_id:
            self._location_id = "us-central1"
            
        self._template_id = template_id
        # The template_id provided is the full resource name, so use it directly if it starts with projects/
        if self._template_id.startswith("projects/"):
            self._model_armor_url = self._template_id
        else:
            self._model_armor_url = f"projects/{self._project_id}/locations/{self._location_id}/templates/{self._template_id}"
        logging.info(f"ModelArmorPlugin template ID: {self._template_id}")
        self._client = modelarmor_v1.ModelArmorClient(
            client_options=ClientOptions(
                api_endpoint=f"modelarmor.{self._location_id}.rep.googleapis.com"
            ),
        )
        logging.info(f"Initialized ModelArmorPlugin with template: {self._model_armor_url}")

    def _sanitize_model_response(
        self, model_response: str
    ) -> modelarmor_v1.SanitizeModelResponseResponse:
        logging.info(f"Attempting to sanitize model response: {model_response}")
        model_response_data = modelarmor_v1.DataItem(text=model_response)

        request = modelarmor_v1.SanitizeModelResponseRequest(
            name=self._model_armor_url,
            model_response_data=model_response_data,
        )

        return self._client.sanitize_model_response(request=request)

    def _get_model_armor_response(
        self,
        method: str,
        text: str,
    ) -> list[tuple[str, Any]]:
        """Gets the Model Armor response for the given text and method."""
        try:
            if method == "sanitizeModelResponse":
                response = self._sanitize_model_response(text)
            else:
                raise ValueError(f"Unsupported method: {method}")
            parsed_result = parse_model_armor_response(response)
            return parsed_result
        except Exception as e:
            logging.error(f"Error calling Model Armor: {e}")
            # Fail open or closed? For safety, typically fail closed, but for dev maybe log and proceed?
            # Let's return empty list to "fail open" if service is unreachable to avoid breaking everything
            return []

    def _extract_sdp_deidentified_text(
        self, response: modelarmor_v1.SanitizeModelResponseResponse
    ) -> str | None:
        """Extract deidentified text from SDP filter result, if available."""
        filter_results = response.sanitization_result.filter_results
        sdp_result = filter_results.get("sdp")
        if sdp_result and sdp_result.sdp_filter_result.deidentify_result:
            deidentify = sdp_result.sdp_filter_result.deidentify_result
            match_found = modelarmor_v1.FilterMatchState.MATCH_FOUND
            if (
                deidentify.match_state == match_found
                and deidentify.execution_state == modelarmor_v1.FilterExecutionState.EXECUTION_SUCCESS
                and deidentify.data.text
            ):
                return deidentify.data.text
        return None

    async def after_model_callback(
        self, *, callback_context: CallbackContext, llm_response: LlmResponse,
    ) -> LlmResponse | None:
        llm_content = llm_response.content
        if not llm_content or not llm_content.parts:
            return None
        model_output = "\n".join(
            [part.text or "" for part in llm_content.parts]
        ).strip()
        if not model_output:
            return None

        try:
            ma_response = self._sanitize_model_response(model_output)
        except Exception as e:
            logging.error(f"Error calling Model Armor: {e}")
            return None

        filter_match_state = modelarmor_v1.FilterMatchState.MATCH_FOUND
        if ma_response.sanitization_result.filter_match_state != filter_match_state:
            return None

        # Check for non-SDP blocking filters (e.g. csam, malicious URLs, etc.)
        has_blocking_match = False
        for filter_id, filter_result in ma_response.sanitization_result.filter_results.items():
            if filter_id == "sdp":
                continue
            # Check if this non-SDP filter found a match
            if hasattr(filter_result, 'csam_filter_filter_result'):
                if filter_result.csam_filter_filter_result.match_state == filter_match_state:
                    has_blocking_match = True
                    break
            elif hasattr(filter_result, 'rai_filter_result'):
                if filter_result.rai_filter_result.match_state == filter_match_state:
                    has_blocking_match = True
                    break
            elif hasattr(filter_result, 'pi_and_jailbreak_filter_result'):
                if filter_result.pi_and_jailbreak_filter_result.match_state == filter_match_state:
                    has_blocking_match = True
                    break
            elif hasattr(filter_result, 'malicious_uri_filter_result'):
                if filter_result.malicious_uri_filter_result.match_state == filter_match_state:
                    has_blocking_match = True
                    break

        if has_blocking_match:
            return LlmResponse(
                content=types.Content(
                    role="model",
                    parts=[types.Part.from_text(text=_MODEL_RESPONSE_REMOVED_MESSAGE)],
                )
            )

        # If SDP matched, use the deidentified (redacted) text
        redacted_text = self._extract_sdp_deidentified_text(ma_response)
        if redacted_text:
            print(f"DEBUG: Returning redacted text: {redacted_text}")
            return LlmResponse(
                content=types.Content(
                    role="model",
                    parts=[types.Part.from_text(text=redacted_text)],
                )
            )

        return None