"""Unit tests for OAuth client_secret protection in ch3_demos/oauth/server.py (b/585276167)."""

import copy
import importlib
import json
import os
import sys
import types
import unittest
from unittest import mock

TEST_CLIENT_ID = "dummy-client-id.apps.googleusercontent.com"
TEST_CLIENT_SECRET = "GOCSPX-supersecret-poc-value-12345"
TEST_REDIRECT_URI = "http://localhost:8000/auth/callback"
TEST_AUTH_URI = (
    "https://accounts.google.com/o/oauth2/auth"
    "?response_type=code&client_id=dummy-client-id.apps.googleusercontent.com"
)


def _load_oauth_server():
    """Import server.py with lightweight stubs if optional ADK/FastAPI deps are absent."""
    stub_modules = {}

    if "dotenv" not in sys.modules:
        dotenv_mod = types.ModuleType("dotenv")
        dotenv_mod.load_dotenv = lambda *args, **kwargs: None
        stub_modules["dotenv"] = dotenv_mod

    if "fastapi" not in sys.modules:
        fastapi_mod = types.ModuleType("fastapi")

        class DummyFastAPI:
            def __init__(self, *args, **kwargs):
                self.middlewares = []

            def add_middleware(self, cls, **kwargs):
                self.middlewares.append((cls, kwargs))

            def get(self, *args, **kwargs):
                def decorator(fn):
                    return fn
                return decorator

            def post(self, *args, **kwargs):
                def decorator(fn):
                    return fn
                return decorator

        fastapi_mod.FastAPI = DummyFastAPI
        fastapi_mod.Request = object
        stub_modules["fastapi"] = fastapi_mod

        cors_mod = types.ModuleType("fastapi.middleware.cors")
        cors_mod.CORSMiddleware = object
        stub_modules["fastapi.middleware.cors"] = cors_mod

        resp_mod = types.ModuleType("fastapi.responses")

        class DummyJSONResponse:
            def __init__(self, status_code: int, content: dict):
                self.status_code = status_code
                self.content = content

        class DummyStreamingResponse:
            def __init__(self, content, media_type: str = "", headers: dict | None = None):
                self.body_iterator = content
                self.media_type = media_type
                self.headers = headers or {}

        resp_mod.HTMLResponse = object
        resp_mod.JSONResponse = DummyJSONResponse
        resp_mod.StreamingResponse = DummyStreamingResponse
        stub_modules["fastapi.responses"] = resp_mod

        openapi_mod = types.ModuleType("fastapi.openapi")
        openapi_models = types.ModuleType("fastapi.openapi.models")
        openapi_models.OAuth2 = mock.MagicMock()
        openapi_models.OAuthFlowAuthorizationCode = mock.MagicMock()
        openapi_models.OAuthFlows = mock.MagicMock()
        stub_modules["fastapi.openapi"] = openapi_mod
        stub_modules["fastapi.openapi.models"] = openapi_models

    if "google.adk" not in sys.modules:
        google_mod = sys.modules.get("google") or types.ModuleType("google")
        google_mod.__path__ = getattr(google_mod, "__path__", [])
        stub_modules["google"] = google_mod

        adk_mod = types.ModuleType("google.adk")
        adk_mod.__path__ = []
        stub_modules["google.adk"] = adk_mod

        agents_mod = types.ModuleType("google.adk.agents")
        agents_mod.__path__ = []
        llm_agent_mod = types.ModuleType("google.adk.agents.llm_agent")
        llm_agent_mod.LlmAgent = mock.MagicMock()
        stub_modules["google.adk.agents"] = agents_mod
        stub_modules["google.adk.agents.llm_agent"] = llm_agent_mod

        class FakeOAuth2Auth:
            def __init__(
                self,
                client_id=None,
                client_secret=None,
                redirect_uri=None,
                auth_uri=None,
                auth_response_uri=None,
                code_verifier=None,
            ):
                self.client_id = client_id
                self.client_secret = client_secret
                self.redirect_uri = redirect_uri
                self.auth_uri = auth_uri
                self.auth_response_uri = auth_response_uri
                self.code_verifier = code_verifier

            def to_dict(self):
                return {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "redirect_uri": self.redirect_uri,
                    "auth_uri": self.auth_uri,
                    "auth_response_uri": self.auth_response_uri,
                    "code_verifier": self.code_verifier,
                }

        class FakeAuthCredential:
            def __init__(self, auth_type="oauth2", oauth2=None):
                self.auth_type = auth_type
                if isinstance(oauth2, dict):
                    self.oauth2 = FakeOAuth2Auth(**oauth2)
                else:
                    self.oauth2 = oauth2

            def model_copy(self, deep=False):
                return copy.deepcopy(self) if deep else copy.copy(self)

            def to_dict(self):
                return {
                    "auth_type": self.auth_type,
                    "oauth2": self.oauth2.to_dict() if self.oauth2 else None,
                }

        class FakeAuthConfig:
            def __init__(
                self,
                auth_scheme=None,
                raw_auth_credential=None,
                exchanged_auth_credential=None,
                credential_key="bigquery_mcp:oauth2",
            ):
                self.auth_scheme = auth_scheme
                self.raw_auth_credential = (
                    FakeAuthCredential(**raw_auth_credential)
                    if isinstance(raw_auth_credential, dict)
                    else raw_auth_credential
                )
                self.exchanged_auth_credential = (
                    FakeAuthCredential(**exchanged_auth_credential)
                    if isinstance(exchanged_auth_credential, dict)
                    else exchanged_auth_credential
                )
                self.credential_key = credential_key

            @classmethod
            def model_validate(cls, data):
                if isinstance(data, cls):
                    return data
                return cls(**data)

            def model_copy(self, deep=False):
                return copy.deepcopy(self) if deep else copy.copy(self)

            def model_dump(self, mode="python", exclude_none=False):
                return {
                    "credential_key": self.credential_key,
                    "raw_auth_credential": (
                        self.raw_auth_credential.to_dict()
                        if self.raw_auth_credential
                        else None
                    ),
                    "exchanged_auth_credential": (
                        self.exchanged_auth_credential.to_dict()
                        if self.exchanged_auth_credential
                        else None
                    ),
                }

        auth_mod = types.ModuleType("google.adk.auth")
        auth_mod.__path__ = []
        auth_tool_mod = types.ModuleType("google.adk.auth.auth_tool")
        auth_tool_mod.AuthConfig = FakeAuthConfig
        auth_cred_mod = types.ModuleType("google.adk.auth.auth_credential")
        auth_cred_mod.AuthCredential = FakeAuthCredential
        auth_cred_mod.AuthCredentialTypes = types.SimpleNamespace(OAUTH2="oauth2")
        auth_cred_mod.OAuth2Auth = FakeOAuth2Auth
        cred_svc_pkg = types.ModuleType("google.adk.auth.credential_service")
        cred_svc_pkg.__path__ = []
        in_mem_cred_mod = types.ModuleType(
            "google.adk.auth.credential_service.in_memory_credential_service"
        )
        in_mem_cred_mod.InMemoryCredentialService = mock.MagicMock()

        stub_modules["google.adk.auth"] = auth_mod
        stub_modules["google.adk.auth.auth_tool"] = auth_tool_mod
        stub_modules["google.adk.auth.auth_credential"] = auth_cred_mod
        stub_modules["google.adk.auth.credential_service"] = cred_svc_pkg
        stub_modules[
            "google.adk.auth.credential_service.in_memory_credential_service"
        ] = in_mem_cred_mod

        events_mod = types.ModuleType("google.adk.events")
        events_mod.Event = object
        stub_modules["google.adk.events"] = events_mod

        runners_mod = types.ModuleType("google.adk.runners")
        runners_mod.Runner = mock.MagicMock()
        stub_modules["google.adk.runners"] = runners_mod

        sessions_mod = types.ModuleType("google.adk.sessions")
        sessions_mod.InMemorySessionService = mock.MagicMock()
        stub_modules["google.adk.sessions"] = sessions_mod

        tools_mod = types.ModuleType("google.adk.tools")
        tools_mod.__path__ = []
        mcp_tool_mod = types.ModuleType("google.adk.tools.mcp_tool")
        mcp_tool_mod.__path__ = []
        mcp_tool_mod.McpToolset = mock.MagicMock()
        mcp_sess_mod = types.ModuleType(
            "google.adk.tools.mcp_tool.mcp_session_manager"
        )
        mcp_sess_mod.StreamableHTTPConnectionParams = mock.MagicMock()
        stub_modules["google.adk.tools"] = tools_mod
        stub_modules["google.adk.tools.mcp_tool"] = mcp_tool_mod
        stub_modules["google.adk.tools.mcp_tool.mcp_session_manager"] = mcp_sess_mod

        genai_mod = types.ModuleType("google.genai")

        class FakeContent:
            def __init__(self, **kwargs):
                self.kwargs = kwargs

        class FakePart:
            def __init__(self, **kwargs):
                self.kwargs = kwargs

        genai_mod.types = types.SimpleNamespace(Content=FakeContent, Part=FakePart)
        stub_modules["google.genai"] = genai_mod

    oauth_dir = os.path.dirname(os.path.abspath(__file__))
    if oauth_dir not in sys.path:
        sys.path.insert(0, oauth_dir)

    env_patch = {
        "GOOGLE_OAUTH_CLIENT_ID": TEST_CLIENT_ID,
        "GOOGLE_OAUTH_CLIENT_SECRET": TEST_CLIENT_SECRET,
        "OAUTH_REDIRECT_URI": TEST_REDIRECT_URI,
    }
    with mock.patch.dict(os.environ, env_patch), mock.patch.dict(
        sys.modules, stub_modules
    ):
        if "server" in sys.modules:
            return importlib.reload(sys.modules["server"])
        return importlib.import_module("server")


def _make_auth_request_event(server_mod, fc_id: str = "adk-req-cred-1"):
    """Construct a synthetic adk_request_credential event carrying client_secret."""
    raw_cred = server_mod.AuthCredential(
        auth_type="oauth2",
        oauth2=server_mod.OAuth2Auth(
            client_id=TEST_CLIENT_ID,
            client_secret=TEST_CLIENT_SECRET,
            redirect_uri=TEST_REDIRECT_URI,
        ),
    )
    exchanged_cred = server_mod.AuthCredential(
        auth_type="oauth2",
        oauth2=server_mod.OAuth2Auth(
            client_id=TEST_CLIENT_ID,
            client_secret=TEST_CLIENT_SECRET,
            redirect_uri=TEST_REDIRECT_URI,
            auth_uri=TEST_AUTH_URI,
            code_verifier="pkce-secret-verifier",
        ),
    )
    auth_cfg = server_mod.AuthConfig(
        raw_auth_credential=raw_cred,
        exchanged_auth_credential=exchanged_cred,
        credential_key="bigquery_mcp:oauth2",
    )
    fc = types.SimpleNamespace(
        id=fc_id,
        name="adk_request_credential",
        args={"authConfig": auth_cfg},
    )
    part = types.SimpleNamespace(function_call=fc, text=None)
    content = types.SimpleNamespace(parts=[part])
    return types.SimpleNamespace(
        content=content,
        long_running_tool_ids={fc_id},
        partial=False,
        is_final_response=lambda: False,
    )


class OAuthClientSecretLeakTests(unittest.IsolatedAsyncioTestCase):
    """Verify OAuth client_secret is never leaked over SSE and Leg 2 hydration works."""

    def setUp(self):
        super().setUp()
        self.server = _load_oauth_server()
        self.server.pending_auth_configs.clear()
        self.server.session_owners.clear()

    async def test_sse_auth_required_does_not_leak_client_secret(self):
        fake_session = types.SimpleNamespace(id="sess-123", events=[])
        self.server.session_service.create_session = mock.AsyncMock(
            return_value=fake_session
        )

        auth_event = _make_auth_request_event(self.server, fc_id="fc-auth-1")

        async def fake_run_async(**kwargs):
            yield auth_event

        self.server.runner.run_async = fake_run_async

        req = types.SimpleNamespace(
            headers={},
            json=mock.AsyncMock(
                return_value={"user_id": "user_1", "message": "Hello"}
            ),
        )
        response = await self.server.chat(req)
        chunks = [chunk async for chunk in response.body_iterator]
        sse_stream = "".join(chunks)

        # Confidential secrets MUST NOT appear anywhere in the SSE payload
        self.assertNotIn(TEST_CLIENT_SECRET, sse_stream)
        self.assertNotIn("pkce-secret-verifier", sse_stream)
        self.assertNotIn("client_secret", sse_stream)

        # Parse the auth_required SSE event and verify required fields
        data_events = [
            json.loads(line[6:])
            for chunk in chunks
            for line in chunk.splitlines()
            if line.startswith("data: ")
        ]
        auth_events = [e for e in data_events if e.get("type") == "auth_required"]
        self.assertEqual(len(auth_events), 1)
        self.assertEqual(auth_events[0]["function_call_id"], "fc-auth-1")
        self.assertEqual(auth_events[0]["auth_uri"], TEST_AUTH_URI)
        self.assertNotIn("auth_config", auth_events[0])

    async def test_leg2_rehydrates_server_side_auth_config_with_client_secret(self):
        auth_event = _make_auth_request_event(self.server, fc_id="fc-auth-2")
        auth_cfg = self.server.get_auth_config(auth_event)
        self.server.pending_auth_configs[("user_1", "sess-123", "fc-auth-2")] = auth_cfg

        callback_url = "http://localhost:8000/auth/callback?code=4/0AeanS0-test&state=xyz"
        client_message = {
            "role": "user",
            "parts": [
                {
                    "function_response": {
                        "id": "fc-auth-2",
                        "name": "adk_request_credential",
                        "response": {"auth_response_uri": callback_url},
                    }
                }
            ],
        }

        hydrated_msg = self.server.build_hydrated_auth_response_message(
            message=client_message,
            user_id="user_1",
            session_id="sess-123",
        )
        hydrated_resp = hydrated_msg["parts"][0]["function_response"]["response"]
        self.assertEqual(
            hydrated_resp["exchanged_auth_credential"]["oauth2"]["auth_response_uri"],
            callback_url,
        )
        self.assertEqual(
            hydrated_resp["exchanged_auth_credential"]["oauth2"]["client_secret"],
            TEST_CLIENT_SECRET,
        )
        self.assertEqual(
            hydrated_resp["raw_auth_credential"]["oauth2"]["client_secret"],
            TEST_CLIENT_SECRET,
        )

    def test_redact_auth_config_strips_secrets(self):
        auth_event = _make_auth_request_event(self.server, fc_id="fc-auth-3")
        auth_cfg = self.server.get_auth_config(auth_event)
        redacted = self.server.redact_auth_config(auth_cfg)
        dumped = json.dumps(redacted.model_dump(mode="json"))
        self.assertNotIn(TEST_CLIENT_SECRET, dumped)
        self.assertNotIn("pkce-secret-verifier", dumped)

    async def test_cross_user_session_access_rejected(self):
        self.server.session_owners["sess-owned"] = "alice"
        req = types.SimpleNamespace(
            headers={},
            json=mock.AsyncMock(
                return_value={
                    "user_id": "mallory",
                    "session_id": "sess-owned",
                    "message": "Hi",
                }
            ),
        )
        response = await self.server.chat(req)
        self.assertEqual(response.status_code, 403)


if __name__ == "__main__":
    unittest.main()
