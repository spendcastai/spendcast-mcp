#!/usr/bin/env python3
"""
Simple MCP server for testing
"""
from fastmcp import FastMCP, Context

# Create a simple server
server = FastMCP(instructions="Simple test server")

@server.tool()
async def hello(ctx: Context, name: str = "World") -> str:
    """Say hello to someone."""
    return f"Hello, {name}!"

@server.resource("test://hello")
def get_hello() -> str:
    """Get a hello message."""
    return "Hello from the test resource!"

if __name__ == "__main__":
    server.run(transport="stdio")



