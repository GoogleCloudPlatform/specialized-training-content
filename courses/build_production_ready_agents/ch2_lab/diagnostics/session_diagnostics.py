"""
Session service cold-start diagnostics.

Times each phase of bringing up the Vertex AI Sessions service so you can see
where the first-request latency actually lives:

  1. import VertexAiSessionService     (cached at server startup; ~0ms)
  2. construct VertexAiSessionService
  3. google.auth.default()              (ADC discovery)
  4. creds.refresh()                    (token fetch)
  5. first list_sessions RPC            (gRPC channel + TLS + first call)
  6. first create_session               (may also wake agent engine resource)
  7. second create_session              (warm baseline)
  8. second client, first create_session (process-warm; isolates server-side cold start)

If step 8 is still slow, the cost is server-side (agent engine cold start).
If step 8 is fast, earlier slowness was process-local (channel/auth/imports).

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
    except Exception as e:
        logger.warning(f"[diagnostics] first list_sessions failed: {e}")

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

    try:
        svc2 = VertexAiSessionService(project=project, location=location)
        t = time.perf_counter()
        await svc2.create_session(app_name=app_name, user_id=user_id, state={})
        logger.info(
            f"[diagnostics] 8. second-client first create_session: {_ms(t):.1f}ms "
            "(slow => server-side cold start; fast => process-local cold start)"
        )
    except Exception as e:
        logger.warning(f"[diagnostics] second-client create_session failed: {e}")

    logger.info("[diagnostics] complete")
