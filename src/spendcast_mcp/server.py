import asyncio
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

def get_schema_description():
    try:
      schema_path = os.path.join(
          os.path.dirname(__file__), "schema-description.md"
      )

      with open(schema_path, "r", encoding="utf-8") as f:
          return f.read()
    except FileNotFoundError:
      return ""

def get_sparql_examples():
    try:
      examples_path = os.path.join(
          os.path.dirname(__file__), "query_examples.yaml"
      )

      with open(examples_path, "r", encoding="utf-8") as f:
          return f.read()
    except FileNotFoundError:
      return ""


mcp = FastMCP(
    name="spendcast-mcp",
    instructions="MCP server for executing SPARQL queries against a financial data triple store",
)


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
    Executes SPARQL queries in a financial data triple store that contains comprehensive bank account, transaction data about the user and information about the purchased items. Detailed information on: bank accounts, parties, payments, payment cards, financial transactions, purchase receipts, products, product categories, and stores where purchases were made by the user during the period from July 1, 2024, to June 30, 2025.

    # Schema description
    ## Node Types
      (pfm:Party() /* Represents a party involved in a financial transaction. */ {
          hasName: STRING /* The name of a party */
          hasTelephoneNumber /* The telephone number of a party */
          hasEmailAddress  /* The email address of a party */
      })

      (pfm:Person(Party) /* An individual human being, subclass of Party */ {
          birthDate: DATE /* The birth date of a person */
          citizenship: STRING /* The citizenship of a person */
      })

      (pfm:Address() /* A physical or logical address */ {
          addressType: STRING /* The type of address (e.g., home, work, billing) */
          street: STRING /* The street address */
          city: STRING /* The city name */
          postalCode: STRING /* The postal or ZIP code */
          country: STRING /* The country name */
          state: STRING /* The state or province name */
          exs:description /* A description of the address */
      })

      (pfm:Organization(Party) /* A structured group of people with a common purpose, subclass of Party */ {
          merchantCategory: skos:Concept /* Links a merchant to their category classification */ 
      })

      (pfm:Merchant(Party)  /* An organization that sells goods or services, subclass of Party */ {})
      (pfm:Bank(Party)  /* A financial institution that provides banking services, subclass of Party */ {})
      (pfm:CardSchemeOperator(Organization) /* An organization that operates a payment card scheme */ {})

      (pfm:Account() /* A party that owns an account */ {
          accountNumber: STRING /* The account number identifier */
          hasInternationalBankAccountIdentifier: STRING /* The IBAN (International Bank Account Number) */
          hasAccountPurpose: STRING /* The purpose of the account (description) */ 
          hasInitialBalance: NUMBER /* The initial balance of the account */
          hasOverdraftLimit: NUMBER /* The overdraft limit of the account */
      })

      (pfm:CheckingAccount(Account) /* A type of account that allows for frequent deposits and withdrawals, subclass of account */ {
      })

      (pfm:SavingsAccount(Account) /* A type of account designed for saving money with interest, subclass of account */ {})
      (pfm:CreditCard(Account) /* A type of account tied to a credit card, subclass of account */ {})
      (pfm:Retirement3A(Account) /* A Swiss third pillar retirement account */ {})
      (pfm:Currency() /* A medium of exchange value */ {})
      (pfm:CurrencyConversion() /* A conversion between different currencies */ {
          conversionDate: DATE /* The date of a currency conversion */
      })

      (pfm:PaymentCard() /* A card used for making payments */ {
          cardNumber: STRING /* The card number of a payment card */
          cardType: STRING /* The type of payment card (e.g., debit, credit) */
          expirydate: DATE /* The expiry date of a payment card */
          dailyLimit: NUMBER /* The daily spending limit for a payment card */
          monthlyLimit: NUMBER /* The monthly spending limit for a payment card */
          contactlessEnabled: BOOLEAN /* Whether contactless payments are enabled for the card */
          onlineEnabled: BOOLEAN /* Whether online transactions are enabled for the card */
          withdrawalEnabled: BOOLEAN /* Whether cash withdrawals are enabled for the card */
      })

      (pfm:FinancialTransaction()  /* A financial event involving the transfer of money */ {
          hasTransactionDate: DATE /* The date of the transaction */
          status: STRING /* The status of a financial transaction */
          transactionType: StrING /* The type of financial transaction (e.g., expense, income) */
          valueDate: DATE /* The value date of a financial transaction */

      })

      (pfm:MonetaryAmount() /* An amount of money with a specified currency*/ {
          hasAmount: NUMBER
          hasCurrency: STRING /* The currency of the amount */ 
      })

      (pfm:PartyRole() /* A specific role a party plays in a financial context */ {
          isPlayedBy: Party /* Links a role to the party that plays it */
      })

      (pfm:Payer(PartyRole) /* A party that pays money in a transaction */ {

      })
      (pfm:Payee(PartyRole) /* A party that receives money in a transaction */ {

      })
      (pfm:AccountHolder(PartyRole) /* A party that owns an account */ {
          
      })
      (pfm:AccountProvider(PartyRole) /* A party that provides and services an account */ {

      })
      (pfm:CardHolder(PartyRole) /* A party that holds a payment card */ {

      })

      (pfm:CardIssuer(PartyRole) /* A party that issues payment cards */ {})

      (pfm:Receipt() /* A document confirming a purchase transaction */ {
          receiptId: STRING /* The identifier of a receipt */ 
          receiptDate: DATE /* The date of a receipt */
          receiptTime: TIME /* The time of a receipt */
          vatNumber: STRING /* The VAT number on a receipt */
          paymentMethod: STRING /* The payment method used */
          authorizationCode: STRING /* The authorization code for a transaction */
      })

      (pfm:ReceiptLineItem() /* An individual item on a receipt */ {
          itemDescription: STRING /* The description of a line item */
          quatity: NUMBER /* The quantity of a line item */
          lineSubtotal: NUMBER /* The subtotal for a line item */
      })

      (pfm:Product() /* */ {
          shortName: STRING /* A short name for a product, used in the RecipeLineItem */
          ean: STRING /* The European Article Number (barcode) */
          unitPrice: NUMBER /* The unit price of a product */
          taxRate: NUMBER /* The tax rate for a product */
          sku: STRING /* The Stock Keeping Unit identifier */
          origin: STRING /* he origin of a product */
          packaginSize: NUMBER /* The packaging size of a product */
          migrosID: STRING /* The Migros internal product identifier */
          name: STRING /* The name of a product */
          uid: STRING /* The unique identifier for a product */ 
          description: STRING /* The description of a product */ 
          migipediaURL: STRING /* The Migipedia URL for a product */
          imageURL: STRING /* The image URL for the product */
      })

      (pfm:ProductCategory() /* */ {
          taxClass: STRING /* The tax classification for a product category */
      })

      ## Relationships
      (pfm:Account)-[pfm:hasAccountHolder /* Links an account to its holder */ {}]->(pfm:AccountHolder)
      (pfm:Account)-[pfm:hasAccountProvider /* Links an account to its provider */ {}]->(pfm:AccountProvider)
      (pfm:Party)-[pfm:hasAccount Account /* Links a party to their account */ {}]->(pfm:Account)
      (pfm:CurrencyConversion)-[pfm:hasBaseAmount /* The amount of the base currency (source currency) */ {}]->(pfm:MonetaryAmount)
      (pfm:CurrencyConversion)-[hasCounterAmount: MonetaryAmount /* The amount converted to the destination currency */ {}]->(pfm:MonetaryAmount)
      (pfm:PaymentCard)-[hasCardIssuer /* Links a payment card to its issuer */ {}]->(pfm:CardIssuer)
      (pfm:PaymentCard)-[hasCardHolder /* Links a payment card to its issuer */ {}]->(pfm:CardHolder)
      (pfm:PaymentCard)-[cardSchemeOperator /* Links a payment card to its scheme operator */ {}]->(pfm:CardSchemeOperator)
      (pfm:PaymentCard)-[linkedAccount /* Links a payment card to its associated account */ {}]->(pfm:Account)
      (pfm:FinancialTransaction)->[hasMonetaryAmount /* */ {}]->(pfm:MonetaryAmount)
      (pfm:FinancialTransaction)->[hasParticipant /* Links a transaction to its participants, a transaction has at least 2 participants */ {}]->(pfm:PartyRole)
      (pfm:FinancialTransaction)->[hasReceipt /* Links a transaction to its receipt (optional)*/ {}]->(pfm:Receipt)
      (pfm:FinancialTransaction)->[hasCurrencyConversion /* */ {}]->(pfm:CurrencyConversion)
      (pfm:FinancialTransaction)->[hasCard /* */ {}]->(pfm:PaymentCard)
      (pfm:Party)-[hasAddress /* Links a party to an address  */ {}]->(pfm:Address)
      (pfm:PartyRole)-[isPlayedBy /* Links a role to the party that plays it */ {}]->(pfm:Party)
      (pfm:Receipt)-[hasLineItem /* Links a receipt to its line items (1..n) */ {}]->(pfm:ReceiptLineItem)
      (pfm:Receipt)-[hasTotalAmount /* The total amount of the purchase documented in the receipt (sum of all line item amounts) */ {}]->(pfm:MonetaryAmount)
      (pfm:Product)-[category /* Links a product to its category */ {}]->(pfm:ProductCategory)
    
    # Instructions
    - Do not escape new lines (\n) within SPARQL queries sent to the tool

    # Examples
    What follows in yaml format is a collection of common questions and the answer is the corresponding SPARQL-query. Use the examples to answer the users questions.

    ```yaml
    ---
    - question: Show my profile
      sparql: |
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX pfm: <https://static.rwpz.net/spendcast/schema#>
        select ?name ?birthDate ?phoneNumber
        WHERE {
        ?person a pfm:Person ;
        rdfs:label ?name .
        OPTIONAL { ?person pfm:birthDate ?birthDate } .
        OPTIONAL { ?person pfm:hasTelephoneNumber ?phoneNumber } .
        }
    - question: Show all my accounts with name, purpose, account number, currency and initial balance
      sparql: |
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX pfm: <https://static.rwpz.net/spendcast/schema#>
        SELECT ?label ?accountPurpose ?initialBalance ?accNum ?accountCurrency
        WHERE {
        ?account a pfm:Account ;
            pfm:hasAccountPurpose ?accountPurpose ;
            rdfs:label ?label .
            OPTIONAL{ ?account pfm:hasInitialBalance ?initialBalance} .
            OPTIONAL{ ?account pfm:accountNumber ?accNum} .
            OPTIONAL{ ?account pfm:hasCurrency ?accountCurrency}
            OPTIONAL{ ?account pfm:hasCurrency ?accountCurrency}
        }

    - question: Show me the current balance of the account number "1234567890" between 2024-07-01 and 2025-07-01
      sparql: |
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX pfm: <https://static.rwpz.net/spendcast/schema#>
        SELECT (SUM(IF(?transactionType = 'income', ?amount, -?amount)) as ?balance) where {
        ?account pfm:accountNumber "1234567890" .
        ?participantRole pfm:isPlayedBy ?account .
        ?transaction pfm:hasParticipant ?participantRole .

        ?transaction a pfm:FinancialTransaction ;
        pfm:hasMonetaryAmount ?monetaryAmount ;
        pfm:hasTransactionDate ?transactionDate ;
        pfm:transactionType ?transactionType ;
        pfm:status ?transactionStatus .
            
        ?monetaryAmount pfm:hasCurrency ?currency ;
        pfm:hasAmount ?amount .
            
        FILTER(strstarts(?transactionStatus, "settled"))
        FILTER (?transactionDate >= "2024-07-01"^^xsd:date)
        FILTER (?transactionDate < "2025-07-01"^^xsd:date)
        }
    - question: Show me the last 100 expense transactions ordered by transaction date, descending
      sparql: |
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        PREFIX pfm: <https://static.rwpz.net/spendcast/schema#>
        SELECT ?transactionId ?transactionDate ?transactionStatus ?transactionType ?amount ?currency ?payer ?payee ?receiptId {
            ?transaction a pfm:FinancialTransaction ;
            pfm:hasMonetaryAmount ?monetaryAmount ;
            pfm:hasTransactionDate ?transactionDate ;
            pfm:transactionType ?transactionType ;    
            rdfs:label ?transactionId ;
            pfm:status ?transactionStatus ;
            pfm:hasParticipant [
                a pfm:Payer ;
                pfm:isPlayedBy/rdfs:label ?payer
            #pfm:accountNumber ?payerAccountNumber 
            ] ;
            pfm:hasParticipant [
                a pfm:Payee ;
                pfm:isPlayedBy/rdfs:label ?payee 
            ] .
        
            OPTIONAL { ?transaction pfm:hasReceipt/rdfs:label ?receiptId } .
            ?monetaryAmount pfm:hasCurrency ?currency ;
            pfm:hasAmount ?amount .
        }

    - question: Show me all my payment cards
      sparql: |
        PREFIX pfm: <https://static.rwpz.net/spendcast/schema#> 
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> 
        SELECT ?cardNumber ?cardType ?expiryDate ?linkedAccountNumber ?cardIssuer ?cardSchemeOperator WHERE { 
            ?card a pfm:PaymentCard ;
            pfm:cardNumber ?cardNumber ;
            pfm:cardType ?cardType ;
            pfm:expiryDate ?expiryDate ;
            pfm:hasCardIssuer/pfm:isPlayedBy/rdfs:label ?cardIssuer ;
            pfm:cardSchemeOperator/pfm:isPlayedBy/rdfs:label ?cardSchemeOperator ;
            pfm:linkedAccount/pfm:accountNumber ?linkedAccountNumber .
        }
    - question: Show me the transactions of the payment card number "4731042107549834" from 2024-07-01 to 2025-07-01
      sparql: |
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        PREFIX pfm: <https://static.rwpz.net/spendcast/schema#> 
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> 
        SELECT ?transactionId ?transactionDate ?transactionType ?transactionStatus ?amount ?currency ?recieptId WHERE { 
            ?card pfm:cardNumber "4731042107549834" .
            ?transaction a pfm:FinancialTransaction ;
            rdfs:label ?transactionId ;
            pfm:hasCard ?card ;
            pfm:hasMonetaryAmount ?monetaryAmount ;
            pfm:hasTransactionDate ?transactionDate ;
            pfm:transactionType ?transactionType ;
            pfm:status ?transactionStatus .
            OPTIONAL { ?transaction pfm:hasReceipt/rdfs:label ?recieptId }.

            ?monetaryAmount pfm:hasCurrency ?currency .
            ?monetaryAmount pfm:hasAmount ?amount .
            
            FILTER(strstarts(?transactionStatus, "settled"))
            FILTER (?transactionDate >= "2024-07-01"^^xsd:date)
            FILTER (?transactionDate < "2025-07-01"^^xsd:date)
        }

    - question: Show me all merchants that received a payment between 2024-10-01 and 2024-10-31
      sparql: |
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        PREFIX pfm: <https://static.rwpz.net/spendcast/schema#>
        SELECT DISTINCT ?payee WHERE {
            ?transaction a pfm:FinancialTransaction ;
            pfm:hasTransactionDate ?transactionDate ;
            pfm:transactionType ?transactionType ;    
            pfm:hasParticipant [
                a pfm:Payee ;
                pfm:isPlayedBy/rdfs:label ?payee 
            ] .

            FILTER(strstarts(?transactionType, "expense"))
            FILTER (?transactionDate >= "2024-10-01"^^xsd:date)
            FILTER (?transactionDate < "2024-10-31"^^xsd:date)
        }  

    - question: Show me the receipt with the id="Receipt 20250627_184626_0033091_251_260"
      sparql: |
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX pfm: <https://static.rwpz.net/spendcast/schema#>
        SELECT ?receiptId ?receiptDate ?totalAmount ?currency ?cardNumber 
        WHERE {
        ?receipt a pfm:Receipt ;
            rdfs:label "Receipt 20250627_184626_0033091_251_260" ;
            pfm:hasCard/pfm:cardNumber ?cardNumber ;
            pfm:receiptDate ?receiptDate ;
            pfm:receiptId ?receiptId ;
            pfm:hasTotalAmount [a pfm:MonetaryAmount ; pfm:hasAmount ?totalAmount; pfm:hasCurrency ?currency] .
        }
    - question: Show me the line items of the receipt with the id="Receipt 20250627_184626_0033091_251_260"
      sparql: |
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX pfm: <https://static.rwpz.net/spendcast/schema#>
        SELECT ?description ?quantity ?unitPrice ?lineSubtotal ?productUrls
        WHERE {
            #?account a pfm:Account ;
            #pfm:hasAccountPurpose ?accountPurpose ;
            ?receipt a pfm:Receipt ;
                    rdfs:label "Receipt 20250627_184626_0033091_251_260";
        pfm:hasLineItem	?lineItem .
        ?lineItem pfm:itemDescription ?description ;
            pfm:quantity ?quantity ;
            pfm:unitPrice ?unitPrice ;
                pfm:lineSubtotal ?lineSubtotal ;
            pfm:hasProduct [a pfm:Product ; 
            pfm:productUrls ?productUrls ;
                pfm:category [a pfm:ProductCategory ; rdfs:label ?category ]] .
        }
    ```
  """

  return await _execute_sparql_impl(ctx, query)


# @mcp.tool()
# def get_schema_help() -> Dict[str, Any]:
#     """
#     Get schema documentation and query examples for the financial data store.
    
#     This tool provides immediate access to schema information and working examples
#     to help you write SPARQL queries. No need to access separate resources.
    
#     :return: Dictionary containing schema content and examples
#     """
#     return {
#         "schema_summary": get_schema_summary.fn(),
#         "example_queries": get_example_queries.fn(),
#         "ontology": get_ontology_content.fn(),
#         "description": "Complete schema information and examples for writing SPARQL queries",
#         "quick_tips": [
#             "Use exs: prefix for schema properties (e.g., exs:hasAccount)",
#             "Use ex: prefix for data instances (e.g., ex:Swiss_franc)",
#             "Transactions use accounts, not cards directly",
#             "Check the schema_summary for entity relationships",
#             "See example_queries for working SPARQL patterns",
#             "Do not use escaped line breaks in the query: \\n"
#         ]
#     }

# #    "note": "All content is included directly - no need to access separate resources",
# #        "ontology_source": "Local files with online fallback at https://static.rwpz.net/spendcast/schema#"

# @mcp.tool()
# def get_schema_content(resource_name: str = "schema_summary") -> Dict[str, Any]:
#     """
#     Get the actual content of schema resources instead of just the URIs.
    
#     This tool reads and returns the content of schema resources, making it easier
#     to access schema information without having to use MCP resource reading.
    
#     :param resource_name: Which resource to read. Options: "schema_summary", "example_queries", "ontology"
#     :return: Dictionary containing the resource content and metadata
#     """
#     resource_map = {
#         "schema_summary": ("internal://schema_summary.md", get_schema_summary.fn),
#         "example_queries": ("internal://example_queries.md", get_example_queries.fn),
#         "ontology": ("https://static.rwpz.net/spendcast/schema#", get_ontology_content.fn)
#     }

#     if resource_name not in resource_map:
#         return {
#             "error": f"Unknown resource: {resource_name}",
#             "available_resources": list(resource_map.keys()),
#             "suggestion": "Use one of the available resource names"
#         }

#     uri, resource_func = resource_map[resource_name]

#     try:
#         content = resource_func()
#         return {
#             "resource_name": resource_name,
#             "uri": uri,
#             "content": content,
#             "content_length": len(content),
#             "note": "This is the actual content, not just a URI reference"
#         }
#     except Exception as e:
#         return {
#             "error": f"Failed to read resource {resource_name}: {str(e)}",
#             "resource_name": resource_name,
#             "uri": uri
#         }


    # """
    # Execute SPARQL queries against a financial data triple store containing comprehensive banking, transaction, and retail data. The store includes:\n\n

    # **IMPORTANT: Before writing queries, use these tools for schema help:**
    # - `get_schema_help()` - Complete schema information and examples (recommended)
    # - `get_schema_content('schema_summary')` - Read entity relationships and schema patterns
    # - `get_schema_content('example_queries')` - Read working SPARQL examples

    # **Core Financial Entities:**\n
    # - **Accounts**: Checking, savings, credit cards, retirement accounts (3A pillar)\n
    # - **Parties**: People (customers) and organizations (banks, merchants) with detailed contact information\n
    # - **Payment Cards**: Credit/debit cards linked to accounts for transactions\n
    # - **Financial Transactions**: Complete transaction records with amounts, dates, status, and types\n\n
    # **Retail & Receipt Data:**\n
    # - **Receipts**: Detailed purchase receipts with line items, dates, and payment methods\n
    # - **Products**: Migros product catalog with EAN codes, names, and category links\n
    # - **Product Categories**: Hierarchical classification (beverages, bread, cleaning, etc.)\n
    # - **Merchants**: Business entities with names and addresses\n\n
    # **Key Data Properties:**\n
    # - Transaction amounts in CHF with currency information\n
    # - Complete transaction dates and status tracking\n
    # - Account balances and payment card details\n
    # - Product information and receipt line items\n
    # - Customer account and card relationships\n\n
    # **Query Capabilities:**\n
    # - Find transactions by customer, date, amount, or merchant\n
    # - Analyze spending patterns through accounts and payment cards\n
    # - Track account balances and payment card usage\n
    # - Search products and receipt details\n
    # - Analyze customer financial relationships\n\n
    # **Important Data Structure Insights:**\n
    # - **Customers** are `exs:Person` entities with direct `exs:hasAccount` relationships\n
    # - **Payment Cards** are linked to accounts via `exs:linkedAccount`\n
    # - **Transactions** use accounts (not cards directly) through `exs:hasParticipant` + `exs:Payer` role + `exs:isPlayedBy`\n
    # - **Product Categories** now work correctly with proper `exs:category` relationships and hierarchical structure\n
    # - **Party Roles** (Payer, Payee, AccountHolder, CardHolder) mediate relationships between entities\n\n
    # **Common Query Patterns:**\n
    # - Use `exs:` prefix for schema properties (e.g., `exs:hasMonetaryAmount`)\n
    # - Use `ex:` prefix for data instances (e.g., `ex:Swiss_franc`)\n
    # - Find customer transactions through accounts: `?person exs:hasAccount ?account`\n
    # - Find card transactions through linked accounts: `?card exs:linkedAccount ?account`\n
    # - Join transactions with receipts using `exs:hasReceipt`
    
    # **💡 Pro Tip:** Use `get_schema_help()` to get complete schema information and examples before writing queries!\n\n
    # **Example Queries:**\n
    # - Find all transactions for a specific customer\n
    # - Find transactions through bank accounts only\n
    # - Find transactions through payment cards only\n
    # - Get customer account summary\n
    # - Monthly spending by category\n
    # - Top spending merchants\n
    # - Payment card usage patterns\n

    # :param ctx: The tool context (unused in this implementation).
    # :param query: The SPARQL query string to execute.
    # :return: The JSON result from GraphDB or an error dictionary.
    # """


# --- Resource Tools ---
# Resources will be added after the functions are defined

# @mcp.resource(
#     "internal://schema_summary.md",
#     name="schema_summary",
#     description="Human-readable summary of key triple store entities and relationships",
#     mime_type="text/markdown",
# )
# def get_schema_summary() -> str:
#     """Generate a human-readable schema summary."""
#     return """# Triple Store Schema Summary

# ## Core Entity Classes

# ### Financial Entities
# - **Account** - Banking accounts (checking, savings, credit cards, retirement 3A)
# - **Person** - Individual customers with accounts and payment cards
# - **Organization** - Banks, merchants, and other business entities
# - **PaymentCard** - Credit/debit cards linked to accounts for transactions
# - **FinancialTransaction** - Money transfers with amounts, dates, and status
# - **MonetaryAmount** - Currency amounts (primarily CHF)
# - **PartyRole** - Mediator entities (Payer, Payee, AccountHolder, CardHolder)

# ### Retail Entities  
# - **Receipt** - Purchase documents with line items and totals
# - **ReceiptLineItem** - Individual items on receipts with products and amounts
# - **Product** - Goods and services with names, descriptions, and category links
# - **ProductCategory** - Hierarchical product classification (beverages, bread, cleaning, etc.)
# - **Merchant** - Business entities with names and addresses
# - **Currency** - Medium of exchange (CHF, EUR, USD)
# - **CurrencyConversion** - Currency exchange operations

# ## Key Properties

# ### Person Properties
# - `exs:hasName` - Customer's full name
# - `exs:hasAccount` - Direct link to customer's accounts
# - `exs:hasPaymentCard` - Direct link to customer's payment cards
# - `exs:hasEmailAddress` - Customer's email
# - `exs:hasTelephoneNumber` - Customer's phone number

# ### Organization Properties
# - `exs:hasName` - Organization name
# - `exs:hasAddress` - Organization address
# - `exs:hasEmailAddress` - Organization email
# - `exs:hasTelephoneNumber` - Organization phone number

# ### Account Properties
# - `exs:hasAccountHolder` - Links account to customer through role
# - `exs:hasAccountProvider` - Links account to bank through role
# - `exs:hasInitialBalance` - Starting balance
# - `exs:hasCurrency` - Account currency (primarily CHF)
# - `exs:accountNumber` - Account number identifier
# - `exs:hasInternationalBankAccountIdentifier` - IBAN number
# - `exs:hasAccountPurpose` - Purpose of the account
# - `exs:overdraftLimit` - Overdraft limit

# ### Payment Card Properties
# - `exs:hasCardHolder` - Links card to customer through role
# - `exs:linkedAccount` - Links card to the account it uses for transactions
# - `exs:hasCardIssuer` - Links card to issuing bank through role
# - `exs:cardSchemeOperator` - Links card to scheme operator (Visa, Mastercard, etc.)

# ### Transaction Properties
# - `exs:hasMonetaryAmount` - Transaction amount
# - `exs:hasTransactionDate` - When transaction occurred
# - `exs:hasParticipant` - Who was involved (through PartyRole)
# - `exs:status` - settled/pending/rejected/cancelled
# - `exs:transactionType` - expense/income/transfer
# - `exs:hasReceipt` - Links to purchase receipt (if applicable)
# - `exs:hasCard` - Links transaction to payment card
# - `exs:hasCurrencyConversion` - Links to currency conversion details
# - `exs:valueDate` - Value date for the transaction

# ### Product Properties
# - `exs:category` - Product classification (links to ProductCategory instances)
# - `exs:name` - Product name
# - `exs:description` - Product description
# - `exs:migrosId` - Migros product identifier
# - `exs:unitPrice` - Price per unit
# - `exs:legalDesignation` - Legal designation for the product
# - `exs:origin` - Product origin information
# - `exs:imageTransparentUrl` - Product image URL
# - `exs:migrosOnlineId` - Online store identifier
# - `exs:productUrls` - Product page URLs

# ### Receipt Line Item Properties
# - `exs:hasProduct` - Links to product (both name and GTIN)
# - `exs:lineSubtotal` - Amount for this line item
# - `exs:quantity` - Number of units purchased
# - `exs:unitPrice` - Price per unit
# - `exs:itemDescription` - Description of the line item

# ### Merchant Properties
# - `exs:hasName` - Business name
# - `exs:hasAddress` - Business location
# - `exs:merchantCategory` - Merchant category classification (SKOS concept)

# ### ProductCategory Properties
# - `rdfs:label` - Category name/label
# - `exs:hasParentCategory` - Links to parent category (hierarchical structure)
# - `exs:co2Factor` - CO2 impact factor (optional)
# - `exs:taxClass` - Tax classification (optional)
# - `exs:description` - Category description (optional)

# ### Receipt Properties
# - `exs:hasLineItem` - Links to individual items
# - `exs:hasTotalAmount` - Total receipt amount
# - `exs:receiptDate` - Date of purchase
# - `exs:receiptTime` - Time of purchase
# - `exs:paymentMethod` - How payment was made
# - `exs:vatNumber` - VAT number on receipt
# - `exs:authorizationCode` - Transaction authorization code
# - `exs:entryMode` - How card was used (chip, contactless, etc.)
# - `exs:receiptId` - Receipt identifier

# ## Common Query Patterns

# ### Find Customer Transactions
# ```sparql
# PREFIX exs: <https://static.rwpz.net/spendcast/schema#>
# PREFIX ex: <https://static.rwpz.net/spendcast/>

# SELECT ?transaction ?amount ?date ?merchant ?payer_type WHERE {
#   # Find the customer
#   ?person exs:hasName "Jeanine Marie Blumenthal" .
  
#   # Get their accounts
#   ?person exs:hasAccount ?account .
#   ?account a ?payer_type .
  
#   # Find transactions where the account is a payer
#   ?transaction a exs:FinancialTransaction .
#   ?transaction exs:hasParticipant ?payerRole .
#   ?payerRole a exs:Payer .
#   ?payerRole exs:isPlayedBy ?account .
  
#   # Get transaction details
#   ?transaction exs:hasMonetaryAmount ?amount_uri .
#   ?amount_uri exs:hasAmount ?amount .
#   ?transaction exs:hasTransactionDate ?date .
  
#   # Get merchant information (payee)
#   ?transaction exs:hasParticipant ?payeeRole .
#   ?payeeRole a exs:Payee .
#   ?payeeRole exs:isPlayedBy ?merchant .
#   ?merchant rdfs:label ?merchant_label .
# }
# ```

# ### Find Transactions Through Payment Cards
# ```sparql
# PREFIX exs: <https://static.rwpz.net/spendcast/schema#>
# PREFIX ex: <https://static.rwpz.net/spendcast/>

# SELECT ?transaction ?amount ?date ?card_type ?linked_account WHERE {
#   ?person exs:hasName "Jeanine Marie Blumenthal" .
#   ?card exs:hasCardHolder ?cardHolderRole .
#   ?cardHolderRole exs:isPlayedBy ?person .
#   ?card a ?card_type .
#   ?card exs:linkedAccount ?linked_account .
  
#   # Find transactions where the linked account is a payer
#   ?transaction a exs:FinancialTransaction .
#   ?transaction exs:hasParticipant ?payerRole .
#   ?payerRole a exs:Payer .
#   ?payerRole exs:isPlayedBy ?linked_account .
  
#   ?transaction exs:hasMonetaryAmount ?amount_uri .
#   ?amount_uri exs:hasAmount ?amount .
#   ?transaction exs:hasTransactionDate ?date .
# }
# ```

# ### Get Customer Account Summary
# ```sparql
# PREFIX exs: <https://static.rwpz.net/spendcast/schema#>
# PREFIX ex: <https://static.rwpz.net/spendcast/>

# SELECT ?account ?type ?balance ?currency WHERE {
#   ?account a ?account_type .
#   ?account exs:hasAccountHolder ?holder_role .
#   ?holder_role exs:isPlayedBy ?person .
#   ?person exs:hasName "Jeanine Marie Blumenthal" .
#   ?account exs:hasInitialBalance ?balance .
#   ?account exs:hasCurrency ?currency .
#   VALUES ?account_type { exs:CheckingAccount exs:SavingsAccount exs:CreditCard exs:Retirement3A }
# }
# ```

# **Key Insights**: 
# - **Direct relationships**: `?person exs:hasAccount ?account` and `?person exs:hasPaymentCard ?card`
# - **Role-based relationships**: `?account exs:hasAccountHolder ?role` → `?role exs:isPlayedBy ?person`
# - **Card-account linking**: `?card exs:linkedAccount ?account` (cards use accounts for transactions)
# - **Transaction participation**: Through `exs:hasParticipant` + `exs:Payer` role + `exs:isPlayedBy`
# """


# @mcp.resource(
#     "internal://example_queries.md",
#     name="example_queries",
#     description="Common SPARQL query patterns and examples for the financial data store",
#     mime_type="text/markdown",
# )

# def get_example_queries() -> str:
#     """Generate example SPARQL queries."""
#     return """# Example SPARQL Queries for Financial Data Store

# ## Important Note on Customer-Transaction Relationships

# **Customers (Persons) have both direct and role-based relationships:**

# 1. **Direct relationships**: `?person exs:hasAccount ?account` and `?person exs:hasPaymentCard ?card`
# 2. **Role-based relationships**: 
#    - `?account exs:hasAccountHolder ?holderRole` → `?holderRole exs:isPlayedBy ?person`
#    - `?card exs:hasCardHolder ?cardHolderRole` → `?cardHolderRole exs:isPlayedBy ?person`

# **Transactions have participants through Party Roles:**
# - `?transaction exs:hasParticipant ?payerRole` → `?payerRole exs:isPlayedBy ?payer`
# - `?transaction exs:hasParticipant ?payeeRole` → `?payeeRole exs:isPlayedBy ?payee`

# **Key Party Role Types:**
# - `exs:Payer` - The party paying money
# - `exs:Payee` - The party receiving money  
# - `exs:AccountHolder` - The party owning an account
# - `exs:CardHolder` - The party holding a payment card
# - `exs:AccountProvider` - The bank providing an account
# - `exs:CardIssuer` - The bank issuing a payment card

# **Important**: Payment cards are linked to accounts via `exs:linkedAccount`, and transactions use the linked account (not the card directly).

# ## Customer Analysis

# ### 1. Find All Transactions for a Specific Customer 
# ```sparql
# PREFIX exs: <https://static.rwpz.net/spendcast/schema#>
# PREFIX ex: <https://static.rwpz.net/spendcast/>

# SELECT ?transaction ?amount ?date ?merchant ?payer_type WHERE {
#   # Find the customer
#   ?customer exs:hasName "Jeanine Marie Blumenthal" .
  
#   # Option 1: Through bank accounts (customer is payer)
#   {
#     ?customer exs:hasAccount ?account .
#     ?account a ?payer_type .
#     ?transaction a exs:FinancialTransaction ;
#       exs:hasParticipant ?payerRole .
#     ?payerRole a exs:Payer ;
#       exs:isPlayedBy ?account .
#   }
#   UNION
#   # Option 2: Through payment cards (customer is payer)
#   {
#     ?customer exs:hasPaymentCard ?card .
#     ?card a ?payer_type .
#     ?transaction a exs:FinancialTransaction ;
#       exs:hasParticipant ?payerRole .
#     ?payerRole a exs:Payer ;
#       exs:isPlayedBy ?card .
#   }
  
#   # Get transaction details
#   ?transaction exs:hasMonetaryAmount ?amount_uri .
#   ?amount_uri exs:hasAmount ?amount ;
#     exs:hasTransactionDate ?date .
  
#   # Get merchant information (merchant is payee)
#   ?transaction exs:hasParticipant ?payeeRole .
#   ?payeeRole a exs:Payee ;
#     exs:isPlayedBy ?merchant .
#   ?merchant rdfs:label ?merchant .
# }
# ORDER BY DESC(?date)
# ```

# ### 1a. Find Transactions Through Bank Accounts Only 
# ```sparql
# PREFIX exs: <https://static.rwpz.net/spendcast/schema#>
# PREFIX ex: <https://static.rwpz.net/spendcast/>

# SELECT ?transaction ?amount ?date ?account_type WHERE {
#   ?customer exs:hasName "Jeanine Marie Blumenthal" .
#   ?account exs:hasAccountHolder ?holderRole .
#   ?holderRole exs:isPlayedBy ?customer .
#   ?account a ?account_type .
#   ?transaction a exs:FinancialTransaction ;
#     exs:hasParticipant ?payerRole .
#   ?payerRole a exs:Payer ;
#     exs:isPlayedBy ?account .
#   ?transaction exs:hasMonetaryAmount ?amount_uri .
#   ?amount_uri exs:hasAmount ?amount ;
#     exs:hasTransactionDate ?date .
# }
# ORDER BY DESC(?date)
# ```

# ### 1b. Find Transactions Through Payment Cards Only 
# ```sparql
# PREFIX exs: <https://static.rwpz.net/spendcast/schema#>
# PREFIX ex: <https://static.rwpz.net/spendcast/>

# SELECT ?transaction ?amount ?date ?card_type WHERE {
#   ?customer exs:hasName "Jeanine Marie Blumenthal" .
#   ?card exs:hasCardHolder ?cardHolderRole .
#   ?cardHolderRole exs:isPlayedBy ?customer .
#   ?card a ?card_type .
#   ?transaction a exs:FinancialTransaction ;
#     exs:hasParticipant ?payerRole .
#   ?payerRole a exs:Payer ;
#     exs:isPlayedBy ?card .
#   ?transaction exs:hasMonetaryAmount ?amount_uri .
#   ?amount_uri exs:hasAmount ?amount ;
#     exs:hasTransactionDate ?date .
# }
# ORDER BY DESC(?date)
# ```

# ### 2. Customer Account Summary
# ```sparql
# PREFIX exs: <https://static.rwpz.net/spendcast/schema#>
# PREFIX ex: <https://static.rwpz.net/spendcast/>

# SELECT ?account ?type ?balance ?currency WHERE {
#   ?account a ?account_type ;
#     exs:hasAccountHolder ?holder_role .
#   ?holder_role exs:isPlayedBy ?customer .
#   ?customer exs:hasName "Jeanine Marie Blumenthal" .
#   ?account exs:hasInitialBalance ?balance ;
#     exs:hasCurrency ?currency .
#   VALUES ?account_type { exs:CheckingAccount exs:SavingsAccount exs:CreditCard exs:Retirement3A }
# }
# ```

# ## Spending Analysis

# ### 3. Monthly Spending by Category 
# ```sparql
# PREFIX exs: <https://static.rwpz.net/spendcast/schema#>
# PREFIX ex: <https://static.rwpz.net/spendcast/>

# SELECT ?month ?category ?category_label (SUM(?amount) AS ?total_spent) WHERE {
#   ?transaction a exs:FinancialTransaction ;
#     exs:hasTransactionDate ?date ;
#     exs:hasReceipt ?receipt .
#   ?receipt exs:hasLineItem ?line_item .
#   ?line_item exs:hasProduct ?product .
#   ?product exs:hasCategory ?category .
#   ?category rdfs:label ?category_label .
#   ?transaction exs:hasMonetaryAmount ?amount_uri .
#   ?amount_uri exs:hasAmount ?amount .
#   BIND(STRDT(CONCAT(YEAR(?date), "-", STR(MONTH(?date)), "-01"), xsd:date) AS ?month)
#   FILTER(?date >= "2025-01-01"^^xsd:date && ?date <= "2025-12-31"^^xsd:date)
# }
# GROUP BY ?month ?category ?category_label
# ORDER BY ?month DESC(?total_spent)
# ```

# **Note**: This example is now working! The product categories have been fixed and return real spending data by category and month.

# ### 4. Top Spending Merchants 
# ```sparql
# PREFIX exs: <https://static.rwpz.net/spendcast/schema#>
# PREFIX ex: <https://static.rwpz.net/spendcast/>

# SELECT ?merchant (SUM(?amount) AS ?total_spent) (COUNT(?transaction) AS ?transaction_count) WHERE {
#   ?transaction a exs:FinancialTransaction ;
#     exs:hasParticipant ?payeeRole .
#   ?payeeRole a exs:Payee ;
#     exs:isPlayedBy ?merchant .
#   ?merchant rdfs:label ?merchant .
#   ?transaction exs:hasMonetaryAmount ?amount_uri .
#   ?amount_uri exs:hasAmount ?amount .
#   FILTER(?transaction exs:transactionType "expense")
# }
# GROUP BY ?merchant
# ORDER BY DESC(?total_spent)
# LIMIT 20
# ```

# ### 5. Payment Card Usage Patterns

# ```sparql
# PREFIX exs: <https://static.rwpz.net/spendcast/schema#>
# PREFIX ex: <https://static.rwpz.net/spendcast/>

# SELECT ?card ?card_type ?total_spent ?transaction_count WHERE {
#   ?transaction a exs:FinancialTransaction ;
#     exs:hasCard ?card .
#   ?card exs:cardType ?card_type ;
#     exs:cardNumber ?card_number .
#   ?transaction exs:hasMonetaryAmount ?amount_uri .
#   ?amount_uri exs:hasAmount ?amount .
#   FILTER(?transaction exs:transactionType "expense")
# }
# GROUP BY ?card ?card_type ?card_number
# ORDER BY DESC(?total_spent)
# ```

# ### 6. Currency Conversion Analysis
# ```sparql
# PREFIX exs: <https://static.rwpz.net/spendcast/schema#>
# PREFIX ex: <https://static.rwpz.net/spendcast/>

# SELECT ?transaction ?base_currency ?counter_currency ?exchange_rate ?date WHERE {
#   ?transaction a exs:FinancialTransaction ;
#     exs:hasCurrencyConversion ?conversion .
#   ?conversion exs:hasBaseAmount ?base_amount ;
#     exs:hasCounterAmount ?counter_amount ;
#     exs:exchangeRate ?exchange_rate ;
#     exs:conversionDate ?date .
#   ?base_amount exs:hasCurrency ?base_currency .
#   ?counter_amount exs:hasCurrency ?counter_currency .
# }
# ORDER BY DESC(?date)
# ```
# ## Tips for Writing Queries

# """


# @mcp.resource(
#     "https://static.rwpz.net/spendcast/schema#",
#     name="triple_store_schema",
#     description="Complete ontology and schema for the financial data triple store",
#     mime_type="text/turtle",
# )
# def get_ontology_content() -> str:
#     """Read the ontology.ttl file content with online fallback."""
#     try:
#         # Try data/ontology.ttl first (for development)
#         ontology_path = os.path.join(
#             os.path.dirname(__file__), "..", "..", "data", "ontology.ttl"
#         )
#         if not os.path.exists(ontology_path):
#             # Fall back to deploy/ontology.ttl (for production)
#             ontology_path = os.path.join(
#                 os.path.dirname(__file__), "..", "..", "deploy", "ontology.ttl"
#             )

#         with open(ontology_path, "r", encoding="utf-8") as f:
#             return f.read()
#     except FileNotFoundError:
#         # Fallback to online ontology
#         try:

#             # Create a simple async function to fetch the online ontology
#             async def fetch_online_ontology():
#                 async with httpx.AsyncClient() as client:
#                     response = await client.get("https://static.rwpz.net/spendcast/schema#", timeout=10.0)
#                     response.raise_for_status()
#                     return response.text

#             # Run the async function in a new event loop if needed
#             try:
#                 loop = asyncio.get_event_loop()
#                 if loop.is_running():
#                     # If we're already in an async context, we can't use run_until_complete
#                     return "# Ontology file not found locally. Online ontology available at: https://static.rwpz.net/spendcast/schema#"
#                 else:
#                     return loop.run_until_complete(fetch_online_ontology())
#             except RuntimeError:
#                 # No event loop available, return the URL
#                 return "# Ontology file not found locally. Online ontology available at: https://static.rwpz.net/spendcast/schema#"

#         except Exception as fetch_error:
#             return f"# Ontology file not found locally. Online ontology available at: https://static.rwpz.net/spendcast/schema#\n# Error fetching online version: {str(fetch_error)}"
#     except Exception as e:
#         return f"# Error reading ontology file: {str(e)}\n# Online ontology available at: https://static.rwpz.net/spendcast/schema#"


# # ---- Query Validation ---
# def validate_sparql_query(query: str) -> tuple[bool, str]:
#     """
#     Basic SPARQL query validation.

#     :param query: The SPARQL query string to validate
#     :return: Tuple of (is_valid, error_message)
#     """
#     # Check for required prefixes
#     required_prefixes = ["exs:", "ex:"]
#     missing_prefixes = []

#     for prefix in required_prefixes:
#         if prefix not in query:
#             missing_prefixes.append(prefix)

#     if missing_prefixes:
#         return False, f"Missing required prefixes: {', '.join(missing_prefixes)}"

#     # Check for basic SPARQL syntax
#     if not query.strip().upper().startswith(("SELECT", "ASK", "CONSTRUCT", "DESCRIBE")):
#         return False, "Query must start with SELECT, ASK, CONSTRUCT, or DESCRIBE"

#     # Check for balanced braces
#     if query.count("{") != query.count("}"):
#         return False, "Unbalanced braces in SPARQL query"

#     # Check for basic WHERE clause
#     if "{" not in query or "}" not in query:
#         return False, "Missing WHERE clause with braces"

#     return True, "Query is valid"


# --- Enhanced SPARQL Tool with Validation ---
# @mcp.tool()
# async def execute_sparql_validated(ctx: Context, query: str) -> Dict[str, Any]:
#     """
#     Execute SPARQL queries with validation against a financial data triple store.

#     This tool provides the same functionality as execute_sparql but includes
#     basic query validation to catch common syntax errors before sending to GraphDB.

#     :param ctx: The tool context (unused in this implementation).
#     :param query: The SPARQL query string to execute.
#     :return: The JSON result from GraphDB or an error dictionary.
#     """
#     # Validate the query first
#     is_valid, error_message = validate_sparql_query(query)
#     if not is_valid:
#         return {
#             "error": f"SPARQL validation failed: {error_message}",
#             "query": query,
#             "validation_tips": [
#                 "Ensure your query starts with SELECT, ASK, CONSTRUCT, or DESCRIBE",
#                 "Include both exs: and ex: prefixes",
#                 "Check that all braces { } are properly balanced",
#                 "Verify your WHERE clause syntax",
#             ],
#         }

#     # If validation passes, execute the query
#     return await _execute_sparql_impl(ctx, query)


# --- Resource Registration ---
# Resources are now registered using decorators above


if __name__ == "__main__":
    load_dotenv()  # Load environment variables from .env file
    get_config()  # Validate config on startup
    mcp.run()
