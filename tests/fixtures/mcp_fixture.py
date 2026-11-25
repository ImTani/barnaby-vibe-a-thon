"""A tiny stdio MCP server standing in for a Synapse-generated one (same FastMCP, same runtime python).

Its answers echo ENDPOINT_BASE_URL and the process id, so tests can see the config's env arrive and a
restart happen.
"""
import os

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("fixture")


@mcp.tool(name="read_thing", description="One thing.")
def read_thing(thing_id: int) -> dict:
    return {"thing": thing_id, "name": f"widget {thing_id}", "base_url": os.environ.get("ENDPOINT_BASE_URL", ""),
            "pid": os.getpid()}


@mcp.tool(name="place_order", description="Order an item.")
def place_order(item: str, quantity: int) -> dict:
    return {"ordered": item, "quantity": quantity}


@mcp.tool(name="drop_thing", description="Delete a thing.")
def drop_thing(thing_id: int) -> dict:
    return {"dropped": thing_id}


@mcp.tool(name="hand_back", description="Hand a job back to its owner.")
def hand_back(job_id: int) -> dict:
    return {"handed_back": job_id}


if __name__ == "__main__":
    mcp.run()
