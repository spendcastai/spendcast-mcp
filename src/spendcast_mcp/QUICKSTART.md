# Quick Start Guide - MCP Server

Get your MCP server running in 5 minutes! 🚀

## 1. Setup Environment

```bash
# Navigate to the MCP directory
cd src/mcp

# Copy environment configuration
cp env.example .env

# Edit .env with your GraphDB details
nano .env
```

## 2. Install Dependencies

```bash
# Install required packages
pip install -r requirements.txt
```

## 3. Configure GraphDB

Edit your `.env` file:

```bash
# GraphDB SPARQL endpoint
GRAPHDB_URL=http://localhost:7200/repositories/jeanine/sparql

# Authentication
GRAPHDB_USER=user
GRAPHDB_PASSWORD=password
```

## 4. Test the Setup

```bash
# Run tests to verify everything works
python test_server.py
```

## 5. Start the Server

```bash
# Start the MCP server
python server.py
```

## 6. Verify Resources

The server provides these resources:

- **`triple_store_schema`** - Complete ontology
- **`schema_summary`** - Human-readable schema
- **`example_queries`** - Working SPARQL examples

## 7. Test with a Simple Query

Use the `execute_sparql` tool with:

```sparql
PREFIX exs: <https://static.rwpz.net/spendcast/schema#>
PREFIX ex: <https://static.rwpz.net/spendcast/>

SELECT ?transaction ?amount WHERE {
  ?transaction a exs:FinancialTransaction ;
    exs:hasMonetaryAmount ?amount_uri .
  ?amount_uri exs:hasAmount ?amount .
}
LIMIT 5
```

## Troubleshooting

### Common Issues

- **Connection refused**: Check GraphDB is running and URL is correct
- **Authentication failed**: Verify username/password in .env
- **File not found**: Ensure ontology.ttl exists in deploy/ directory

### Need Help?

1. Check the comprehensive README.md
2. Run `python test_server.py` for diagnostics
3. Verify GraphDB repository exists and is accessible
4. Check GraphDB logs for detailed error information

## Next Steps

- Explore the example queries in the `example_queries` resource
- Review the schema summary for available entities and properties
- Build complex queries using the provided patterns
- Integrate with your LLM application using the MCP protocol

🎉 You're ready to query your financial data triple store!
