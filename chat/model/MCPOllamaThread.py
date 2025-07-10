import asyncio
import json
import platform
import time
from contextlib import AsyncExitStack
from typing import List, TypedDict, Dict

import ollama
from PyQt6.QtCore import QThread, pyqtSignal
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from util.Constants import Constants


class ToolDefinition(TypedDict):
    name: str
    description: str
    input_schema: dict


class MCPOllamaThread(QThread):
    response_signal = pyqtSignal(str, bool)
    response_finished_signal = pyqtSignal(str, str, float, bool)

    def __init__(self, args):
        super().__init__()
        self.args = args
        self.ollama = ollama
        self.ai_arg = args['ai_arg']
        self.model = self.ai_arg['model']
        self.options = self.ai_arg['options']
        self.stream = self.ai_arg['stream']
        self.mcp_json = self.args['mcp_json']
        self.start_time = None
        self.force_stop = False

        # MCP attributes
        self.sessions: List[ClientSession] = []
        self.available_tools: List[ToolDefinition] = []
        self.tool_to_session: Dict[str, ClientSession] = {}

        self.exit_stack = AsyncExitStack()
        self.cleanup_requested = False
        self.loop = None

    def run(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        try:
            self.loop.run_until_complete(self._async_run())
        except Exception as e:
            self.finish_error(f"{Constants.ERROR_STOP}: {str(e)}")
        finally:
            self._cleanup_loop()

    async def _async_run(self):
        self.start_time = time.time()

        try:
            await self.connect_to_servers()
            if not self.cleanup_requested:
                await self.process_query(self.ai_arg)
        except asyncio.CancelledError:
            self.response_signal.emit("Operation cancelled by user.", self.stream)
            self.response_finished_signal.emit(self.model, Constants.ERROR_STOP, 0.0, self.stream)
        except Exception as e:
            self.response_signal.emit(str(e), self.stream)
        finally:
            await self._cleanup_resources()

    async def process_query(self, ai_arg) -> None:
        if self.cleanup_requested:
            return

        messages = ai_arg['messages']
        try:
            # Convert tools to Ollama format
            tools = []
            for tool in self.available_tools:
                tools.append({
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool["description"],
                        "parameters": tool["input_schema"]
                    }
                })

            final_text = ""
            processing = True

            while processing and not self.force_stop:
                # Prepare request data for Ollama
                request_data = {
                    "model": self.model,
                    "messages": messages,
                    "stream": False,
                    "options": self.options
                }

                # Add tools if available
                if tools:
                    request_data["tools"] = tools

                # Using run_in_executor to avoid blocking since ollama.chat is synchronous
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: self.ollama.chat(**request_data)
                )

                if not response:
                    self.finish_error("Failed to get response from Ollama")
                    return

                message = response.get('message', {})
                content = message.get('content', '')

                if content:
                    final_text += content
                    self.response_signal.emit(f"{final_text}\n", self.stream)

                # Check for tool calls
                tool_calls = message.get('tool_calls', [])
                if tool_calls:
                    for tool_call in tool_calls:
                        function = tool_call.get('function', {})
                        tool_name = function.get('name', '')
                        tool_args = function.get('arguments', {})

                        if isinstance(tool_args, str):
                            try:
                                tool_args = json.loads(tool_args)
                            except json.JSONDecodeError:
                                tool_args = {}

                        print(f"Calling tool {tool_name} with args {tool_args}")

                        # Special handling for sequentialthinking tool
                        if tool_name == "sequentialthinking" and 'thought' in tool_args:
                            thought_content = f"Calling tool {tool_name} with args {tool_args}"
                            self.response_signal.emit(f"{thought_content}\n", self.stream)

                        # Call the tool
                        if tool_name in self.tool_to_session:
                            session = self.tool_to_session[tool_name]
                            result = await session.call_tool(tool_name, arguments=tool_args)

                            # Emit result content conditionally
                            if tool_name != "sequentialthinking" or 'thought' not in tool_args:
                                self.response_signal.emit(f"{self.format_content(result.content)}\n", self.stream)

                            # Add tool result to messages
                            messages.append({
                                "role": "tool",
                                "content": json.dumps(self.serialize_content(result.content)),
                                "tool_call_id": tool_call.get('id', '')
                            })
                        else:
                            print(f"Tool {tool_name} not found in available tools")
                            messages.append({
                                "role": "tool",
                                "content": f"Error: Tool {tool_name} not available",
                                "tool_call_id": tool_call.get('id', '')
                            })
                else:
                    self.finish_run()
                    processing = False

        except Exception as e:
            self.finish_error(f"Error processing query: {e}")

    def serialize_content(self, content):
        if isinstance(content, (str, int, float, bool, type(None))):
            return content
        if isinstance(content, dict):
            return {k: self.serialize_content(v) for k, v in content.items()}
        if isinstance(content, list):
            return [self.serialize_content(item) for item in content]
        if hasattr(content, "dict"):
            return self.serialize_content(content.dict())
        if hasattr(content, "__dict__"):
            return self.serialize_content(vars(content))
        if hasattr(content, "text"):
            return str(content.text)
        return str(content)

    def format_content(self, content) -> str:
        if isinstance(content, str):
            return content
        elif isinstance(content, list):
            formatted_parts = []
            for item in content:
                if hasattr(item, 'text'):
                    formatted_parts.append(item.text)
                elif isinstance(item, dict):
                    formatted_parts.append(str(item))
                else:
                    formatted_parts.append(str(item))
            return '\n'.join(formatted_parts)
        elif hasattr(content, 'text'):
            return content.text
        else:
            return str(content)

    async def connect_to_server(self, server_name: str, server_config: dict):
        if self.cleanup_requested:
            return

        try:
            print(f"Connecting to {server_name}...")
            server_params = StdioServerParameters(**server_config)

            # Add timeout for server connection
            stdio_transport = await asyncio.wait_for(
                self.exit_stack.enter_async_context(stdio_client(server_params)),
                timeout=10.0
            )

            read, write = stdio_transport
            session = await asyncio.wait_for(
                self.exit_stack.enter_async_context(ClientSession(read, write)),
                timeout=10.0
            )

            await asyncio.wait_for(session.initialize(), timeout=10.0)
            self.sessions.append(session)

            response = await asyncio.wait_for(session.list_tools(), timeout=10.0)
            tools = response.tools
            print(f"Connected to {server_name} with tools:", [t.name for t in tools])

            for tool in tools:
                self.tool_to_session[tool.name] = session
                self.available_tools.append({
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema
                })

        except asyncio.TimeoutError:
            err_text = f"Connection to {server_name} timed out"
            print(err_text)
            self.response_signal.emit(err_text, self.stream)
        except asyncio.CancelledError:
            self.response_signal.emit(f"Connection to {server_name} cancelled.", self.stream)
            raise
        except Exception as e:
            err_text = f"Failed to connect to {server_name}: {e}"
            print(err_text)
            self.response_signal.emit(err_text, self.stream)

    async def connect_to_servers(self):
        if self.cleanup_requested:
            return

        try:
            with open(self.mcp_json, "r") as file:
                data = json.load(file)
            servers = data.get("mcpServers", {})

            connection_tasks = []
            for server_name, server_config in servers.items():
                if self.cleanup_requested:
                    break
                task = asyncio.create_task(
                    self.connect_to_server(server_name, server_config)
                )
                connection_tasks.append(task)

            # Wait for all connections to complete
            if connection_tasks:
                await asyncio.gather(*connection_tasks, return_exceptions=True)

        except asyncio.CancelledError:
            self.response_signal.emit("Server connection cancelled.", self.stream)
            raise
        except Exception as e:
            err_msg = f"Error loading server configuration: {e}"
            self.response_signal.emit(err_msg, self.stream)
            raise

    def _cancel_tasks(self):
        if not self.loop:
            return

        for task in asyncio.all_tasks(self.loop):
            if not task.done():
                task.cancel()

    def _cleanup_loop(self):
        if not self.loop:
            return

        try:
            # Cancel all remaining tasks
            pending = asyncio.all_tasks(self.loop)
            if pending:
                print(f"MCPOllamaThread: Cancelling {len(pending)} pending tasks...")
                for task in pending:
                    if not task.done():
                        task.cancel()

                # Wait for tasks to complete or be cancelled with timeout
                try:
                    self.loop.run_until_complete(
                        asyncio.wait_for(
                            asyncio.gather(*pending, return_exceptions=True),
                            timeout=3.0
                        )
                    )
                except asyncio.TimeoutError:
                    print("MCPOllamaThread: Task cleanup timed out")
                except Exception as e:
                    print(f"MCPOllamaThread: Error during task cleanup: {e}")

            # Windows-specific ProactorEventLoop cleanup
            if platform.system() == 'Windows' and hasattr(self.loop, '_selector'):
                try:
                    self.loop.run_until_complete(asyncio.sleep(0.25))
                except Exception:
                    pass

            # Close the event loop
            if not self.loop.is_closed():
                self.loop.close()
                print("MCPOllamaThread: Event loop closed")

        except Exception as e:
            print(f"MCPOllamaThread: Error during loop cleanup: {e}")
        finally:
            self.loop = None

    async def _cleanup_resources(self):
        try:
            print("MCPOllamaThread: Cleaning up resources...")

            # Close all sessions gracefully
            for session in self.sessions:
                try:
                    if hasattr(session, '_write_stream') and hasattr(session._write_stream, 'close'):
                        session._write_stream.close()
                        if hasattr(session._write_stream, 'wait_closed'):
                            await session._write_stream.wait_closed()
                except Exception as e:
                    print(f"Error closing session write stream: {e}")

                try:
                    if hasattr(session, '_read_stream') and hasattr(session._read_stream, 'close'):
                        session._read_stream.close()
                except Exception as e:
                    print(f"Error closing session read stream: {e}")

            # Give time for streams to close
            await asyncio.sleep(0.2)

            # Close the exit stack which manages all context managers
            try:
                await asyncio.wait_for(self.exit_stack.aclose(), timeout=5.0)
            except asyncio.TimeoutError:
                print("Warning: Exit stack cleanup timed out")
            except Exception as e:
                print(f"Error closing exit stack: {e}")

            # Clear references
            self.sessions.clear()
            self.tool_to_session.clear()
            self.available_tools.clear()

            print("MCPOllamaThread: Resources cleaned up successfully")
        except Exception as e:
            print(f"MCPOllamaThread: Error during cleanup: {e}")

    def set_force_stop(self, force_stop: bool):
        self.force_stop = force_stop
        if force_stop:
            self.cleanup_requested = True
            if self.loop and self.loop.is_running():
                print("Force Stop requested")
                self.loop.call_soon_threadsafe(self._cancel_tasks)
                self.response_finished_signal.emit(self.model, Constants.FORCE_STOP, 0.0, True)

    def finish_error(self, error_message: str):
        self.response_signal.emit(error_message, self.stream)
        elapsed_time = time.time() - self.start_time if self.start_time else 0.0
        self.response_finished_signal.emit(self.model, Constants.ERROR_STOP, elapsed_time, self.stream)

    def finish_run(self):
        elapsed_time = time.time() - self.start_time if self.start_time else 0.0
        self.response_finished_signal.emit(self.model, Constants.NORMAL_STOP, elapsed_time, self.stream)
