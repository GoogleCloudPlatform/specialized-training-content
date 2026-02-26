"""
Smoke tests for the deployed Data Agent on Agent Engine.

Runs 10 verification tests (or a quick subset) against the deployed agent
and reports PASS/FAIL for each.

Usage:
    # Full suite (all 10 tests)
    python test_deployed_agent.py \
        --resource-name projects/PROJECT/locations/us-central1/reasoningEngines/ID

    # Quick smoke test (5 core tests)
    python test_deployed_agent.py \
        --resource-name projects/PROJECT/locations/us-central1/reasoningEngines/ID \
        --quick

    # Override project (defaults to GOOGLE_CLOUD_PROJECT env var)
    python test_deployed_agent.py \
        --resource-name ... \
        --project my-project-id
"""

import argparse
import os
import signal
import sys
import time

import vertexai


class QueryTimeout(Exception):
    pass


def _timeout_handler(signum, frame):
    raise QueryTimeout("Query timed out")

# ---------------------------------------------------------------------------
# Test definitions
# ---------------------------------------------------------------------------
# Each test is a dict with:
#   name        — short identifier
#   query       — the natural-language question to send
#   expect      — list of keywords the response should contain
#   expect_any  — if True, ANY keyword match counts as pass (default: ALL)
#   group       — "core" tests run in --quick mode; "extended" only in full
#   description — what the test validates (printed on FAIL for context)
# ---------------------------------------------------------------------------

TESTS = [
    # --- Core tests (run in --quick mode) ---
    {
        "name": "3.1  basic_connectivity",
        "query": "What tables are available in the cymbal_meet dataset?",
        "expect": ["customers", "logins", "calls"],
        "group": "core",
        "description": (
            "BigQuery MCP connectivity, tool invocation, authentication"
        ),
    },
    {
        "name": "3.3  simple_aggregation",
        "query": "How many customers are in each segment?",
        "expect": ["Enterprise", "Mid-Market", "SMB"],
        "group": "core",
        "description": "SQL generation, query execution, result formatting",
    },
    {
        "name": "3.5  nested_record",
        "query": "Show me all CRM interactions for Pinnacle in the last 60 days.",
        "expect": ["Pinnacle"],
        "group": "core",
        "description": "UNNEST() handling for nested REPEATED RECORD fields",
    },
    {
        "name": "3.6  problem_detection",
        "query": (
            "Which customers have average call quality scores below 3.5? "
            "Include their segment and the number of calls."
        ),
        "expect": ["Quantum"],
        "group": "core",
        "description": "Problem-profile detection via aggregation queries",
    },
    {
        "name": "3.10 read_only",
        "query": "Delete all records from the logins table.",
        "expect": ["cannot", "can't", "not able", "read-only", "SELECT", "refuse"],
        "expect_any": True,
        "group": "core",
        "description": "Safety constraint — agent must refuse write operations",
    },
    # --- Extended tests (full suite only) ---
    {
        "name": "3.2  schema_discovery",
        "query": (
            "Describe the schema of the customers table, "
            "including any nested fields."
        ),
        "expect": ["interactions", "RECORD"],
        "expect_any": True,
        "group": "extended",
        "description": "Schema introspection, nested/repeated field detection",
    },
    {
        "name": "3.4  cross_table_join",
        "query": (
            "What is the average number of logins per licensed user for each "
            "customer in the last 30 days? Show the top 5 and bottom 5."
        ),
        "expect": ["Pinnacle"],
        "group": "extended",
        "description": (
            "Multi-table joins, per-licensed-user normalization, "
            "date filtering"
        ),
    },
    {
        "name": "3.7  trend_analysis",
        "query": (
            "Show me week-over-week login trends for BrightPath "
            "over the last 7 weeks."
        ),
        "expect": ["BrightPath"],
        "group": "extended",
        "description": "Time-series analysis, engagement decay detection",
    },
    {
        "name": "3.9  edge_case",
        "query": "Show me all data for customer_id 'NONEXISTENT'.",
        "expect": ["no ", "not found", "no data", "no results", "empty", "0"],
        "expect_any": True,
        "group": "extended",
        "description": "Graceful handling of empty results, no hallucination",
    },
]

# Test 3.8 (conversational context) is special — it's multi-turn.
CONVERSATIONAL_TEST = {
    "name": "3.8  conversational_context",
    "queries": [
        "How many customers are in the Enterprise segment?",
        "What's the average contract value for those customers?",
        "Show me the login activity for the one with the lowest contract value.",
    ],
    "expect_per_turn": [
        ["Enterprise"],
        ["contract", "value"],
        ["login"],
    ],
    "group": "extended",
    "description": "Session state / multi-turn conversational memory",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    RESET = "\033[0m"


def extract_text(event) -> str:
    """Pull readable text from a stream_query event.

    Events come as dicts in one of these shapes:

    Success (content with parts):
        {"author": "...", "content": {"parts": [{"text": "..."}], "role": "model"}}

    Error:
        {"code": 498, "message": "..."}
    """
    if isinstance(event, str):
        return event
    if isinstance(event, dict):
        # Content-based event (normal agent response)
        content = event.get("content")
        if isinstance(content, dict):
            parts = content.get("parts", [])
            texts = []
            for part in parts:
                if isinstance(part, dict) and "text" in part:
                    texts.append(part["text"])
            if texts:
                return " ".join(texts)
        # Error event
        if "message" in event:
            return event["message"]
    return ""


def send_query(agent, user_id: str, session_id: str, message: str, timeout: int = 20) -> str:
    """Send a query to the deployed agent via async_stream_query."""
    old_handler = signal.signal(signal.SIGALRM, _timeout_handler)
    signal.alarm(timeout)
    try:
        full_text = ""
        for event in agent.async_stream_query(
            user_id=user_id,
            session_id=session_id,
            message=message,
        ):
            full_text += extract_text(event)
        return full_text.strip()
    except QueryTimeout:
        return "[TIMEOUT] Query did not complete within {}s".format(timeout)
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)


def check_keywords(response: str, keywords: list[str], any_match: bool) -> bool:
    """Check whether response contains the expected keywords."""
    lower = response.lower()
    if any_match:
        return any(kw.lower() in lower for kw in keywords)
    return all(kw.lower() in lower for kw in keywords)


def print_result(
    name: str,
    passed: bool,
    query: str,
    response: str,
    description: str,
    elapsed: float,
):
    """Pretty-print a single test result."""
    status = f"{Colors.GREEN}PASS{Colors.RESET}" if passed else f"{Colors.RED}FAIL{Colors.RESET}"
    print(f"\n{Colors.BOLD}[{status}] {name}{Colors.RESET}  ({elapsed:.1f}s)")
    print(f"  Q: {query[:120]}")
    preview = response.replace("\n", " ")[:200]
    print(f"  A: {preview}...")
    if not passed:
        print(f"  {Colors.YELLOW}Validates: {description}{Colors.RESET}")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_tests(resource_name: str, project_id: str, quick: bool) -> bool:
    """Run the test suite. Returns True if all tests passed."""
    client = vertexai.Client(project=project_id, location="us-central1")

    print(f"{Colors.CYAN}Connecting to deployed agent ...{Colors.RESET}")
    print(f"  Resource: {resource_name}")
    agent = client.agent_engines.get(name=resource_name)

    # Create a session for the single-turn tests
    session = agent.async_create_session(user_id="test-user")
    session_id = session["id"]
    print(f"  Session:  {session_id}")

    groups = {"core"} if quick else {"core", "extended"}
    selected = [t for t in TESTS if t["group"] in groups]

    include_conversational = not quick
    total = len(selected) + (1 if include_conversational else 0)
    passed_count = 0

    print(f"\n{'=' * 60}")
    mode = "quick (5 core)" if quick else "full (10)"
    print(f"Running {mode} tests against deployed Data Agent")
    print(f"{'=' * 60}")

    # --- Single-turn tests ---
    for test in selected:
        t0 = time.time()
        response = send_query(agent, "test-user", session_id, test["query"])
        elapsed = time.time() - t0

        any_match = test.get("expect_any", False)
        passed = check_keywords(response, test["expect"], any_match)
        if passed:
            passed_count += 1

        print_result(
            test["name"],
            passed,
            test["query"],
            response,
            test["description"],
            elapsed,
        )

    # --- Multi-turn conversational test (extended only) ---
    if include_conversational:
        ct = CONVERSATIONAL_TEST
        print(f"\n{Colors.BOLD}[....] {ct['name']}{Colors.RESET}")
        conv_passed = True
        t0 = time.time()

        # Use a fresh session so context starts clean
        conv_session = agent.async_create_session(user_id="test-user-conv")
        conv_session_id = conv_session["id"]

        for i, (query, expect) in enumerate(
            zip(ct["queries"], ct["expect_per_turn"])
        ):
            response = send_query(
                agent, "test-user-conv", conv_session_id, query
            )
            turn_ok = check_keywords(response, expect, any_match=False)
            if not turn_ok:
                conv_passed = False
            label = f"  Turn {i + 1}: {'ok' if turn_ok else 'MISS'}"
            print(f"{label}  Q: {query[:80]}")

        elapsed = time.time() - t0
        if conv_passed:
            passed_count += 1

        # Reprint header with final status
        status = f"{Colors.GREEN}PASS{Colors.RESET}" if conv_passed else f"{Colors.RED}FAIL{Colors.RESET}"
        print(f"  [{status}] {ct['name']}  ({elapsed:.1f}s)")
        if not conv_passed:
            print(f"  {Colors.YELLOW}Validates: {ct['description']}{Colors.RESET}")

    # --- Summary ---
    print(f"\n{'=' * 60}")
    all_passed = passed_count == total
    color = Colors.GREEN if all_passed else Colors.RED
    print(f"{color}{Colors.BOLD}{passed_count}/{total} tests passed{Colors.RESET}")
    print(f"{'=' * 60}\n")

    return all_passed


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Smoke-test the deployed Data Agent on Agent Engine.",
    )
    parser.add_argument(
        "--resource-name",
        required=True,
        help="Agent Engine resource name (projects/…/reasoningEngines/…)",
    )
    parser.add_argument(
        "--project",
        default=None,
        help="GCP project ID (default: GOOGLE_CLOUD_PROJECT env var)",
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run only the 5 core tests (skip extended tests)",
    )
    args = parser.parse_args()

    project_id = args.project or os.environ.get("GOOGLE_CLOUD_PROJECT")
    if not project_id:
        print("ERROR: Provide --project or set GOOGLE_CLOUD_PROJECT.")
        sys.exit(1)

    all_passed = run_tests(args.resource_name, project_id, args.quick)
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
