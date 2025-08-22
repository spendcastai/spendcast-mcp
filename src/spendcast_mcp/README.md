# MCP Server for Financial Data Triple Store

This MCP (Model Context Protocol) server provides a comprehensive interface to query a financial data triple store containing banking, transaction, and retail data.

## Claude Desktop 
Open the MCP-Configuration file under "Settings" → "Developer" and add the following configuration:

### Example Configuration

```json
    "spendcast-mcp": {
      "command": "/<path-to>/bin/uv",
      "args": [
        "--directory",
        "/<path-to>/spendcast-mcp",
        "run",
        "src/spendcast_mcp/server.py"
      ],
      "env": {
        "GRAPHDB_URL": "https://localhost:7200/repositories/demo",
        "GRAPHDB_USER": "user",
        "GRAPHDB_PASSWORD": "pass"
      },
      "transport": "stdio"
    }
```

## Features

### 🛠️ Tools

#### 1. `execute_sparql`
Execute SPARQL queries against the financial data triple store with comprehensive error handling.

#### 2. `execute_sparql_validated` 
Enhanced version with built-in query validation to catch common SPARQL syntax errors before execution.

### 📚 Resources

#### 1. `triple_store_schema`
Complete ontology and schema definition in Turtle format.

#### 2. `schema_summary`
Human-readable summary of key entities, properties, and relationships.

#### 3. `example_queries`
Comprehensive collection of example SPARQL queries for common use cases.

## Data Model Overview

### Core Financial Entities
- **Accounts**: Checking, savings, credit cards, retirement accounts (3A pillar)
- **Parties**: Customers, banks, merchants, organizations
- **Payment Cards**: Debit/credit cards with limits and status
- **Financial Transactions**: Complete transaction records
- **Monetary Amounts**: Currency amounts with exchange rates

### Retail & Receipt Data
- **Receipts**: Purchase documents with line items
- **Products**: Migros product catalog with sustainability metrics
- **Product Categories**: Hierarchical classification with CO2 factors
- **Merchants**: Business entities with MCC codes

### Key Properties
- Transaction amounts in CHF, EUR, USD
- CO2 footprint calculations
- Tax classifications (standard, reduced, zero, exempt)
- Merchant Category Codes (MCC)
- Complete address and contact information

## Setup

### Environment Variables
Create a `.env` file with your GraphDB configuration:

```bash
GRAPHDB_URL=http://localhost:7200/repositories/your-repo/sparql
GRAPHDB_USER=your_username
GRAPHDB_PASSWORD=your_password
```

### Dependencies
Install required packages:

```bash
pip install fastmcp httpx python-dotenv
```

### Running the Server
```bash
cd src/mcp
python server.py
```

## Usage Examples

### Basic Query Execution
```python
# Simple transaction query
result = await execute_sparql(
    query="""
    PREFIX exs: <https://static.rwpz.net/spendcast/schema#>
    PREFIX ex: <https://static.rwpz.net/spendcast/>
    
    SELECT ?transaction ?amount WHERE {
      ?transaction a exs:FinancialTransaction ;
        exs:hasMonetaryAmount ?amount_uri .
      ?amount_uri exs:hasAmount ?amount .
    }
    LIMIT 10
    """
)
```

### Validated Query Execution
```python
# Query with validation
result = await execute_sparql_validated(
    query="""
    PREFIX exs: <https://static.rwpz.net/spendcast/schema#>
    PREFIX ex: <https://static.rwpz.net/spendcast/>
    
    SELECT ?customer ?total_spent WHERE {
      ?transaction a exs:FinancialTransaction ;
        exs:hasParticipant ?role .
      ?role exs:isPlayedBy ?customer .
      ?customer exs:hasName "Jeanine Marie Blumenthal" .
      ?transaction exs:hasMonetaryAmount ?amount_uri .
      ?amount_uri exs:hasAmount ?amount .
    }
    GROUP BY ?customer
    """
)
```

## Common Query Patterns

### Customer Analysis
- Find all transactions for a specific customer
- Customer account summary
- Spending patterns over time

### Spending Analysis
- Monthly spending by category
- Top spending merchants
- Transaction frequency analysis

### Sustainability Analysis
- CO2 impact by purchase category
- Environmental impact over time
- Product sustainability metrics

### Product Analysis
- Product search by category
- Products with highest CO2 factors
- Price analysis by category

### Payment Analysis
- Payment card usage patterns
- Currency conversion analysis
- Transaction method distribution

## Query Validation

The `execute_sparql_validated` tool performs basic validation:

- ✅ Required prefixes (`exs:`, `ex:`)
- ✅ Basic SPARQL syntax (SELECT, ASK, CONSTRUCT, DESCRIBE)
- ✅ Balanced braces in WHERE clause
- ✅ Proper query structure

## Error Handling

The server provides comprehensive error handling:

- **HTTP Errors**: Detailed status codes and response text
- **Connection Errors**: Network and timeout issues
- **JSON Errors**: Invalid response parsing
- **Validation Errors**: Query syntax and structure issues

## Best Practices

### 1. Always Use Correct Prefixes
```sparql
PREFIX exs: <https://static.rwpz.net/spendcast/schema#>
PREFIX ex: <https://static.rwpz.net/spendcast/>
```

### 2. Filter Large Result Sets
```sparql
FILTER(?date >= "2025-01-01"^^xsd:date && ?date <= "2025-12-31"^^xsd:date)
LIMIT 100
```

### 3. Use Proper Joins
```sparql
?transaction exs:hasReceipt ?receipt .
?receipt exs:hasLineItem ?line_item .
```

### 4. Handle Optional Data
```sparql
OPTIONAL { ?product exs:co2Factor ?co2_factor }
```

### 5. Group and Aggregate
```sparql
GROUP BY ?category
ORDER BY DESC(?total_spent)
```

## Troubleshooting

### Common Issues

1. **Missing Prefixes**: Ensure both `exs:` and `ex:` are included
2. **Unbalanced Braces**: Check WHERE clause syntax
3. **Invalid Property Names**: Use exact property names from the schema
4. **Date Format**: Use proper `xsd:date` format
5. **Large Results**: Always use LIMIT for large datasets

### Debug Tips

1. Start with simple queries and build complexity
2. Use the schema summary resource to verify property names
3. Check example queries for working patterns
4. Validate queries before execution
5. Monitor GraphDB logs for detailed error information

## API Reference

### Tool Parameters

#### `execute_sparql`
- `query` (string): SPARQL query string

#### `execute_sparql_validated`
- `query` (string): SPARQL query string

### Return Format

Successful queries return GraphDB's SPARQL results in JSON format.

Error responses include:
- `error`: Error message
- `query`: Original query (for validation errors)
- `validation_tips`: Helpful suggestions (for validation errors)

## Contributing

When adding new features:

1. Follow the existing code structure
2. Add comprehensive documentation
3. Include error handling
4. Add validation where appropriate
5. Update this README

## 🔒 License and Usage Restrictions

The code and data in this repository are provided by PostFinance AG
solely for participation in the BernHackt 2025 (22.08.2025 - 24.08.2025).

- Use is permitted **only during the event**.  
- Redistribution, retention after the event, or use for any other purpose 
  is **strictly prohibited**.  
- All rights remain with PostFinance AG.  

See [LICENSE](../../LICENSE) for full terms.