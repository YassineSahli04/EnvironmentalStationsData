import json
import asyncio
import os
from pathlib import Path
from langchain_mcp_adapters.client import MultiServerMCPClient

_MCP_CLIENT = None


async def load_mcp_tools(config_path: str | Path):
    global _MCP_CLIENT
    cfg = json.loads(Path(config_path).read_text(encoding="utf-8"))

    _MCP_CLIENT = MultiServerMCPClient(cfg)
    tools = await _MCP_CLIENT.get_tools()
    return tools

ANTV_TOOLS = []
async def init_tool():
    global ANTV_TOOLS
    config_path = "mcp.servers.json"
    ANTV_TOOLS = await load_mcp_tools(config_path)

asyncio.run(init_tool())

