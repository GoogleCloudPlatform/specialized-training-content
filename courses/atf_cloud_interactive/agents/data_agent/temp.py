def _make_bigquery_mcp_toolset() -> McpToolset:
    """Create the BigQuery MCP toolset with dynamic bearer auth via header_provider."""

    credentials, project = google.auth.default(scopes=[BIGQUERY_SCOPE])

    def _header_provider(context):
        """Called on every tool invocation — refreshes token if needed."""
        credentials.refresh(google.auth.transport.requests.Request())
        return {
            "Authorization": f"Bearer {credentials.token}",
            "x-goog-user-project": project,
        }

    return McpToolset(
        connection_params=StreamableHTTPConnectionParams(
            url=BIGQUERY_MCP_ENDPOINT,
        ),
        header_provider=_header_provider,
        # NO auth_credential, NO auth_scheme
    )


def _make_bigquery_mcp_toolset() -> McpToolset:
    credentials, project = google.auth.default(scopes=[BIGQUERY_SCOPE])
    credentials.refresh(google.auth.transport.requests.Request())

    return McpToolset(
        connection_params=StreamableHTTPConnectionParams(
            url=BIGQUERY_MCP_ENDPOINT,
            headers={
                "Authorization": f"Bearer {credentials.token}",
                "x-goog-user-project": project,
            },
        ),
        # NO auth_credential, NO auth_scheme
    )


auth_credential = AuthCredential(
    auth_type=AuthCredentialTypes.SERVICE_ACCOUNT,
    service_account=ServiceAccount(
        use_default_credential=True,
        scopes=["https://www.googleapis.com/auth/cloud-platform"],
    ),
)

def _make_bigquery_mcp_toolset() -> McpToolset:
    return McpToolset(
        connection_params=StreamableHTTPConnectionParams(
            url=BIGQUERY_MCP_ENDPOINT,
        ),
        auth_credential=AuthCredential(
            auth_type=AuthCredentialTypes.SERVICE_ACCOUNT,
            service_account=ServiceAccount(
                use_default_credential=True,
                scopes=[BIGQUERY_SCOPE],
            ),
        ),
        auth_scheme=HTTPBase(scheme="bearer"),
        header_provider=lambda ctx: {"x-goog-user-project": PROJECT_ID},
    )
