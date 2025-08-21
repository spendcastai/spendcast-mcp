import asyncio
import json

from dotenv import load_dotenv
from fastmcp.client import Client

from src.spendcast_mcp.server import mcp


async def main():
    """Connects to the MCP server and executes a SPARQL query."""

    print("MCP Client connected.")

    # The SPARQL query from the project plan
    query = "SELECT ?s ?p ?o WHERE {?s ?p ?o} LIMIT 10"

    print(f"Executing tool 'execute_sparql' with query:\n{query}\n")

    try:
        async with Client(mcp) as client:
            print("--- Server Response ---")
            result = await client.call_tool("execute_sparql", {"query": query})

            print("--- Server Response ---")
            print(json.dumps(result.data, indent=2))
            print("-----------------------")

            if result and "error" not in result.data:
                print("\n✅ Test successful: Received a valid response from the server.")
            else:
                print(f"\n❌ Test failed: Server returned an error: {result.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"\n❌ An error occurred while executing the tool: {e}")
    finally:
        print("\nMCP Client disconnected.")


if __name__ == "__main__":
    load_dotenv()
    asyncio.run(main())
