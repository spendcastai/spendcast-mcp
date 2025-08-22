import os
import base64
from unittest.mock import MagicMock

import json
import httpx
import pytest
import pytest_asyncio
import respx
from fastmcp import Client, Context

from spendcast_mcp.server import mcp, execute_sparql, execute_sparql_validated, get_config, validate_sparql_query, get_schema_summary, get_example_queries, get_ontology_content, get_schema_help

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


def test_query_validation():
    """Test the SPARQL query validation functionality."""
    # Valid queries
    valid_queries = [
        "SELECT ?s ?p ?o WHERE { ?s ?p ?o } LIMIT 10 exs: ex:",
        "ASK WHERE { ?s a exs:FinancialTransaction } exs: ex:"
    ]
    
    # Invalid queries
    invalid_queries = [
        # Missing prefixes
        "SELECT ?s WHERE { ?s ?p ?o }",
        # Invalid syntax
        "INVALID QUERY",
        # Unbalanced braces
        "SELECT ?s WHERE { ?s ?p ?o",
        # Missing WHERE clause
        "SELECT ?s ?p ?o LIMIT 10"
    ]
    
    # Test valid queries
    for i, query in enumerate(valid_queries, 1):
        is_valid, message = validate_sparql_query(query)
        assert is_valid, f"Query {i} should be valid: {message}"
    
    # Test invalid queries
    for i, query in enumerate(invalid_queries, 1):
        is_valid, message = validate_sparql_query(query.strip())
        assert not is_valid, f"Query {i} should be invalid: {message}"


def test_resource_generation():
    """Test the resource generation functions."""
    # Test schema summary - access the original function through the resource
    schema_summary = get_schema_summary.fn()
    assert "Core Entity Classes" in schema_summary
    assert "Financial Entities" in schema_summary
    assert "Retail Entities" in schema_summary
    
    # Test example queries - access the original function through the resource
    example_queries = get_example_queries.fn()
    assert "Customer Analysis" in example_queries
    assert "Spending Analysis" in example_queries
    assert "Payment Card Usage Patterns" in example_queries
    assert "PREFIX exs:" in example_queries
    
    # Test ontology content - access the original function through the resource
    ontology_content = get_ontology_content.fn()
    if "Ontology file not found" in ontology_content:
        # This is expected in development environment
        pass
    else:
        assert "@prefix" in ontology_content


def test_configuration_enhanced():
    """Test the configuration loading with enhanced error handling."""
    # Test environment variable loading
    try:
        config = get_config()
        # If we get here, config loaded successfully
        assert config.url is not None
        assert config.username is not None
        assert config.password is not None
    except ValueError as e:
        # This is expected if .env file is not configured
        assert "environment variable not set" in str(e)


@pytest.mark.asyncio
async def test_mcp_resources():
    """Test that MCP resources are properly registered and accessible."""
    # Test that resources are registered
    resources = await mcp.get_resources()
    assert len(resources) >= 3, f"Expected at least 3 resources, got {len(resources)}"
    
    # Check for specific resources by name
    resource_names = [r.name for r in resources.values()]
    assert "schema_summary" in resource_names
    assert "example_queries" in resource_names
    assert "triple_store_schema" in resource_names
    
    # Test resource details
    schema_resource = next(r for r in resources.values() if r.name == "schema_summary")
    assert schema_resource.description == "Human-readable summary of key triple store entities and relationships"
    assert str(schema_resource.uri) == "internal://schema_summary.md"
    assert schema_resource.mime_type == "text/markdown"
    
    example_resource = next(r for r in resources.values() if r.name == "example_queries")
    assert example_resource.description == "Common SPARQL query patterns and examples for the financial data store"
    assert str(example_resource.uri) == "internal://example_queries.md"
    assert example_resource.mime_type == "text/markdown"
    
    ontology_resource = next(r for r in resources.values() if r.name == "triple_store_schema")
    assert ontology_resource.description == "Complete ontology and schema for the financial data triple store"
    assert str(ontology_resource.uri) == "https://static.rwpz.net/spendcast/schema#"
    assert ontology_resource.mime_type == "text/turtle"


@pytest.mark.asyncio
async def test_resource_reading():
    """Test that resources can be read through the MCP server."""
    # Get resources first
    resources = await mcp.get_resources()
    
    # Test reading schema summary resource
    schema_resource = next(r for r in resources.values() if r.name == "schema_summary")
    content = await schema_resource.read()
    assert isinstance(content, str)
    assert "Core Entity Classes" in content
    assert "Financial Entities" in content
    assert "Retail Entities" in content
    
    # Test reading example queries resource
    example_resource = next(r for r in resources.values() if r.name == "example_queries")
    content = await example_resource.read()
    assert isinstance(content, str)
    assert "Customer Analysis" in content
    assert "Spending Analysis" in content
    assert "PREFIX exs:" in content
    
    # Test reading ontology resource
    ontology_resource = next(r for r in resources.values() if r.name == "triple_store_schema")
    content = await ontology_resource.read()
    assert isinstance(content, str)
    # The ontology content might be "not found" in test environment, which is expected
    if "Ontology file not found" not in content:
        assert "@prefix" in content or "rdf:" in content


@pytest.mark.asyncio
async def test_execute_sparql_validated_success(mock_env, mocked_sparql_endpoint):
    """Test successful SPARQL query execution with validation."""
    mock_response_data = {
        "head": {"vars": ["s", "p", "o"]},
        "results": {
            "bindings": [{"s": {"type": "uri", "value": "http://example.com/s"}}]
        },
    }
    mocked_sparql_endpoint.post(url=TEST_GRAPHDB_URL).mock(
        return_value=httpx.Response(200, json=mock_response_data)
    )

    query = "SELECT ?s ?p ?o WHERE {?s ?p ?o} LIMIT 1 exs: ex:"

    async with Client(mcp) as client:
        result = await client.call_tool("execute_sparql_validated", {"query": query})
        assert result.data == mock_response_data


@pytest.mark.asyncio
async def test_execute_sparql_validated_failure(mock_env, mocked_sparql_endpoint):
    """Test SPARQL query validation failure."""
    invalid_query = "INVALID QUERY"

    async with Client(mcp) as client:
        result = await client.call_tool("execute_sparql_validated", {"query": invalid_query})
        assert "error" in result.data
        assert "SPARQL validation failed" in result.data["error"]
        assert "validation_tips" in result.data


def test_get_schema_help():
    """Test that get_schema_help returns the expected structure and content."""
    result = get_schema_help.fn()
    
    # Check that it returns a dictionary
    assert isinstance(result, dict)
    
    # Check required keys
    required_keys = ["schema_summary", "example_queries", "ontology", "description", "quick_tips"]
    for key in required_keys:
        assert key in result, f"Missing required key: {key}"
    
    # Check resource URIs
    assert result["schema_summary"] == "internal://schema_summary.md"
    assert result["example_queries"] == "internal://example_queries.md"
    assert result["ontology"] == "https://static.rwpz.net/spendcast/schema#"
    
    # Check description
    assert "data structure" in result["description"]
    assert "SPARQL queries" in result["description"]
    
    # Check quick_tips is a list with expected content
    assert isinstance(result["quick_tips"], list)
    assert len(result["quick_tips"]) >= 5
    
    # Check specific tips
    tips_text = " ".join(result["quick_tips"])
    assert "schema_summary.md" in tips_text
    assert "example_queries.md" in tips_text
    assert "exs:" in tips_text
    assert "ex:" in tips_text
    assert "accounts" in tips_text


@pytest.mark.asyncio
async def test_get_schema_help_tool_integration():
    """Test that get_schema_help tool is properly registered and accessible via MCP."""
    # Test that the tool is registered
    tools = await mcp.get_tools()
    tool_names = [tool.name for tool in tools.values()]
    assert "get_schema_help" in tool_names
    
    # Test tool execution through MCP client
    async with Client(mcp) as client:
        result = await client.call_tool("get_schema_help", {})
        
        # Check the result structure
        assert "schema_summary" in result.data
        assert "example_queries" in result.data
        assert "ontology" in result.data
        assert "description" in result.data
        assert "quick_tips" in result.data
        
        # Verify the tool provides actionable guidance
        assert "Use these resources" in result.data["description"]
        assert len(result.data["quick_tips"]) > 0


def test_get_schema_help_content_quality():
    """Test that get_schema_help provides high-quality, actionable content."""
    result = get_schema_help.fn()
    
    # Check that quick_tips are actually helpful
    tips = result["quick_tips"]
    
    # Should mention key resources
    resource_tips = [tip for tip in tips if any(resource in tip for resource in ["schema_summary", "example_queries"])]
    assert len(resource_tips) >= 2, "Should mention both schema and example resources"
    
    # Should mention key prefixes
    prefix_tips = [tip for tip in tips if "exs:" in tip or "ex:" in tip]
    assert len(prefix_tips) >= 2, "Should mention both exs: and ex: prefixes"
    
    # Should mention key relationships
    relationship_tips = [tip for tip in tips if "accounts" in tip or "transactions" in tip]
    assert len(relationship_tips) >= 1, "Should mention key entity relationships"
    
    # Check that description is helpful
    description = result["description"]
    assert len(description) > 50, "Description should be substantial"
    assert "before writing" in description, "Should guide users on when to use the tool"