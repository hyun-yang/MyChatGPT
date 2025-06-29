import json
from contextlib import AsyncExitStack
from typing import List, Dict, TypedDict

from PyQt6.QtCore import QObject
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class ToolDefinition(TypedDict):
    name: str
    description: str
    input_schema: dict


class MCPServerCheck(QObject):

    def __init__(self, config_path="server_config.json"):
        super().__init__()
        self.config_path = config_path
        self.exit_stack = None
        self.sessions: List[ClientSession] = []
        self.available_tools: List[ToolDefinition] = []
        self.tool_to_session: Dict[str, ClientSession] = {}
        self.is_initialized = False
        self.cleanup_done = False

    async def initialize(self):
        if self.is_initialized:
            return True

        try:
            self.exit_stack = AsyncExitStack()

            with open(self.config_path, "r") as file:
                data = json.load(file)

            servers = data.get("mcpServers", {})

            for server_name, server_config in servers.items():
                await self.connect_to_server(server_name, server_config)

            self.is_initialized = True
            return True
        except Exception as e:
            return False

    async def connect_to_server(self, server_name: str, server_config: dict) -> None:
        try:
            required_fields = ["command", "args"]
            for field in required_fields:
                if field not in server_config:
                    raise ValueError(f"Missing required field '{field}' in server config")

            server_params = StdioServerParameters(
                command=server_config["command"],
                args=server_config["args"],
                cwd=server_config.get("cwd"),
                env=server_config.get("env")
            )

            print(f"Connecting to {server_name} with params: {server_params}")
            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            read, write = stdio_transport
            session = await self.exit_stack.enter_async_context(
                ClientSession(read, write)
            )

            await session.initialize()
            self.sessions.append(session)

            response = await session.list_tools()
            tools = response.tools
            print(f"Connected to {server_name} with tools:", [t.name for t in tools])

            for tool in tools:
                tool_schema = tool.inputSchema if hasattr(tool, 'inputSchema') else tool.input_schema
                self.tool_to_session[tool.name] = session
                self.available_tools.append({
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool_schema
                })
        except Exception as e:
            print(f"Failed to connect to {server_name}: {e}")

    async def cleanup(self):
        if self.exit_stack and not self.cleanup_done:
            print("Cleaning up MCP resources...")
            await self.exit_stack.aclose()
            self.cleanup_done = True
            self.is_initialized = False
            print("MCP cleanup completed")

    def get_available_tools(self):
        return self.available_tools.copy() if self.is_initialized else []

    async def execute_tool(self, tool_name: str, params: dict):
        if not self.is_initialized:
            raise RuntimeError("MCP Service not initialized")

        session = self.tool_to_session.get(tool_name)
        if not session:
            raise ValueError(f"Tool '{tool_name}' not found")

        result = await session.execute_tool(tool_name, params)
        return result
