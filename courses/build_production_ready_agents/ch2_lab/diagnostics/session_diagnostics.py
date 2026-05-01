"""
Session service cold-start diagnostics.

Times each phase of bringing up the Vertex AI Sessions service so you can see
where the first-request latency actually lives:

  1. import VertexAiSessionService     (cached at server startup; ~0ms)
  2. construct VertexAiSessionService
  3. google.auth.default()              (ADC discovery)
  4. creds.refresh()                    (token fetch)
  5. first list_sessions RPC            (httpx pool init: TLS + HTTP/2 + first call)
  5b. second list_sessions RPC          (same instance; isolates connection-init cost)
  6. first create_session               (may also wake agent engine resource)
  7. second create_session              (warm baseline)

Diagnostic: compare 5 vs 5b on the SAME VertexAiSessionService instance.
  - If 5b drops to baseline (~1s), the cold cost was httpx connection-pool init
    (TLS handshake + HTTP/2 negotiation against the regional endpoint). Fix by
    warming the same instance at server startup before serving traffic.
  - If 5b is still ~5's latency, the cost is per-RPC (server-side) and an
    in-process warm-up won't help.

To remove: delete this file and revert the diagnostics block in
sessions_server.py to its original single-line app construction.
"""

import logging
import time

logger = logging.getLogger(__name__)


def _ms(start: float) -> float:
    return (time.perf_counter() - start) * 1000


async def run(project: str, location: str, app_name: str, user_id: str = "_diag_warmup") -> None:
    logger.info("[diagnostics] starting session service diagnostics")

    t = time.perf_counter()
    from google.adk.sessions import VertexAiSessionService
    logger.info(f"[diagnostics] 1. import VertexAiSessionService: {_ms(t):.1f}ms")

    t = time.perf_counter()
    svc = VertexAiSessionService(project=project, location=location)
    logger.info(f"[diagnostics] 2. construct VertexAiSessionService: {_ms(t):.1f}ms")

    try:
        import google.auth
        from google.auth.transport.requests import Request

        t = time.perf_counter()
        creds, _ = google.auth.default()
        logger.info(f"[diagnostics] 3. google.auth.default(): {_ms(t):.1f}ms")

        t = time.perf_counter()
        creds.refresh(Request())
        logger.info(f"[diagnostics] 4. creds.refresh(): {_ms(t):.1f}ms")
    except Exception as e:
        logger.warning(f"[diagnostics] auth bootstrap failed: {e}")

    try:
        t = time.perf_counter()
        await svc.list_sessions(app_name=app_name, user_id=user_id)
        logger.info(f"[diagnostics] 5. first list_sessions RPC: {_ms(t):.1f}ms")

        t = time.perf_counter()
        await svc.list_sessions(app_name=app_name, user_id=user_id)
        logger.info(f"[diagnostics] 5b. second list_sessions RPC (same instance): {_ms(t):.1f}ms")
    except Exception as e:
        logger.warning(f"[diagnostics] list_sessions failed: {e}")

    try:
        t = time.perf_counter()
        await svc.create_session(app_name=app_name, user_id=user_id, state={})
        logger.info(f"[diagnostics] 6. first create_session: {_ms(t):.1f}ms")

        t = time.perf_counter()
        await svc.create_session(app_name=app_name, user_id=user_id, state={})
        logger.info(f"[diagnostics] 7. second create_session (warm): {_ms(t):.1f}ms")
    except Exception as e:
        logger.warning(f"[diagnostics] create_session failed: {e}")
        logger.info("[diagnostics] complete (aborted before second-client check)")
        return

    logger.info("[diagnostics] complete")
