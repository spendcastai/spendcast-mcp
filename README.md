# Spendcast MCP Server

A Model Context Protocol (MCP) server that provides access to Spendcast GraphDB through SPARQL queries. This server enables AI assistants like Claude Desktop to interact with your GraphDB knowledge base directly through natural language conversations.

## What is MCP?

The Model Context Protocol (MCP) is an open standard that allows AI assistants to securely connect to external data sources, APIs, and tools. It enables AI models to:

- Query databases and knowledge bases
- Execute code and scripts
- Access real-time information
- Interact with external services

## Features

- **SPARQL Query Execution**: Execute SPARQL queries against GraphDB
- **Secure Authentication**: Basic authentication with username/password
- **Error Handling**: Comprehensive error handling for network and HTTP issues
- **Async Support**: Built with async/await for high performance
- **Easy Integration**: Simple setup for Claude Desktop and other MCP clients

## Prerequisites

- Python 3.10 or higher
- Access to a GraphDB instance
- GraphDB credentials (username/password)

## Installation

### Install from source (recommended for development)

```bash
# Clone the repository
git clone <your-repo-url>
cd spendcast-mcp

# Install dependencies using uv (recommended)
uv sync

# Or install using pip
pip install -e .
```

## Configuration

Set the following environment variables:

```bash
export GRAPHDB_URL="http://your-graphdb-host:7200/repositories/your-repo"
export GRAPHDB_USER="your-username"
export GRAPHDB_PASSWORD="your-password"
```

Or create a `.env` file in your project directory:

```env
GRAPHDB_URL=http://your-graphdb-host:7200/repositories/your-repo
GRAPHDB_USER=your-username
GRAPHDB_PASSWORD=your-password
```

## Usage

### Using with Claude Desktop

1. **Install Claude Desktop** from [Anthropic's website](https://claude.ai/download)

2. **Configure MCP in Claude Desktop**:
   - Open Claude Desktop
   - Go to Settings → Model Context Protocol
   - Click "Add Server"
   - Configure the server:
     - **Name**: `Spendcast GraphDB`
     - **Command**: `spendcast-mcp`
     - **Working Directory**: Leave empty (or specify if needed)
     - **Environment Variables**: Add your GraphDB credentials

3. **Start a conversation** and ask Claude to query your GraphDB:
   ```
   "Can you query the GraphDB to find all entities related to project spending?"
   "What are the top 10 spending categories in our database?"
   "Show me all transactions from last month"
   ```

### Using with Other MCP Clients

This server is compatible with any MCP client. Common alternatives include:

- **Cursor**: AI-powered code editor with MCP support
- **Continue**: AI pair programming tool
- **Custom MCP clients**: Build your own using the MCP specification

## Available Tools

### `execute_sparql`

Executes SPARQL queries against your GraphDB instance.

**Parameters:**
- `query` (string): The SPARQL query to execute

**Example usage:**
```sparql
SELECT ?s ?p ?o WHERE { ?s ?p ?o } LIMIT 10
```

**Working Examples:**
The server includes several working SPARQL examples for:
- Customer transaction analysis
- Account and payment card usage
- Spending patterns by category and merchant
- Payment card usage patterns

See the server documentation for complete working examples.

**Returns:** JSON results from GraphDB or error information

## Development

### Running Tests

```bash
# Run all tests
uv run pytest tests/

# Run with coverage
uv run pytest tests/ --cov=src/spendcast_mcp --cov-report=term-missing

# Run specific test
uv run pytest tests/test_server.py::test_execute_sparql_success -v
```

### Project Structure

```
spendcast-mcp/
├── src/spendcast_mcp/
│   ├── __init__.py
│   └── server.py          # Main MCP server implementation
├── tests/
│   └── test_server.py     # Test suite
├── pyproject.toml         # Project configuration
└── README.md
```

## Troubleshooting

### Common Issues

1. **"GRAPHDB_URL environment variable not set"**
   - Ensure all required environment variables are set
   - Check your `.env` file if using one

2. **Connection refused to GraphDB**
   - Verify GraphDB is running and accessible
   - Check firewall settings and network connectivity
   - Ensure the repository name in the URL is correct

3. **Authentication failed**
   - Verify username and password are correct
   - Check if the user has access to the specified repository

4. **MCP client can't connect**
   - Ensure the server is running (`spendcast-mcp`)
   - Check that the command path in your MCP client configuration is correct
   - Verify no firewall is blocking the connection

### Debug Mode

Enable debug logging by setting the log level:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the terms specified in the LICENSE file.

## Support

For issues and questions:
- Check the troubleshooting section above
- Review the test suite for usage examples
- Open an issue on the project repository

## Related Links

- [Model Context Protocol (MCP) Specification](https://modelcontextprotocol.io/)
- [Claude Desktop](https://claude.ai/download)
- [GraphDB Documentation](https://graphdb.ontotext.com/)
- [SPARQL Query Language](https://www.w3.org/TR/sparql11-query/)