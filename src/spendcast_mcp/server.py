import json
import logging
import os
from typing import Any, Dict

import httpx
from dotenv import load_dotenv
from fastmcp import Context, FastMCP
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


# --- Configuration ---
class GraphDBConfig(BaseModel):
    """Configuration for the GraphDB connection."""

    url: str = Field(..., description="The URL of the GraphDB SPARQL endpoint.")
    username: str = Field(..., description="The username for GraphDB authentication.")
    password: str = Field(..., description="The password for GraphDB authentication.")


def get_config() -> GraphDBConfig:
    """Loads configuration from environment variables."""
    graphdb_url = os.getenv("GRAPHDB_URL")
    graphdb_user = os.getenv("GRAPHDB_USER")
    graphdb_password = os.getenv("GRAPHDB_PASSWORD")

    if not graphdb_url:
        logging.error("GRAPHDB_URL environment variable not set.")
        raise ValueError("GRAPHDB_URL environment variable not set.")
    if not graphdb_user:
        logging.error("GRAPHDB_USER environment variable not set.")
        raise ValueError("GRAPHDB_USER environment variable not set.")
    if not graphdb_password:
        logging.error("GRAPHDB_PASSWORD environment variable not set.")
        raise ValueError("GRAPHDB_PASSWORD environment variable not set.")

    return GraphDBConfig(
        url=graphdb_url, username=graphdb_user, password=graphdb_password
    )

mcp = FastMCP()

# --- Tool Definition ---
async def _execute_sparql_impl(ctx: Context, query: str) -> Dict[str, Any]:
    """
    Internal implementation of SPARQL query execution.
    
    :param ctx: The tool context (unused in this implementation).
    :param query: The SPARQL query string to execute.
    :return: The JSON result from GraphDB or an error dictionary.
    """
    config = get_config()
    logging.info(f"Executing SPARQL query on {config.url}")

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/sparql-results+json",
    }
    data = {"query": query}
    auth = httpx.BasicAuth(config.username, config.password)

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                config.url, headers=headers, data=data, auth=auth, timeout=30.0
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        error_msg = f"HTTP error occurred: {e.response.status_code} - {e.response.text}"
        logging.error(error_msg)
        return {"error": error_msg}
    except httpx.RequestError as e:
        error_msg = f"An error occurred while connecting to GraphDB: {e}"
        logging.error(error_msg)
        return {"error": error_msg}
    except json.JSONDecodeError:
        logging.error("Failed to decode JSON response from GraphDB.")
        return {"error": "Invalid JSON response from GraphDB."}


@mcp.tool()
async def execute_sparql(ctx: Context, query: str) -> Dict[str, Any]:
    """
    Execute SPARQL queries against a financial data triple store containing comprehensive banking, transaction, and retail data. The store includes:\n\n
    **Core Financial Entities:**\n
    - **Accounts**: Checking, savings, credit cards, retirement accounts (3A pillar)\n
    - **Parties**: Customers, banks, merchants, organizations with detailed contact information\n
    - **Payment Cards**: Debit/credit cards with limits, status, and issuer details\n
    - **Financial Transactions**: Complete transaction records with amounts, dates, status, and types\n\n
    **Retail & Receipt Data:**\n
    - **Receipts**: Detailed purchase receipts with line items, dates, payment methods\n
    - **Products**: Migros product catalog with EAN codes, prices, categories, CO2 factors\n
    - **Product Categories**: Hierarchical classification with tax rates and sustainability metrics\n
    - **Merchants**: Business entities with MCC codes and address information\n\n
    **Key Data Properties:**\n
    - Transaction amounts in CHF, EUR, USD with currency conversions\n
    - CO2 footprint calculations for products and categories\n
    - Tax classifications (standard, reduced, zero, exempt)\n
    - Merchant Category Codes (MCC) for business classification\n
    - Complete address and contact information for parties\n\n
    **Query Capabilities:**\n
    - Find transactions by date, amount, merchant, or account\n
    - Analyze spending patterns and category distributions\n
    - Calculate CO2 impact of purchases\n
    - Track account balances and card usage\n
    - Search products by category, price, or sustainability metrics\n\n
    **Common Query Patterns:**\n
    - Use `exs:` prefix for schema properties (e.g., `exs:hasMonetaryAmount`)\n
    - Use `ex:` prefix for data instances (e.g., `ex:Swiss_franc`)\n
    - Join transactions with receipts using `exs:hasReceipt`\n
    - Filter by account holders using `exs:hasAccountHolder`\n
    - Query product categories with `exs:hasCategory`\n\n
    **Example Queries:**\n
    - Find all transactions for a specific customer\n
    - Calculate total spending by category for a date range\n
    - List products with highest CO2 factors\n
    - Find merchants by location or MCC code\n
    - Analyze payment card usage patterns\n

    :param ctx: The tool context (unused in this implementation).
    :param query: The SPARQL query string to execute.
    :return: The JSON result from GraphDB or an error dictionary.
    """
    return await _execute_sparql_impl(ctx, query)


# --- Resource Tools ---
# Resources will be added after the functions are defined


@mcp.resource(
    "internal://schema_summary.md",
    name="schema_summary",
    description="Human-readable summary of key triple store entities and relationships",
    mime_type="text/markdown"
)
def get_schema_summary() -> str:
    """Generate a human-readable schema summary."""
    return """# Triple Store Schema Summary

## Core Entity Classes

### Financial Entities
- **Account** - Banking accounts (checking, savings, credit cards, retirement 3A)
- **Party** - People and organizations (customers, banks, merchants)
- **PaymentCard** - Credit/debit cards with limits and status
- **FinancialTransaction** - Money transfers with amounts, dates, and status
- **MonetaryAmount** - Currency amounts with exchange rates

### Retail Entities  
- **Receipt** - Purchase documents with line items and totals
- **ReceiptLineItem** - Individual items on receipts
- **Product** - Goods and services with pricing and metadata
- **ProductCategory** - Hierarchical product classification
- **Merchant** - Business entities with MCC codes

## Key Properties

### Account Properties
- `exs:hasAccountHolder` - Links account to customer
- `exs:hasAccountProvider` - Links account to bank
- `exs:accountNumber` - Account identifier
- `exs:hasInitialBalance` - Starting balance

### Transaction Properties
- `exs:hasMonetaryAmount` - Transaction amount
- `exs:hasTransactionDate` - When transaction occurred
- `exs:hasParticipant` - Who was involved
- `exs:status` - settled/pending/rejected/cancelled
- `exs:transactionType` - expense/income/transfer

### Product Properties
- `exs:hasCategory` - Product classification
- `exs:co2Factor` - Environmental impact metric
- `exs:taxClass` - standard/reduced/zero/exempt
- `exs:unitPrice` - Price per unit
- `exs:migrosId` - Migros product identifier

### Merchant Properties
- `exs:merchantCategory` - MCC code classification
- `exs:hasAddress` - Business location
- `exs:hasName` - Business name

## Common Query Patterns

### Find Customer Transactions
```sparql
PREFIX exs: <https://static.rwpz.net/spendcast/schema#>
PREFIX ex: <https://static.rwpz.net/spendcast/>

SELECT ?transaction ?amount ?date WHERE {
  # Find customer's account
  ?customer exs:hasName "Customer Name" ;
    exs:hasAccount ?account .
  
  # Transaction has a payer role played by the account
  ?transaction a exs:FinancialTransaction ;
    exs:hasParticipant ?payerRole .
  ?payerRole a exs:Payer ;
    exs:isPlayedBy ?account .
  
  # Get transaction details
  ?transaction exs:hasMonetaryAmount ?amount_uri .
  ?amount_uri exs:hasAmount ?amount ;
    exs:hasTransactionDate ?date .
}
```

**Note**: Customers participate in transactions through Party Roles (Payer, Payee) played by their accounts or payment cards.

### Analyze Spending by Category
```sparql
PREFIX exs: <https://static.rwpz.net/spendcast/schema#>
PREFIX ex: <https://static.rwpz.net/spendcast/>

SELECT ?category ?total WHERE {
  ?transaction a exs:FinancialTransaction ;
    exs:hasReceipt ?receipt .
  ?receipt exs:hasLineItem ?line_item .
  ?line_item exs:hasProduct ?product .
  ?product exs:hasCategory ?category .
  ?transaction exs:hasMonetaryAmount ?amount_uri .
  ?amount_uri exs:hasAmount ?amount .
}
GROUP BY ?category
ORDER BY DESC(?total)
```

### CO2 Impact Analysis
```sparql
PREFIX exs: <https://static.rwpz.net/spendcast/schema#>
PREFIX ex: <https://static.rwpz.net/spendcast/>

SELECT ?category ?co2_factor ?total_spent WHERE {
  ?category a exs:ProductCategory ;
    exs:co2Factor ?co2_factor .
  ?product exs:hasCategory ?category .
  ?line_item exs:hasProduct ?product ;
    exs:lineSubtotal ?amount .
}
GROUP BY ?category ?co2_factor
ORDER BY DESC(?co2_factor)
```
"""


@mcp.resource(
    "internal://example_queries.md",
    name="example_queries",
    description="Common SPARQL query patterns and examples for the financial data store",
    mime_type="text/markdown"
)
def get_example_queries() -> str:
    """Generate example SPARQL queries."""
    return """# Example SPARQL Queries for Financial Data Store

## Important Note on Customer-Transaction Relationships

**Customers do not directly participate in transactions.** They participate through **Party Roles**:

1. **Account Holder Role**: `?account exs:hasAccountHolder ?holderRole` → `?holderRole exs:isPlayedBy ?customer`
2. **Card Holder Role**: `?card exs:hasCardHolder ?cardHolderRole` → `?cardHolderRole exs:isPlayedBy ?customer`

**Transactions have participants through Party Roles:**
- `?transaction exs:hasParticipant ?payerRole` → `?payerRole exs:isPlayedBy ?payer`
- `?transaction exs:hasParticipant ?payeeRole` → `?payeeRole exs:isPlayedBy ?payee`

**Key Party Role Types:**
- `exs:Payer` - The party paying money
- `exs:Payee` - The party receiving money  
- `exs:AccountHolder` - The party owning an account
- `exs:CardHolder` - The party holding a payment card
- `exs:AccountProvider` - The bank providing an account
- `exs:CardIssuer` - The bank issuing a payment card

## Customer Analysis

### 1. Find All Transactions for a Specific Customer
```sparql
PREFIX exs: <https://static.rwpz.net/spendcast/schema#>
PREFIX ex: <https://static.rwpz.net/spendcast/>

SELECT ?transaction ?amount ?date ?merchant ?payer_type WHERE {
  # Find the customer
  ?customer exs:hasName "Jeanine Marie Blumenthal" .
  
  # Option 1: Through bank accounts (customer is payer)
  {
    ?customer exs:hasAccount ?account .
    ?account a ?payer_type .
    ?transaction a exs:FinancialTransaction ;
      exs:hasParticipant ?payerRole .
    ?payerRole a exs:Payer ;
      exs:isPlayedBy ?account .
  }
  UNION
  # Option 2: Through payment cards (customer is payer)
  {
    ?customer exs:hasPaymentCard ?card .
    ?card a ?payer_type .
    ?transaction a exs:FinancialTransaction ;
      exs:hasParticipant ?payerRole .
    ?payerRole a exs:Payer ;
      exs:isPlayedBy ?card .
  }
  
  # Get transaction details
  ?transaction exs:hasMonetaryAmount ?amount_uri .
  ?amount_uri exs:hasAmount ?amount ;
    exs:hasTransactionDate ?date .
  
  # Get merchant information (merchant is payee)
  ?transaction exs:hasParticipant ?payeeRole .
  ?payeeRole a exs:Payee ;
    exs:isPlayedBy ?merchant .
  ?merchant rdfs:label ?merchant .
}
ORDER BY DESC(?date)
```

### 1a. Find Transactions Through Bank Accounts Only
```sparql
PREFIX exs: <https://static.rwpz.net/spendcast/schema#>
PREFIX ex: <https://static.rwpz.net/spendcast/>

SELECT ?transaction ?amount ?date ?account_type WHERE {
  ?customer exs:hasName "Jeanine Marie Blumenthal" .
  ?account exs:hasAccountHolder ?holderRole .
  ?holderRole exs:isPlayedBy ?customer .
  ?account a ?account_type .
  ?transaction a exs:FinancialTransaction ;
    exs:hasParticipant ?payerRole .
  ?payerRole a exs:Payer ;
    exs:isPlayedBy ?account .
  ?transaction exs:hasMonetaryAmount ?amount_uri .
  ?amount_uri exs:hasAmount ?amount ;
    exs:hasTransactionDate ?date .
}
ORDER BY DESC(?date)
```

### 1b. Find Transactions Through Payment Cards Only
```sparql
PREFIX exs: <https://static.rwpz.net/spendcast/schema#>
PREFIX ex: <https://static.rwpz.net/spendcast/>

SELECT ?transaction ?amount ?date ?card_type WHERE {
  ?customer exs:hasName "Jeanine Marie Blumenthal" .
  ?card exs:hasCardHolder ?cardHolderRole .
  ?cardHolderRole exs:isPlayedBy ?customer .
  ?card a ?card_type .
  ?transaction a exs:FinancialTransaction ;
    exs:hasParticipant ?payerRole .
  ?payerRole a exs:Payer ;
    exs:isPlayedBy ?card .
  ?transaction exs:hasMonetaryAmount ?amount_uri .
  ?amount_uri exs:hasAmount ?amount ;
    exs:hasTransactionDate ?date .
}
ORDER BY DESC(?date)
```

### 2. Customer Account Summary
```sparql
PREFIX exs: <https://static.rwpz.net/spendcast/schema#>
PREFIX ex: <https://static.rwpz.net/spendcast/>

SELECT ?account ?type ?balance ?currency WHERE {
  ?account a ?account_type ;
    exs:hasAccountHolder ?holder_role .
  ?holder_role exs:isPlayedBy ?customer .
  ?customer exs:hasName "Jeanine Marie Blumenthal" .
  ?account exs:hasInitialBalance ?balance ;
    exs:hasCurrency ?currency .
  VALUES ?account_type { exs:CheckingAccount exs:SavingsAccount exs:CreditCard exs:Retirement3A }
}
```

## Spending Analysis

### 3. Monthly Spending by Category
```sparql
PREFIX exs: <https://static.rwpz.net/spendcast/schema#>
PREFIX ex: <https://static.rwpz.net/spendcast/>

SELECT ?month ?category ?category_label (SUM(?amount) AS ?total_spent) WHERE {
  ?transaction a exs:FinancialTransaction ;
    exs:hasTransactionDate ?date ;
    exs:hasReceipt ?receipt .
  ?receipt exs:hasLineItem ?line_item .
  ?line_item exs:hasProduct ?product .
  ?product exs:hasCategory ?category .
  ?category rdfs:label ?category_label .
  ?transaction exs:hasMonetaryAmount ?amount_uri .
  ?amount_uri exs:hasAmount ?amount .
  BIND(STRDT(CONCAT(YEAR(?date), "-", STR(MONTH(?date)), "-01"), xsd:date) AS ?month)
  FILTER(?date >= "2025-01-01"^^xsd:date && ?date <= "2025-12-31"^^xsd:date)
}
GROUP BY ?month ?category ?category_label
ORDER BY ?month DESC(?total_spent)
```

### 4. Top Spending Merchants
```sparql
PREFIX exs: <https://static.rwpz.net/spendcast/schema#>
PREFIX ex: <https://static.rwpz.net/spendcast/>

SELECT ?merchant (SUM(?amount) AS ?total_spent) (COUNT(?transaction) AS ?transaction_count) WHERE {
  ?transaction a exs:FinancialTransaction ;
    exs:hasParticipant ?payeeRole .
  ?payeeRole a exs:Payee ;
    exs:isPlayedBy ?merchant .
  ?merchant rdfs:label ?merchant .
  ?transaction exs:hasMonetaryAmount ?amount_uri .
  ?amount_uri exs:hasAmount ?amount .
  FILTER(?transaction exs:transactionType "expense")
}
GROUP BY ?merchant
ORDER BY DESC(?total_spent)
LIMIT 20
```

## Sustainability Analysis

### 5. CO2 Impact by Purchase Category
```sparql
PREFIX exs: <https://static.rwpz.net/spendcast/schema#>
PREFIX ex: <https://static.rwpz.net/spendcast/>

SELECT ?category ?category_label ?co2_factor (SUM(?amount) AS ?total_spent) (SUM(?amount * ?co2_factor) AS ?co2_impact) WHERE {
  ?category a exs:ProductCategory ;
    exs:co2Factor ?co2_factor ;
    rdfs:label ?category_label .
  ?product exs:hasCategory ?category .
  ?line_item exs:hasProduct ?product ;
    exs:lineSubtotal ?amount .
  ?receipt exs:hasLineItem ?line_item .
  ?transaction exs:hasReceipt ?receipt .
}
GROUP BY ?category ?category_label ?co2_factor
ORDER BY DESC(?co2_impact)
```

### 6. Environmental Impact by Month
```sparql
PREFIX exs: <https://static.rwpz.net/spendcast/schema#>
PREFIX ex: <https://static.rwpz.net/spendcast/>

SELECT ?month (SUM(?amount * ?co2_factor) AS ?total_co2_impact) (SUM(?amount) AS ?total_spent) WHERE {
  ?transaction a exs:FinancialTransaction ;
    exs:hasTransactionDate ?date ;
    exs:hasReceipt ?receipt .
  ?receipt exs:hasLineItem ?line_item .
  ?line_item exs:hasProduct ?product ;
    exs:lineSubtotal ?amount .
  ?product exs:hasCategory ?category .
  ?category exs:co2Factor ?co2_factor .
  BIND(STRDT(CONCAT(YEAR(?date), "-", STR(MONTH(?date)), "-01"), xsd:date) AS ?month)
  FILTER(?date >= "2025-01-01"^^xsd:date && ?date <= "2025-12-31"^^xsd:date)
}
GROUP BY ?month
ORDER BY ?month
```

## Product Analysis

### 7. Product Search by Category
```sparql
PREFIX exs: <https://static.rwpz.net/spendcast/schema#>
PREFIX ex: <https://static.rwpz.net/spendcast/>

SELECT ?product ?name ?price ?category WHERE {
  ?product a exs:Product ;
    exs:name ?name ;
    exs:unitPrice ?price ;
    exs:hasCategory ?category .
  ?category rdfs:label ?category_label .
  FILTER(CONTAINS(LCASE(?category_label), "beverages"))
}
ORDER BY ?price
LIMIT 50
```

### 8. Products with Highest CO2 Factors
```sparql
PREFIX exs: <https://static.rwpz.net/spendcast/schema#>
PREFIX ex: <https://static.rwpz.net/spendcast/>

SELECT ?product ?name ?category ?co2_factor WHERE {
  ?product a exs:Product ;
    exs:name ?name ;
    exs:hasCategory ?category .
  ?category exs:co2Factor ?co2_factor ;
    rdfs:label ?category_label .
  FILTER(?co2_factor > 1.0)
}
ORDER BY DESC(?co2_factor)
LIMIT 20
```

## Payment Analysis

### 9. Payment Card Usage Patterns
```sparql
PREFIX exs: <https://static.rwpz.net/spendcast/schema#>
PREFIX ex: <https://static.rwpz.net/spendcast/>

SELECT ?card ?card_type ?total_spent ?transaction_count WHERE {
  ?transaction a exs:FinancialTransaction ;
    exs:hasCard ?card .
  ?card exs:cardType ?card_type ;
    exs:cardNumber ?card_number .
  ?transaction exs:hasMonetaryAmount ?amount_uri .
  ?amount_uri exs:hasAmount ?amount .
  FILTER(?transaction exs:transactionType "expense")
}
GROUP BY ?card ?card_type ?card_number
ORDER BY DESC(?total_spent)
```

### 10. Currency Conversion Analysis
```sparql
PREFIX exs: <https://static.rwpz.net/spendcast/schema#>
PREFIX ex: <https://static.rwpz.net/spendcast/>

SELECT ?transaction ?base_currency ?counter_currency ?exchange_rate ?date WHERE {
  ?transaction a exs:FinancialTransaction ;
    exs:hasCurrencyConversion ?conversion .
  ?conversion exs:hasBaseAmount ?base_amount ;
    exs:hasCounterAmount ?counter_amount ;
    exs:exchangeRate ?exchange_rate ;
    exs:conversionDate ?date .
  ?base_amount exs:hasCurrency ?base_currency .
  ?counter_amount exs:hasCurrency ?counter_currency .
}
ORDER BY DESC(?date)
```

## Tips for Writing Queries

1. **Always use the correct prefixes**: `exs:` for schema, `ex:` for data
2. **Filter by date ranges** using `FILTER()` with `xsd:date` comparisons
3. **Group results** using `GROUP BY` for aggregations
4. **Order results** using `ORDER BY` for meaningful sorting
5. **Limit large result sets** using `LIMIT` to avoid overwhelming responses
6. **Use `BIND()`** for calculated values like CO2 impact
7. **Join entities properly** using the defined object properties
8. **Handle optional data** using `OPTIONAL` for nullable relationships
"""


@mcp.resource(
    "https://static.rwpz.net/spendcast/schema#",
    name="triple_store_schema",
    description="Complete ontology and schema for the financial data triple store",
    mime_type="text/turtle"
)
def get_ontology_content() -> str:
    """Read the ontology.ttl file content."""
    try:
        # Try data/ontology.ttl first (for development)
        ontology_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "ontology.ttl")
        if not os.path.exists(ontology_path):
            # Fall back to deploy/ontology.ttl (for production)
            ontology_path = os.path.join(os.path.dirname(__file__), "..", "..", "deploy", "ontology.ttl")
        
        with open(ontology_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "# Ontology file not found. Please ensure data/ontology.ttl or deploy/ontology.ttl exists."
    except Exception as e:
        return f"# Error reading ontology file: {str(e)}"


# --- Query Validation ---
def validate_sparql_query(query: str) -> tuple[bool, str]:
    """
    Basic SPARQL query validation.
    
    :param query: The SPARQL query string to validate
    :return: Tuple of (is_valid, error_message)
    """
    # Check for required prefixes
    required_prefixes = ["exs:", "ex:"]
    missing_prefixes = []

    for prefix in required_prefixes:
        if prefix not in query:
            missing_prefixes.append(prefix)

    if missing_prefixes:
        return False, f"Missing required prefixes: {', '.join(missing_prefixes)}"

    # Check for basic SPARQL syntax
    if not query.strip().upper().startswith(("SELECT", "ASK", "CONSTRUCT", "DESCRIBE")):
        return False, "Query must start with SELECT, ASK, CONSTRUCT, or DESCRIBE"

    # Check for balanced braces
    if query.count('{') != query.count('}'):
        return False, "Unbalanced braces in SPARQL query"

    # Check for basic WHERE clause
    if '{' not in query or '}' not in query:
        return False, "Missing WHERE clause with braces"

    return True, "Query is valid"


# --- Enhanced SPARQL Tool with Validation ---
@mcp.tool()
async def execute_sparql_validated(ctx: Context, query: str) -> Dict[str, Any]:
    """
    Execute SPARQL queries with validation against a financial data triple store.
    
    This tool provides the same functionality as execute_sparql but includes
    basic query validation to catch common syntax errors before sending to GraphDB.
    
    :param ctx: The tool context (unused in this implementation).
    :param query: The SPARQL query string to execute.
    :return: The JSON result from GraphDB or an error dictionary.
    """
    # Validate the query first
    is_valid, error_message = validate_sparql_query(query)
    if not is_valid:
        return {
            "error": f"SPARQL validation failed: {error_message}",
            "query": query,
            "validation_tips": [
                "Ensure your query starts with SELECT, ASK, CONSTRUCT, or DESCRIBE",
                "Include both exs: and ex: prefixes",
                "Check that all braces { } are properly balanced",
                "Verify your WHERE clause syntax"
            ]
        }

    # If validation passes, execute the query
    return await _execute_sparql_impl(ctx, query)


# --- Resource Registration ---
# Resources are now registered using decorators above


if __name__ == "__main__":
    load_dotenv()  # Load environment variables from .env file
    get_config()  # Validate config on startup
    mcp.run()
