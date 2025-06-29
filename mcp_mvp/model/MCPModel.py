from PyQt6.QtCore import QObject, pyqtSignal

from chat.model.ClaudeThread import ClaudeThread
from chat.model.OpenAIThread import OpenAIThread
from mcp_mvp.model.MCPClaudeThread import MCPClaudeThread
from mcp_mvp.model.MCPOpenAIThread import MCPOpenAIThread
from util.Constants import MODEL_MESSAGE, AIProviderName
from util.SettingsManager import SettingsManager


class MCPThreadFactory:
    @staticmethod
    def create_thread(args, llm, mcp=True):
        if mcp:
            if llm == AIProviderName.CLAUDE.value:
                return MCPClaudeThread(args)
            elif llm == AIProviderName.OPENAI.value:
                return MCPOpenAIThread(args)
            else:
                raise ValueError(f"{MODEL_MESSAGE.MODEL_UNSUPPORTED} {llm}")
        else:
            if llm == AIProviderName.CLAUDE.value:
                return ClaudeThread(args)
            elif llm == AIProviderName.OPENAI.value:
                return OpenAIThread(args)
            else:
                raise ValueError(f"{MODEL_MESSAGE.MODEL_UNSUPPORTED} {llm}")


class MCPModel(QObject):
    thread_started_signal = pyqtSignal()
    thread_finished_signal = pyqtSignal()
    response_signal = pyqtSignal(str, bool)
    response_finished_signal = pyqtSignal(str, str, float, bool)

    def __init__(self):
        super().__init__()
        self.mcp_thread = None
        self._settings = SettingsManager.get_settings()

    def send_user_input(self, args, llm):
        if self.mcp_thread is not None and self.mcp_thread.isRunning():
            print(f"{MODEL_MESSAGE.THREAD_RUNNING}")
            self.mcp_thread.wait()

        self.mcp_thread = MCPThreadFactory.create_thread(args, llm, mcp=bool(self._settings.value('MCP/config_path')))
        self.mcp_thread.started.connect(self.thread_started_signal.emit)
        self.mcp_thread.finished.connect(self.handle_thread_finished)
        self.mcp_thread.response_signal.connect(self.response_signal.emit)
        self.mcp_thread.response_finished_signal.connect(self.response_finished_signal.emit)
        self.mcp_thread.start()

    def handle_thread_finished(self):
        print(f"{MODEL_MESSAGE.THREAD_FINISHED}")
        self.thread_finished_signal.emit()
        self.mcp_thread = None

    def force_stop(self):
        if self.mcp_thread is not None:
            self.mcp_thread.set_force_stop(True)
