import os
import json
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

DOMO_HOST = os.environ["DOMO_HOST"]
DOMO_DEVELOPER_TOKEN = os.environ["DOMO_DEVELOPER_TOKEN"]
BASE_URL = f"https://{DOMO_HOST}"

server = Server("domo-mcp")


def headers():
    return {
        "X-DOMO-Developer-Token": DOMO_DEVELOPER_TOKEN,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="list_datasets",
            description="List Domo datasets",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "default": 50},
                    "offset": {"type": "integer", "default": 0},
                    "name_filter": {"type": "string", "description": "Filter by name (partial match)"},
                },
            },
        ),
        types.Tool(
            name="get_dataset",
            description="Get metadata for a Domo dataset by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "dataset_id": {"type": "string"},
                },
                "required": ["dataset_id"],
            },
        ),
        types.Tool(
            name="query_dataset",
            description="Run a SQL query against a Domo dataset",
            inputSchema={
                "type": "object",
                "properties": {
                    "dataset_id": {"type": "string"},
                    "sql": {"type": "string", "description": "SQL query to execute"},
                },
                "required": ["dataset_id", "sql"],
            },
        ),
        types.Tool(
            name="get_dataset_data",
            description="Export raw CSV data from a Domo dataset",
            inputSchema={
                "type": "object",
                "properties": {
                    "dataset_id": {"type": "string"},
                    "include_header": {"type": "boolean", "default": True},
                },
                "required": ["dataset_id"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    async with httpx.AsyncClient() as client:
        if name == "list_datasets":
            limit = arguments.get("limit", 50)
            offset = arguments.get("offset", 0)
            name_filter = arguments.get("name_filter", "")
            params = {"limit": limit, "offset": offset}
            if name_filter:
                params["nameLike"] = name_filter
            r = await client.get(f"{BASE_URL}/v1/datasets", headers=headers(), params=params)
            r.raise_for_status()
            return [types.TextContent(type="text", text=json.dumps(r.json(), indent=2))]

        elif name == "get_dataset":
            dataset_id = arguments["dataset_id"]
            r = await client.get(f"{BASE_URL}/v1/datasets/{dataset_id}", headers=headers())
            r.raise_for_status()
            return [types.TextContent(type="text", text=json.dumps(r.json(), indent=2))]

        elif name == "query_dataset":
            dataset_id = arguments["dataset_id"]
            sql = arguments["sql"]
            r = await client.post(
                f"{BASE_URL}/v1/datasets/query/execute/{dataset_id}",
                headers=headers(),
                json={"sql": sql},
            )
            r.raise_for_status()
            return [types.TextContent(type="text", text=json.dumps(r.json(), indent=2))]

        elif name == "get_dataset_data":
            dataset_id = arguments["dataset_id"]
            include_header = arguments.get("include_header", True)
            h = {**headers(), "Accept": "text/csv"}
            r = await client.get(
                f"{BASE_URL}/v1/datasets/{dataset_id}/data",
                headers=h,
                params={"includeHeader": str(include_header).lower()},
            )
            r.raise_for_status()
            return [types.TextContent(type="text", text=r.text)]

        else:
            raise ValueError(f"Unknown tool: {name}")


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
