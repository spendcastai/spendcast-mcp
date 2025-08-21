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

mcp = FastMCP(name="spendcast-mcp", instructions="MCP server for executing SPARQL queries against a financial data triple store")

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
    - **Parties**: People (customers) and organizations (banks, merchants) with detailed contact information\n
    - **Payment Cards**: Credit/debit cards linked to accounts for transactions\n
    - **Financial Transactions**: Complete transaction records with amounts, dates, status, and types\n\n
    **Retail & Receipt Data:**\n
    - **Receipts**: Detailed purchase receipts with line items, dates, and payment methods\n
    - **Products**: Migros product catalog with EAN codes, names, and category links\n
    - **Product Categories**: Hierarchical classification (beverages, bread, cleaning, etc.)\n
    - **Merchants**: Business entities with names and addresses\n\n
    **Key Data Properties:**\n
    - Transaction amounts in CHF with currency information\n
    - Complete transaction dates and status tracking\n
    - Account balances and payment card details\n
    - Product information and receipt line items\n
    - Customer account and card relationships\n\n
    **Query Capabilities:**\n
    - Find transactions by customer, date, amount, or merchant\n
    - Analyze spending patterns through accounts and payment cards\n
    - Track account balances and payment card usage\n
    - Search products and receipt details\n
    - Analyze customer financial relationships\n\n
    **Important Data Structure Insights:**\n
    - **Customers** are `exs:Person` entities with direct `exs:hasAccount` relationships\n
    - **Payment Cards** are linked to accounts via `exs:linkedAccount`\n
    - **Transactions** use accounts (not cards directly) through `exs:hasParticipant` + `exs:Payer` role + `exs:isPlayedBy`\n
    - **Receipts** have line items with products, but product categories may have data structure issues\n
    - **Party Roles** (Payer, Payee, AccountHolder, CardHolder) mediate relationships between entities\n\n
    **Common Query Patterns:**\n
    - Use `exs:` prefix for schema properties (e.g., `exs:hasMonetaryAmount`)\n
    - Use `ex:` prefix for data instances (e.g., `ex:Swiss_franc`)\n
    - Find customer transactions through accounts: `?person exs:hasAccount ?account`\n
    - Find card transactions through linked accounts: `?card exs:linkedAccount ?account`\n
    - Join transactions with receipts using `exs:hasReceipt`\n\n
    **Example Queries:**\n
    - Find all transactions for a specific customer (working)\n
    - Find transactions through bank accounts only (working)\n
    - Find transactions through payment cards only (working)\n
    - Get customer account summary (working)\n
    - Monthly spending by category (pending category data fix)\n

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
- **Person** - Individual customers with accounts and payment cards
- **Organization** - Banks, merchants, and other business entities
- **PaymentCard** - Credit/debit cards linked to accounts for transactions
- **FinancialTransaction** - Money transfers with amounts, dates, and status
- **MonetaryAmount** - Currency amounts (primarily CHF)
- **PartyRole** - Mediator entities (Payer, Payee, AccountHolder, CardHolder)

### Retail Entities  
- **Receipt** - Purchase documents with line items and totals
- **ReceiptLineItem** - Individual items on receipts with products and amounts
- **Product** - Goods and services with names, descriptions, and category links
- **ProductCategory** - Hierarchical product classification (beverages, bread, cleaning, etc.)
- **Merchant** - Business entities with names and addresses

## Key Properties

### Person Properties
- `exs:hasName` - Customer's full name
- `exs:hasAccount` - Direct link to customer's accounts
- `exs:hasPaymentCard` - Direct link to customer's payment cards
- `exs:hasEmailAddress` - Customer's email
- `exs:hasTelephoneNumber` - Customer's phone number

### Account Properties
- `exs:hasAccountHolder` - Links account to customer through role
- `exs:hasAccountProvider` - Links account to bank through role
- `exs:hasInitialBalance` - Starting balance
- `exs:hasCurrency` - Account currency (primarily CHF)

### Payment Card Properties
- `exs:hasCardHolder` - Links card to customer through role
- `exs:linkedAccount` - Links card to the account it uses for transactions
- `exs:hasCardIssuer` - Links card to issuing bank through role

### Transaction Properties
- `exs:hasMonetaryAmount` - Transaction amount
- `exs:hasTransactionDate` - When transaction occurred
- `exs:hasParticipant` - Who was involved (through PartyRole)
- `exs:status` - settled/pending/rejected/cancelled
- `exs:transactionType` - expense/income/transfer
- `exs:hasReceipt` - Links to purchase receipt (if applicable)

### Product Properties
- `exs:category` - Product classification (currently linking to placeholder URI)
- `exs:name` - Product name
- `exs:description` - Product description
- `exs:migrosId` - Migros product identifier

### Receipt Line Item Properties
- `exs:hasProduct` - Links to product (both name and GTIN)
- `exs:lineSubtotal` - Amount for this line item
- `exs:quantity` - Number of units purchased
- `exs:unitPrice` - Price per unit

### Merchant Properties
- `exs:hasName` - Business name
- `exs:hasAddress` - Business location

## Common Query Patterns

### Find Customer Transactions (Working Example)
```sparql
PREFIX exs: <https://static.rwpz.net/spendcast/schema#>
PREFIX ex: <https://static.rwpz.net/spendcast/>

SELECT ?transaction ?amount ?date ?merchant ?payer_type WHERE {
  # Find the customer
  ?person exs:hasName "Jeanine Marie Blumenthal" .
  
  # Get their accounts
  ?person exs:hasAccount ?account .
  ?account a ?payer_type .
  
  # Find transactions where the account is a payer
  ?transaction a exs:FinancialTransaction .
  ?transaction exs:hasParticipant ?payerRole .
  ?payerRole a exs:Payer .
  ?payerRole exs:isPlayedBy ?account .
  
  # Get transaction details
  ?transaction exs:hasMonetaryAmount ?amount_uri .
  ?amount_uri exs:hasAmount ?amount .
  ?transaction exs:hasTransactionDate ?date .
  
  # Get merchant information (payee)
  ?transaction exs:hasParticipant ?payeeRole .
  ?payeeRole a exs:Payee .
  ?payeeRole exs:isPlayedBy ?merchant .
  ?merchant rdfs:label ?merchant_label .
}
```

### Find Transactions Through Payment Cards (Working Example)
```sparql
PREFIX exs: <https://static.rwpz.net/spendcast/schema#>
PREFIX ex: <https://static.rwpz.net/spendcast/>

SELECT ?transaction ?amount ?date ?card_type ?linked_account WHERE {
  ?person exs:hasName "Jeanine Marie Blumenthal" .
  ?card exs:hasCardHolder ?cardHolderRole .
  ?cardHolderRole exs:isPlayedBy ?person .
  ?card a ?card_type .
  ?card exs:linkedAccount ?linked_account .
  
  # Find transactions where the linked account is a payer
  ?transaction a exs:FinancialTransaction .
  ?transaction exs:hasParticipant ?payerRole .
  ?payerRole a exs:Payer .
  ?payerRole exs:isPlayedBy ?linked_account .
  
  ?transaction exs:hasMonetaryAmount ?amount_uri .
  ?amount_uri exs:hasAmount ?amount .
  ?transaction exs:hasTransactionDate ?date .
}
```

### Get Customer Account Summary (Working Example)
```sparql
PREFIX exs: <https://static.rwpz.net/spendcast/schema#>
PREFIX ex: <https://static.rwpz.net/spendcast/>

SELECT ?account ?type ?balance ?currency WHERE {
  ?account a ?account_type .
  ?account exs:hasAccountHolder ?holder_role .
  ?holder_role exs:isPlayedBy ?person .
  ?person exs:hasName "Jeanine Marie Blumenthal" .
  ?account exs:hasInitialBalance ?balance .
  ?account exs:hasCurrency ?currency .
  VALUES ?account_type { exs:CheckingAccount exs:SavingsAccount exs:CreditCard exs:Retirement3A }
}
```

**Key Insights**: 
- **Direct relationships**: `?person exs:hasAccount ?account` and `?person exs:hasPaymentCard ?card`
- **Role-based relationships**: `?account exs:hasAccountHolder ?role` → `?role exs:isPlayedBy ?person`
- **Card-account linking**: `?card exs:linkedAccount ?account` (cards use accounts for transactions)
- **Transaction participation**: Through `exs:hasParticipant` + `exs:Payer` role + `exs:isPlayedBy`
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

**Customers (Persons) have both direct and role-based relationships:**

1. **Direct relationships**: `?person exs:hasAccount ?account` and `?person exs:hasPaymentCard ?card`
2. **Role-based relationships**: 
   - `?account exs:hasAccountHolder ?holderRole` → `?holderRole exs:isPlayedBy ?person`
   - `?card exs:hasCardHolder ?cardHolderRole` → `?cardHolderRole exs:isPlayedBy ?person`

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

**Important**: Payment cards are linked to accounts via `exs:linkedAccount`, and transactions use the linked account (not the card directly).

## Customer Analysis

### 1. Find All Transactions for a Specific Customer ✅ **WORKING**
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

### 1a. Find Transactions Through Bank Accounts Only ✅ **WORKING**
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

### 1b. Find Transactions Through Payment Cards Only ✅ **WORKING**
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

### 3. Monthly Spending by Category ⚠️ **PENDING CATEGORY DATA FIX**
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

**Note**: This example currently returns no results due to product category data structure issues. Products link to `https://static.rwpz.net/spendcast/migros/category/` but actual category instances are at `https://static.rwpz.net/spendcast/product/Category_*`.

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

## Current Example Status

### ✅ **Working Examples**
- **Example 1**: Find All Transactions for a Specific Customer
- **Example 1a**: Find Transactions Through Bank Accounts Only  
- **Example 1b**: Find Transactions Through Payment Cards Only
- **Example 2**: Customer Account Summary

### ⚠️ **Examples with Issues**
- **Example 3**: Monthly Spending by Category - Product category data structure mismatch
- **Examples 5-6**: CO2 Impact Analysis - Depend on product categories
- **Examples 7-8**: Product Analysis - Depend on product categories

### 🔧 **Known Data Structure Issues**
- Products link to `https://static.rwpz.net/spendcast/migros/category/` (placeholder)
- Actual category instances are at `https://static.rwpz.net/spendcast/product/Category_*`
- Category relationships need to be fixed in the data

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
