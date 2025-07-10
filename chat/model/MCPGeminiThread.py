import asyncio
import copy
import json
import platform
import time
from contextlib import AsyncExitStack
from typing import List, TypedDict, Dict

import google.genai as genai
from PyQt6.QtCore import QThread, pyqtSignal
from google.genai import types
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from util.Constants import Constants


class ToolDefinition(TypedDict):
    name: str
    description: str
    input_schema: dict


class MCPGeminiThread(QThread):
    response_signal = pyqtSignal(str, bool)
    response_finished_signal = pyqtSignal(str, str, float, bool)

    def __init__(self, args):
        super().__init__()
        self.args = args
        self.api_key = args['api_key']
        self.ai_arg = args['ai_arg']
        self.model = self.ai_arg['model']
        self.contents = self.ai_arg['messages']
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

        self.client = genai.Client(api_key=self.api_key)

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

    def fix_schema(self, schema: dict) -> dict:
        """
        Recursively fix schema to be compatible with Gemini API:
        - Replace 'exclusiveMaximum' with 'maximum'
        - Replace 'exclusiveMinimum' with 'minimum'
        - Remove unsupported format values for STRING type
        - Remove other unsupported keys
        """
        if isinstance(schema, dict):
            new_schema = {}
            for k, v in schema.items():
                # skip these keys
                if k in ("additionalProperties", "$schema"):
                    continue
                elif k == "exclusiveMaximum":
                    new_schema["maximum"] = v
                elif k == "exclusiveMinimum":
                    new_schema["minimum"] = v
                elif k == "format" and isinstance(schema.get("type"), str) and schema.get("type").lower() == "string":
                    # Only allow 'enum' and 'date-time' formats for STRING type in Gemini
                    # Skip other formats like 'uri', 'url', 'email', etc.
                    if v in ("enum", "date-time"):
                        new_schema[k] = v
                elif isinstance(v, dict):
                    new_schema[k] = self.fix_schema(v)
                elif isinstance(v, list):
                    new_schema[k] = [self.fix_schema(i) if isinstance(i, dict) else i for i in v]
                else:
                    new_schema[k] = v
            return new_schema
        elif isinstance(schema, list):
            return [self.fix_schema(item) if isinstance(item, dict) else item for item in schema]
        return schema

    async def process_query(self, ai_arg) -> None:
        if self.cleanup_requested:
            return

        contents = self.contents

        tools = [
            types.Tool(
                function_declarations=[
                    {
                        "name": tool["name"],
                        "description": tool["description"],
                        "parameters": self.fix_schema(copy.deepcopy(tool["input_schema"]))
                    }
                ]
            )
            for tool in self.available_tools
        ]

        self.config = types.GenerateContentConfig(tools=tools, **self.ai_arg['config'])

        try:
            final_text = ""
            processing = True

            while processing and not self.force_stop:
                try:
                    response = self.client.models.generate_content(
                        model=self.model,
                        contents=contents,
                        config=self.config
                    )
                except Exception as api_error:
                    print(f"API call failed: {api_error}")
                    self.response_signal.emit(f"API Error: {str(api_error)}", self.stream)
                    processing = False
                    continue

                if not response or not response.candidates or len(response.candidates) == 0:
                    print("Warning: Empty response from Gemini API")
                    processing = False
                    continue

                candidate = response.candidates[0]
                if not candidate or not candidate.content:
                    print("Warning: No content in response candidate")
                    processing = False
                    continue

                parts = candidate.content.parts
                if not parts:
                    print("Warning: No parts in response content")
                    processing = False
                    continue

                text_parts = []
                function_calls = []

                # First, separate text and function calls
                for part in parts:
                    if hasattr(part, "text") and part.text:
                        text_parts.append(part.text)
                        final_text += part.text
                    elif hasattr(part, 'function_call') and part.function_call is not None:
                        function_calls.append(part.function_call)

                # Emit text response if any
                if text_parts:
                    text_content = "\n".join(text_parts)
                    self.response_signal.emit(text_content, self.stream)

                # Create a new message with the model's response
                model_parts = []

                # Add text parts first if present
                if text_parts:
                    for text in text_parts:
                        model_parts.append({"text": text})

                # Process function calls
                for function_call in function_calls:
                    tool_name = function_call.name
                    tool_args = function_call.args if hasattr(function_call, "args") else {}

                    print(f"Calling tool {tool_name} with args {tool_args}")

                    # Add function call to model message
                    model_parts.append({
                        "function_call": {
                            "name": tool_name,
                            "args": tool_args
                        }
                    })

                # Only add the model message if there are parts to add
                if model_parts:
                    contents.append({
                        "role": "model",
                        "parts": model_parts
                    })

                # Process function calls and add responses
                function_response_parts = []

                for function_call in function_calls:
                    tool_name = function_call.name
                    tool_args = function_call.args if hasattr(function_call, "args") else {}

                    # Special handling for sequentialthinking tool
                    if tool_name == "sequentialthinking" and 'thought' in tool_args:
                        thought_content = f"Calling tool {tool_name} with args {tool_args}"
                        self.response_signal.emit(f"{thought_content}\n", self.stream)

                    try:
                        # Call the tool
                        session = self.tool_to_session[tool_name]
                        result = await session.call_tool(tool_name, arguments=tool_args)

                        # Format and emit tool result
                        part_result = self.format_content(result.content)

                        # Emit result content conditionally
                        if tool_name != "sequentialthinking" or 'thought' not in tool_args:
                            self.response_signal.emit(f"{part_result}\n", self.stream)

                        # Add tool result to function response parts
                        function_response_parts.append({
                            "function_response": {
                                "name": tool_name,
                                "response": {"result": part_result}
                            }
                        })

                    except Exception as e:
                        error_msg = f"Error calling tool {tool_name}: {str(e)}"
                        self.response_signal.emit(error_msg, self.stream)

                        # Add error to function response parts
                        function_response_parts.append({
                            "function_response": {
                                "name": tool_name,
                                "response": {"error": error_msg}
                            }
                        })

                # Only add the function message if there are responses to add
                if function_response_parts:
                    contents.append({
                        "role": "function",
                        "parts": function_response_parts
                    })

                # Check if processing should continue
                if not function_calls:
                    print(f"No more function calls needed. Final text: '{final_text}'")
                    processing = False

                # Check if we got an empty response with no function calls
                if not text_parts and not function_calls:
                    print("Empty response - ending processing")
                    processing = False

            self.finish_run()

        except Exception as e:
            self.finish_error(f"Error processing query: {e}")

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
                print(f"MCPGeminiThread: Cancelling {len(pending)} pending tasks...")
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
                    print("MCPGeminiThread: Task cleanup timed out")
                except Exception as e:
                    print(f"MCPGeminiThread: Error during task cleanup: {e}")

            # Windows-specific ProactorEventLoop cleanup
            if platform.system() == 'Windows' and hasattr(self.loop, '_selector'):
                try:
                    self.loop.run_until_complete(asyncio.sleep(0.25))
                except Exception:
                    pass

            # Close the event loop
            if not self.loop.is_closed():
                self.loop.close()
                print("MCPGeminiThread: Event loop closed")

        except Exception as e:
            print(f"MCPGeminiThread: Error during loop cleanup: {e}")
        finally:
            self.loop = None

    async def _cleanup_resources(self):
        try:
            print("MCPGeminiThread: Cleaning up resources...")

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

            print("MCPGeminiThread: Resources cleaned up successfully")
        except Exception as e:
            print(f"MCPGeminiThread: Error during cleanup: {e}")

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
