import os
import base64
from unittest.mock import MagicMock

import json
import httpx
import pytest
import pytest_asyncio
import respx
from fastmcp import Client, Context

from spendcast_mcp.server import mcp, execute_sparql, get_config

# Mock GraphDB URL for testing
TEST_GRAPHDB_URL = "http://test-graphdb:7200/repositories/test"
TEST_USER = "testuser"
TEST_PASSWORD = "testpassword"


@pytest.fixture
def mock_env():
    """Fixture to set environment variables for tests."""
    # Store original values if they exist
    original_values = {}
    for var in ["GRAPHDB_URL", "GRAPHDB_USER", "GRAPHDB_PASSWORD"]:
        if var in os.environ:
            original_values[var] = os.environ[var]
    
    os.environ["GRAPHDB_URL"] = TEST_GRAPHDB_URL
    os.environ["GRAPHDB_USER"] = TEST_USER
    os.environ["GRAPHDB_PASSWORD"] = TEST_PASSWORD
    yield os.environ
    
    # Restore original values or remove test values
    for var in ["GRAPHDB_URL", "GRAPHDB_USER", "GRAPHDB_PASSWORD"]:
        if var in original_values:
            os.environ[var] = original_values[var]
        elif var in os.environ:
            del os.environ[var]


def test_get_config_success(mock_env):
    """Test that get_config successfully loads the URL from the environment."""
    config = get_config()
    assert config.url == TEST_GRAPHDB_URL
    assert config.username == TEST_USER
    assert config.password == TEST_PASSWORD


@pytest.mark.parametrize(
    "missing_var, error_msg",
    [
        ("GRAPHDB_URL", "GRAPHDB_URL environment variable not set."),
        ("GRAPHDB_USER", "GRAPHDB_USER environment variable not set."),
        ("GRAPHDB_PASSWORD", "GRAPHDB_PASSWORD environment variable not set."),
    ],
)
def test_get_config_missing_variable(monkeypatch, mock_env, missing_var, error_msg):
    """Test that get_config raises ValueError if an env var is not set."""
    # mock_env already sets them, so we just need to remove one
    monkeypatch.delenv(missing_var)

    with pytest.raises(ValueError, match=error_msg):
        get_config()


@pytest_asyncio.fixture
async def mocked_sparql_endpoint():
    """Respx fixture to mock the GraphDB SPARQL endpoint."""
    async with respx.mock(base_url=TEST_GRAPHDB_URL) as mock:
        yield mock


@pytest.mark.asyncio
async def test_execute_sparql_success(mock_env, mocked_sparql_endpoint):
    """Test a successful SPARQL query execution."""
    mock_response_data = {
        "head": {"vars": ["s", "p", "o"]},
        "results": {
            "bindings": [{"s": {"type": "uri", "value": "http://example.com/s"}}]
        },
    }
    mocked_sparql_endpoint.post(url=TEST_GRAPHDB_URL).mock(
        return_value=httpx.Response(200, json=mock_response_data)
    )

    # mock_ctx = MagicMock(spec=Context)
    query = "SELECT ?s ?p ?o WHERE {?s ?p ?o} LIMIT 1"

    # result = await execute_sparql(mock_ctx, query)
    async with Client(mcp) as client:
        result = await client.call_tool("execute_sparql", {"query": query})

        assert result.data == mock_response_data
        assert mocked_sparql_endpoint.calls.call_count == 1
        request = mocked_sparql_endpoint.calls.last.request
        assert (
            request.content
            == b"query=SELECT+%3Fs+%3Fp+%3Fo+WHERE+%7B%3Fs+%3Fp+%3Fo%7D+LIMIT+1"
        )
        auth_header = request.headers["authorization"]
        expected_token = base64.b64encode(
            f"{TEST_USER}:{TEST_PASSWORD}".encode()
        ).decode()
        assert auth_header == f"Basic {expected_token}"


@pytest.mark.asyncio
async def test_execute_sparql_http_error(mock_env, mocked_sparql_endpoint):
    """Test handling of an HTTP status error from GraphDB."""
    mocked_sparql_endpoint.post(url=TEST_GRAPHDB_URL).mock(
        return_value=httpx.Response(500, text="Internal Server Error")
    )

    async with Client(mcp) as client:
        result = await client.call_tool("execute_sparql", {"query": "SELECT ?s"})
        assert "error" in result.data
        assert "500" in result.data["error"]


@pytest.mark.asyncio
async def test_execute_sparql_request_error(mock_env, mocked_sparql_endpoint):
    """Test handling of a network request error."""
    mocked_sparql_endpoint.post(url=TEST_GRAPHDB_URL).mock(
        side_effect=httpx.ConnectError("Connection failed")
    )

    async with Client(mcp) as client:
        result = await client.call_tool("execute_sparql", {"query": "SELECT ?s"})
        assert "error" in result.data
        assert "Connection failed" in result.data["error"]



