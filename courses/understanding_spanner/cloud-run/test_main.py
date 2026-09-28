"""Unit tests for authentication on DELETE /pets in courses/understanding_spanner/cloud-run/main.py."""

import importlib
import os
import sys
import types
import unittest
from unittest import mock


def _load_main_module():
    """Import main.py with lightweight stubs for Spanner and Flask if not installed."""
    stub_modules = {}

    google_mod = sys.modules.get("google") or types.ModuleType("google")
    google_mod.__path__ = getattr(google_mod, "__path__", [])
    stub_modules["google"] = google_mod

    cloud_mod = types.ModuleType("google.cloud")
    cloud_mod.__path__ = []
    stub_modules["google.cloud"] = cloud_mod

    spanner_mod = types.ModuleType("google.cloud.spanner")
    spanner_mod.Client = mock.MagicMock()
    spanner_mod.param_types = types.SimpleNamespace(STRING="STRING")
    stub_modules["google.cloud.spanner"] = spanner_mod

    auth_mod = types.ModuleType("google.auth")
    auth_mod.__path__ = []
    stub_modules["google.auth"] = auth_mod

    auth_transport = types.ModuleType("google.auth.transport")
    auth_transport.requests = mock.MagicMock()
    stub_modules["google.auth.transport"] = auth_transport

    oauth2_mod = types.ModuleType("google.oauth2")
    oauth2_mod.id_token = mock.MagicMock()
    stub_modules["google.oauth2"] = oauth2_mod

    if "flask" not in sys.modules:
        flask_mod = types.ModuleType("flask")

        class DummyFlask:
            def __init__(self, *args, **kwargs):
                pass

            def errorhandler(self, *args, **kwargs):
                def decorator(fn):
                    return fn
                return decorator

            def run(self, *args, **kwargs):
                pass

        flask_mod.Flask = DummyFlask
        flask_mod.request = types.SimpleNamespace(headers={}, get_json=lambda *a, **kw: {})
        flask_mod.jsonify = lambda x: x
        stub_modules["flask"] = flask_mod

    if "flask_restful" not in sys.modules:
        restful_mod = types.ModuleType("flask_restful")
        restful_mod.Resource = object
        restful_mod.Api = mock.MagicMock()
        stub_modules["flask_restful"] = restful_mod

    with mock.patch.dict(sys.modules, stub_modules):
        if "main" in sys.modules:
            return importlib.reload(sys.modules["main"])
        return importlib.import_module("main")


class PetsListDeleteAuthTests(unittest.TestCase):
    """Tests ensuring DELETE /pets requires valid authentication."""

    def setUp(self):
        super().setUp()
        self.main = _load_main_module()
        self.resource = self.main.PetsList()
        self.main.database.run_in_transaction.reset_mock()

    def test_delete_rejects_unauthenticated_request(self):
        with mock.patch.object(self.main, "request", types.SimpleNamespace(headers={})):
            body, status_code = self.resource.delete()
        self.assertEqual(status_code, 401)
        self.assertEqual(body, {"error": "Unauthorized"})
        self.main.database.run_in_transaction.assert_not_called()

    def test_delete_rejects_invalid_bearer_token(self):
        headers = {"Authorization": "Bearer invalid-token"}
        with (
            mock.patch.object(self.main, "request", types.SimpleNamespace(headers=headers)),
            mock.patch.object(
                self.main.id_token,
                "verify_oauth2_token",
                side_effect=ValueError("Invalid token"),
            ),
        ):
            body, status_code = self.resource.delete()
        self.assertEqual(status_code, 401)
        self.main.database.run_in_transaction.assert_not_called()

    def test_delete_rejects_unverified_email_token(self):
        headers = {"Authorization": "Bearer unverified-token"}
        with (
            mock.patch.object(self.main, "request", types.SimpleNamespace(headers=headers)),
            mock.patch.object(
                self.main.id_token,
                "verify_oauth2_token",
                return_value={"email": "attacker@example.com", "email_verified": False},
            ),
        ):
            body, status_code = self.resource.delete()
        self.assertEqual(status_code, 401)
        self.main.database.run_in_transaction.assert_not_called()

    def test_delete_allows_verified_oauth_token(self):
        headers = {"Authorization": "Bearer valid-oauth-token"}
        self.main.database.run_in_transaction.return_value = 5
        with (
            mock.patch.object(self.main, "request", types.SimpleNamespace(headers=headers)),
            mock.patch.object(
                self.main.id_token,
                "verify_oauth2_token",
                return_value={"email": "admin@example.com", "email_verified": True},
            ),
        ):
            body, status_code = self.resource.delete()
        self.assertEqual(status_code, 201)
        self.assertEqual(body, "5 record(s) deleted.")
        self.main.database.run_in_transaction.assert_called_once()

    def test_delete_allows_matching_admin_api_token(self):
        headers = {"Authorization": "Bearer secret-admin-token"}
        self.main.database.run_in_transaction.return_value = 3
        with (
            mock.patch.dict(os.environ, {"ADMIN_API_TOKEN": "secret-admin-token"}),
            mock.patch.object(self.main, "request", types.SimpleNamespace(headers=headers)),
        ):
            body, status_code = self.resource.delete()
        self.assertEqual(status_code, 201)
        self.assertEqual(body, "3 record(s) deleted.")
        self.main.database.run_in_transaction.assert_called_once()


if __name__ == "__main__":
    unittest.main()
