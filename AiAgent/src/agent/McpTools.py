import json
import asyncio
from pathlib import Path
from langchain_mcp_adapters.client import MultiServerMCPClient

_MCP_CLIENT = None
_INIT_LOCK = asyncio.Lock()
_IS_INITIALIZED = False


async def load_mcp_tools(config_path: str | Path):
    global _MCP_CLIENT
    cfg = json.loads(Path(config_path).read_text(encoding="utf-8"))

    _MCP_CLIENT = MultiServerMCPClient(cfg)
    tools = await _MCP_CLIENT.get_tools()
    return tools


MCP_TOOLS = []


async def init_tool(config_path: str | Path = "mcp.servers.json", force: bool = False):
    global _IS_INITIALIZED

    if _IS_INITIALIZED and not force:
        return MCP_TOOLS

    async with _INIT_LOCK:
        if _IS_INITIALIZED and not force:
            return MCP_TOOLS

        tools = await load_mcp_tools(config_path)
        MCP_TOOLS.clear()
        MCP_TOOLS.extend(tools)
        _IS_INITIALIZED = True
        return MCP_TOOLS
