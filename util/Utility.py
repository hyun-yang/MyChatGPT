import asyncio
import base64
import json
import os
import re
import sys
import tempfile
from pathlib import Path

import anthropic
import google.generativeai as genai
import openai
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QDialogButtonBox, QMessageBox

from util.Constants import Constants, UI, MODEL_MESSAGE
from util.MCPServerCheck import MCPServerCheck
from util.SettingsManager import SettingsManager
from typing import List, Optional, Tuple


class Utility:

    @staticmethod
    def check_openai_api_key(api_key):
        openai.api_key = api_key

        try:
            response = openai.models.list().model_dump()
            if response['data']:
                return True
            else:
                return False
        except openai.AuthenticationError:
            print(f"{MODEL_MESSAGE.AUTHENTICATION_FAILED_OPENAI}")
            return False
        except Exception as exception:
            print(f"{MODEL_MESSAGE.UNEXPECTED_ERROR} {str(exception)}")
            return False

    @staticmethod
    def check_gemini_api_key(api_key):
        genai.configure(api_key=api_key)

        try:
            response = genai.list_models()
            model_list = []
            for model in response:
                model_list.append(model)
            if len(model_list) > 0:
                return True
            else:
                return False
        except Exception as exception:
            print(f"{MODEL_MESSAGE.UNEXPECTED_ERROR} {str(exception)}")
            return False

    @staticmethod
    def check_claude_api_key(api_key):
        try:
            client = anthropic.Anthropic(api_key=api_key)
            response = client.messages.create(
                max_tokens=1024,
                messages=[
                    {
                        "role": "user",
                        "content": "Hi",
                    }
                ],
                model="claude-3-haiku-20240307",
                stream=False,
            )
            if response.content:
                return True
            else:
                return False
        except anthropic.AuthenticationError:
            print(f"{MODEL_MESSAGE.AUTHENTICATION_FAILED_CLAUDE}")
            return False
        except Exception as exception:
            print(f"{MODEL_MESSAGE.UNEXPECTED_ERROR} {str(exception)}")
            return False

    @staticmethod
    def check_ollama_api_key(api_key):
        return bool(api_key and api_key.strip())

    @staticmethod
    def get_openai_dalle_model_list(api_key):
        openai.api_key = api_key

        try:
            response = openai.models.list().model_dump()
            response_data = response['data']
            gtp_ids = [item['id'] for item in response_data if item['id'].strip().startswith('dall-e')]
            return gtp_ids
        except openai.AuthenticationError:
            print(f"{MODEL_MESSAGE.AUTHENTICATION_FAILED_OPENAI}")
            return []
        except Exception as exception:
            print(f"{MODEL_MESSAGE.UNEXPECTED_ERROR} {str(exception)}")
            return []

    @staticmethod
    def get_openai_model_list(api_key):
        openai.api_key = api_key

        try:
            response = openai.models.list().model_dump()
            response_data = response['data']
            gtp_ids = sorted([item['id'] for item in response_data if
                              'instruct' not in item['id'] and (item['id'].strip().startswith('gpt') or
                                                                item['id'].strip().startswith('o'))],
                             key=lambda x: ('gpt-3.5' in x, x))
            return gtp_ids
        except openai.AuthenticationError:
            print(f"{MODEL_MESSAGE.AUTHENTICATION_FAILED_OPENAI}")
            return []
        except Exception as exception:
            print(f"{MODEL_MESSAGE.UNEXPECTED_ERROR} {str(exception)}")
            return []

    @staticmethod
    def get_gemini_model_list(api_key):
        genai.configure(api_key=api_key)

        try:
            response = genai.list_models()
            gemini_models = [model for model in response if model.name.startswith('models/gemini')]
            name_list = [model.name.split('/')[-1] for model in gemini_models]
            return name_list
        except Exception as exception:
            print(f"{MODEL_MESSAGE.UNEXPECTED_ERROR} {str(exception)}")
            return []

    @staticmethod
    def get_gemini_vision_model_list(api_key):
        genai.configure(api_key=api_key)

        try:
            response = genai.list_models()
            gemini_models = [model for model in response if model.name.startswith('models/gemini')]
            name_list = [model.name.split('/')[-1] for model in gemini_models]
            image_models = [
                model for model in name_list
                if 'vision' in model or model.startswith('gemini-1.5-pro') or model.startswith('gemini-1.5-flash')
            ]
            sorted_models = sorted(image_models, reverse=True)
            return sorted_models
        except Exception as exception:
            print(f"{MODEL_MESSAGE.UNEXPECTED_ERROR} {str(exception)}")
            return []

    @staticmethod
    def get_gemini_tts_model_list(api_key):
        genai.configure(api_key=api_key)

        try:
            response = genai.list_models()
            gemini_models = [model for model in response if model.name.startswith('models/gemini')]
            name_list = [model.name.split('/')[-1] for model in gemini_models]
            image_models = [
                model for model in name_list
                if 'vision' in model or model.startswith('gemini-1.5-pro') or model.startswith('gemini-1.5-flash')
            ]
            sorted_models = sorted(image_models, reverse=True)
            return sorted_models
        except Exception as exception:
            print(f"{MODEL_MESSAGE.UNEXPECTED_ERROR} {str(exception)}")
            return []

    @staticmethod
    def parse_version_from_id(model_id: str) -> Optional[Tuple[int, int]]:
        """
        Handles:
        - claude-3-5-sonnet-20240620 -> (3, 5)
        - claude-4-opus-20240620 -> (4, 0)
        - claude-3-haiku-20240307 -> (3, 0)
        - claude-sonnet-4-20250514 -> (4, 0)
        - claude-opus-4-20250514 -> (4, 0)
        """
        # Pattern 1: claude-3-5-sonnet-20240620, claude-3-haiku-20240307, etc.
        m = re.match(r"claude-(\d+)(?:-(\d+))?", model_id)
        if m:
            major = int(m.group(1))
            minor = int(m.group(2)) if m.group(2) else 0
            return (major, minor)
        # Pattern 2: claude-sonnet-4-20250514, claude-opus-4-20250514, etc.
        m2 = re.match(r"claude-(?:[a-z]+)-(\d+)(?:-(\d+))?", model_id)
        if m2:
            major = int(m2.group(1))
            minor = int(m2.group(2)) if m2.group(2) else 0
            return (major, minor)
        return None

    @staticmethod
    def is_version_gte(version: Tuple[int, int], base_version: Tuple[int, int]) -> bool:
        return version >= base_version

    @staticmethod
    def filter_models(models: List, min_version=(3, 5)):
        """
        models: List[ModelInfo]
        min_version: tuple, e.g. (3, 5)
        """
        filtered = []
        for m in models:
            version = Utility.parse_version_from_id(m.id)
            if version and Utility.is_version_gte(version, min_version):
                filtered.append(m.id)
        return filtered

    @staticmethod
    def get_claude_ai_model_list(api_key):
        claude = anthropic.Anthropic(api_key=api_key)

        try:
            response = claude.models.list()
            model_list = Utility.filter_models(response.data, min_version=(3, 5))
            return model_list
        except anthropic.AuthenticationError:
            print(f"{MODEL_MESSAGE.AUTHENTICATION_FAILED_CLAUDE}")
            return []
        except Exception as exception:
            print(f"{MODEL_MESSAGE.UNEXPECTED_ERROR} {str(exception)}")
            return []

    @staticmethod
    def add_ollama_model_list():
        settings = SettingsManager.get_settings()
        settings.beginGroup(Constants.OLLAMA_MODEL_LIST_SECTION)
        for model in Constants.OLLAMA_MODEL_LIST:
            settings.setValue(model, True)
        settings.endGroup()

    @staticmethod
    def get_ollama_ai_model_list(api_key):
        Utility.add_ollama_model_list()
        settings = SettingsManager.get_settings()
        settings.beginGroup(Constants.OLLAMA_MODEL_LIST_SECTION)
        model_list = [key for key in settings.childKeys()]
        settings.endGroup()
        return model_list

    @staticmethod
    def get_icon_path(folder: str, icon: str):
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = Path(os.path.dirname(__file__))
            base_path = base_path.parents[0]  # root path

        icon_path = os.path.join(base_path, folder, icon)
        icon_path = icon_path.replace(os.sep, '/')

        if not os.path.exists(icon_path):
            print(f"{UI.ICON_FILE_ERROR} {icon_path} {UI.ICON_FILE_NOT_EXIST}")
            return None
        return icon_path

    @staticmethod
    def get_settings_value(section: str, prop: str, default: str, save: bool) -> str:
        settings = SettingsManager.get_settings()
        settings.beginGroup(section)

        value = settings.value(prop, None)

        if value is None:
            if save:
                settings.setValue(prop, default)
                settings.sync()
            value = default

        settings.endGroup()
        return value

    @staticmethod
    def get_system_value(section: str, prefix: str, default: str, length: int) -> dict:
        settings = SettingsManager.get_settings()

        if section not in settings.childGroups():
            settings.beginGroup(section)
            for i in range(1, length + 1):
                settings.setValue(f"{prefix}{i}", default)
            settings.endGroup()

        settings.beginGroup(section)
        values = {f"{prefix}{i}": settings.value(f"{prefix}{i}", default) for i in range(1, length + 1)}
        settings.endGroup()

        return values

    @staticmethod
    def extract_number_from_end(name):
        match = re.search(r'\d+$', name)
        if match:
            return int(match.group())
        return None

    @staticmethod
    def confirm_dialog(title: str, message: str) -> bool:
        dialog = QDialog()
        dialog.setWindowTitle(title)
        dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
        dialog.setLayout(QVBoxLayout())

        message_label = QLabel(message)
        dialog.layout().addWidget(message_label)

        dialog_buttonbox = QDialogButtonBox(QDialogButtonBox.StandardButton.Yes | QDialogButtonBox.StandardButton.No)
        dialog.layout().addWidget(dialog_buttonbox)

        no_button = dialog_buttonbox.button(QDialogButtonBox.StandardButton.No)
        no_button.setDefault(True)
        no_button.setFocus()

        def on_click(button):
            dialog.done(dialog_buttonbox.standardButton(button) == QDialogButtonBox.StandardButton.Yes)

        dialog_buttonbox.clicked.connect(on_click)

        result = dialog.exec()
        return result == QDialog.DialogCode.Accepted

    @staticmethod
    def show_alarm_message(title: str, message: str,
                           buttons: QMessageBox.StandardButton = QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel):
        message_box = QMessageBox()
        message_box.setWindowTitle(title)
        message_box.setText(message)
        message_box.setStandardButtons(buttons)
        return message_box.exec()

    @staticmethod
    def base64_encode_file(path):
        with open(path, UI.FILE_READ_IN_BINARY_MODE) as file:
            return base64.b64encode(file.read()).decode(UI.UTF_8)

    @staticmethod
    def create_temp_file(content, extension_name, apply_decode):
        with tempfile.NamedTemporaryFile(delete=False, suffix='.' + extension_name) as temp_file:
            if apply_decode:
                temp_file.write(base64.b64decode(content))
            else:
                temp_file.write(content)
            temp_file.flush()
            temp_file_name = temp_file.name
        return temp_file_name

    @staticmethod
    def is_over_4k_limit(file_path: str) -> bool:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                content = file.read()
                return len(content) < Constants.TTS_4K_LIMIT
        except FileNotFoundError:
            print(f"{UI.TTS_FILE_NOT_FOUND} '{file_path}'")
            return False
        except Exception as e:
            print(f"{UI.TTS_FILE_ERROR} {e}")
            return False

    @staticmethod
    async def get_available_tools_count_ex(config_path):
        mcp_service_check = MCPServerCheck(config_path)

        try:
            init_success = await mcp_service_check.initialize()
            if not init_success:
                return 0
            tools = mcp_service_check.get_available_tools()
            tool_count = len(tools)
            return tool_count
        except Exception as e:
            print(f"Error getting MCP tools: {e}")
            return 0

        finally:
            await mcp_service_check.cleanup()

    @staticmethod
    def check_mcp_tools_ex(config_path, parent_widget=None):
        try:
            with open(config_path, "r") as file:
                json.load(file)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            QMessageBox.critical(
                parent_widget,
                'MCP Configuration Error',
                f'Invalid configuration file: {str(e)}',
                QMessageBox.StandardButton.Ok
            )
            return

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        tool_count = loop.run_until_complete(Utility.get_available_tools_count(config_path))
        loop.close()

        if tool_count > 0:
            QMessageBox.information(
                parent_widget,
                'MCP Tools',
                f'There are {tool_count} tools available.',
                QMessageBox.StandardButton.Ok
            )
        else:
            QMessageBox.warning(
                parent_widget,
                'MCP Tools',
                'No MCP tools are available. Make sure the configuration is correct.',
                QMessageBox.StandardButton.Ok
            )

    @staticmethod
    async def get_available_tools_count(config_path):
        """Get the count of available MCP tools."""
        server_check = MCPServerCheck(config_path)
        try:
            await server_check.initialize()
            tool_count = len(server_check.get_available_tools())
            # Ensure cleanup happens before returning
            await server_check.cleanup()
            return tool_count
        except Exception as e:
            print(f"Error checking MCP tools: {e}")
            # Make sure to clean up even if there's an error
            await server_check.cleanup()
            return 0

    @staticmethod
    def check_mcp_tools(config_path, parent_widget=None):
        try:
            with open(config_path, "r") as file:
                json.load(file)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            QMessageBox.critical(
                parent_widget,
                'MCP Configuration Error',
                f'Invalid configuration file: {str(e)}',
                QMessageBox.StandardButton.Ok
            )
            return

        # Safer way to get or create an event loop
        try:
            # Try to get the current event loop
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                raise RuntimeError("Event loop is closed")
            should_close = False
        except RuntimeError:
            # Create a new event loop if one isn't available
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            should_close = True

        try:
            tool_count = loop.run_until_complete(Utility.get_available_tools_count(config_path))

            if tool_count > 0:
                QMessageBox.information(
                    parent_widget,
                    'MCP Tools',
                    f'There are {tool_count} tools available.',
                    QMessageBox.StandardButton.Ok
                )
            else:
                QMessageBox.warning(
                    parent_widget,
                    'MCP Tools',
                    'No MCP tools are available. Make sure the configuration is correct.',
                    QMessageBox.StandardButton.Ok
                )
        finally:
            # Ensure all pending tasks are completed
            try:
                pending = asyncio.all_tasks(loop)
                if pending:
                    loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            except RuntimeError:
                # Handle case where loop might already be closed
                pass

            # Only close the loop if we created it
            if should_close and not loop.is_closed():
                loop.close()