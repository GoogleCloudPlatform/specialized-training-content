"""Unit tests for Google OAuth token validation in sessions_server_auth."""

import importlib
import sys
import types
import unittest
from unittest import mock


def _load_sessions_server_auth():
    """Import sessions_server_auth with lightweight stubs if optional deps are absent."""
    stub_modules = {}

    if "dotenv" not in sys.modules:
        dotenv_mod = types.ModuleType("dotenv")
        dotenv_mod.load_dotenv = lambda *args, **kwargs: None
        stub_modules["dotenv"] = dotenv_mod

    if "starlette" not in sys.modules:
        starlette_mod = types.ModuleType("starlette")
        starlette_mod.responses = mock.MagicMock()
        stub_modules["starlette"] = starlette_mod

    if "fastapi" not in sys.modules:
        fastapi_mod = types.ModuleType("fastapi")

        class DummyFastAPI:
            def __init__(self, *args, **kwargs):
                pass

            def add_middleware(self, *args, **kwargs):
                pass

            def middleware(self, *args, **kwargs):
                def decorator(fn):
                    return fn
                return decorator

            def get(self, *args, **kwargs):
                def decorator(fn):
                    return fn
                return decorator

            def post(self, *args, **kwargs):
                def decorator(fn):
                    return fn
                return decorator

        class DummyHTTPException(Exception):
            def __init__(self, status_code: int, detail: str = ""):
                super().__init__(detail)
                self.status_code = status_code
                self.detail = detail

        fastapi_mod.FastAPI = DummyFastAPI
        fastapi_mod.HTTPException = DummyHTTPException
        fastapi_mod.Request = object
        fastapi_mod.status = types.SimpleNamespace(HTTP_401_UNAUTHORIZED=401)
        stub_modules["fastapi"] = fastapi_mod

        cors_mod = types.ModuleType("fastapi.middleware.cors")
        cors_mod.CORSMiddleware = object
        stub_modules["fastapi.middleware.cors"] = cors_mod

        resp_mod = types.ModuleType("fastapi.responses")

        class DummyJSONResponse:
            def __init__(self, status_code: int, content: dict):
                self.status_code = status_code
                self.content = content

        resp_mod.HTMLResponse = object
        resp_mod.JSONResponse = DummyJSONResponse
        resp_mod.StreamingResponse = object
        stub_modules["fastapi.responses"] = resp_mod

    if "google.adk" not in sys.modules:
        google_mod = sys.modules.get("google") or types.ModuleType("google")
        google_mod.__path__ = getattr(google_mod, "__path__", [])
        stub_modules["google"] = google_mod

        adk_mod = types.ModuleType("google.adk")
        adk_mod.__path__ = []
        adk_mod.Agent = mock.MagicMock()
        stub_modules["google.adk"] = adk_mod

        adk_tools = types.ModuleType("google.adk.tools")
        adk_tools.google_search = mock.MagicMock()
        stub_modules["google.adk.tools"] = adk_tools

        adk_agents = types.ModuleType("google.adk.agents")
        adk_agents.__path__ = []
        adk_agents.Agent = mock.MagicMock()
        stub_modules["google.adk.agents"] = adk_agents

        run_config_mod = types.ModuleType("google.adk.agents.run_config")
        run_config_mod.RunConfig = mock.MagicMock()
        run_config_mod.StreamingMode = types.SimpleNamespace(SSE="SSE")
        stub_modules["google.adk.agents.run_config"] = run_config_mod

        examples_mod = types.ModuleType("google.adk.examples")
        examples_mod.VertexAiExampleStore = mock.MagicMock()
        stub_modules["google.adk.examples"] = examples_mod

        runners_mod = types.ModuleType("google.adk.runners")
        runners_mod.InMemoryRunner = mock.MagicMock()
        runners_mod.Runner = mock.MagicMock()
        stub_modules["google.adk.runners"] = runners_mod

        sessions_mod = types.ModuleType("google.adk.sessions")
        sessions_mod.InMemorySessionService = mock.MagicMock()
        stub_modules["google.adk.sessions"] = sessions_mod

        genai_mod = types.ModuleType("google.genai")
        genai_mod.types = mock.MagicMock()
        stub_modules["google.genai"] = genai_mod

        auth_mod = types.ModuleType("google.auth")
        auth_mod.__path__ = []
        stub_modules["google.auth"] = auth_mod

        auth_transport = types.ModuleType("google.auth.transport")
        auth_transport.requests = mock.MagicMock()
        stub_modules["google.auth.transport"] = auth_transport

        oauth2_mod = types.ModuleType("google.oauth2")
        oauth2_mod.id_token = mock.MagicMock()
        stub_modules["google.oauth2"] = oauth2_mod

    with mock.patch.dict(sys.modules, stub_modules):
        if "sessions_server_auth" in sys.modules:
            return importlib.reload(sys.modules["sessions_server_auth"])
        return importlib.import_module("sessions_server_auth")


class ValidateTokenTests(unittest.IsolatedAsyncioTestCase):
    """Tests for validate_token email_verified enforcement."""

    def setUp(self):
        super().setUp()
        self.server = _load_sessions_server_auth()

    async def test_validate_token_accepts_verified_email(self):
        expected_claims = {
            "sub": "1234567890",
            "email": "user@example.com",
            "email_verified": True,
        }
        with mock.patch.object(
            self.server.id_token,
            "verify_oauth2_token",
            return_value=expected_claims,
        ):
            result = await self.server.validate_token("Bearer valid-token")
        self.assertEqual(result, expected_claims)

    async def test_validate_token_rejects_unverified_email(self):
        unverified_claims = {
            "sub": "1234567890",
            "email": "victim@example.com",
            "email_verified": False,
        }
        with mock.patch.object(
            self.server.id_token,
            "verify_oauth2_token",
            return_value=unverified_claims,
        ):
            result = await self.server.validate_token("Bearer unverified-token")
        self.assertIsNone(result)

    async def test_validate_token_rejects_missing_email_verified_claim(self):
        missing_claim = {
            "sub": "1234567890",
            "email": "victim@example.com",
        }
        with mock.patch.object(
            self.server.id_token,
            "verify_oauth2_token",
            return_value=missing_claim,
        ):
            result = await self.server.validate_token("Bearer missing-claim-token")
        self.assertIsNone(result)

    async def test_authentication_middleware_returns_401_for_unverified_email(self):
        unverified_claims = {
            "sub": "1234567890",
            "email": "victim@example.com",
            "email_verified": False,
        }
        request = types.SimpleNamespace(
            method="POST",
            url=types.SimpleNamespace(path="/chat"),
            headers={"Authorization": "Bearer unverified-token"},
            state=types.SimpleNamespace(),
        )
        call_next = mock.AsyncMock()
        with mock.patch.object(
            self.server.id_token,
            "verify_oauth2_token",
            return_value=unverified_claims,
        ):
            response = await self.server.authentication_middleware(request, call_next)
        self.assertEqual(response.status_code, 401)
        call_next.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
