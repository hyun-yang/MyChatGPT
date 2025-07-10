from PyQt6.QtCore import QObject, pyqtSignal

from chat.model.ClaudeThread import ClaudeThread
from chat.model.GeminiThread import GeminiThread
from chat.model.OllamaThread import OllamaThread
from chat.model.OpenAIThread import OpenAIThread
from chat.model.MCPClaudeThread import MCPClaudeThread
from chat.model.MCPGeminiThread import MCPGeminiThread
from chat.model.MCPOllamaThread import MCPOllamaThread
from chat.model.MCPOpenAIThread import MCPOpenAIThread
from util.Constants import AIProviderName, MODEL_MESSAGE


class AIThreadFactory:
    @staticmethod
    def create_thread(args, chat_llm, mcp=False):
        if mcp:
            if chat_llm == AIProviderName.CLAUDE.value:
                return MCPClaudeThread(args)
            elif chat_llm == AIProviderName.OPENAI.value:
                return MCPOpenAIThread(args)
            elif chat_llm == AIProviderName.GEMINI.value:
                return MCPGeminiThread(args)
            elif chat_llm == AIProviderName.OLLAMA.value:
                return MCPOllamaThread(args)
            else:
                raise ValueError(f"{MODEL_MESSAGE.MODEL_UNSUPPORTED} {chat_llm}")
        else:
            if chat_llm == AIProviderName.GEMINI.value:
                return GeminiThread(args)
            elif chat_llm == AIProviderName.OPENAI.value:
                return OpenAIThread(args)
            elif chat_llm == AIProviderName.CLAUDE.value:
                return ClaudeThread(args)
            elif chat_llm == AIProviderName.OLLAMA.value:
                return OllamaThread(args)
            else:
                raise ValueError(f"{MODEL_MESSAGE.MODEL_UNSUPPORTED} {chat_llm}")


class ChatModel(QObject):
    thread_started_signal = pyqtSignal()
    thread_finished_signal = pyqtSignal()
    response_signal = pyqtSignal(str, bool)
    response_finished_signal = pyqtSignal(str, str, float, bool)

    def __init__(self):
        super().__init__()
        self.chat_thread = None

    def send_user_input(self, args, chat_llm):
        if self.chat_thread is not None and self.chat_thread.isRunning():
            print(f"{MODEL_MESSAGE.THREAD_RUNNING}")
            self.chat_thread.wait()

        mcp_check = args.get('mcp', False)
        mcp_json = args.get('mcp_json', False)
        self.chat_thread = AIThreadFactory.create_thread(args, chat_llm, mcp_check and mcp_json)
        self.chat_thread.started.connect(self.thread_started_signal.emit)
        self.chat_thread.finished.connect(self.handle_thread_finished)
        self.chat_thread.response_signal.connect(self.response_signal.emit)
        self.chat_thread.response_finished_signal.connect(self.response_finished_signal.emit)
        self.chat_thread.start()

    def handle_thread_finished(self):
        print(f"{MODEL_MESSAGE.THREAD_FINISHED}")
        self.thread_finished_signal.emit()
        self.chat_thread = None

    def force_stop(self):
        if self.chat_thread is not None:
            self.chat_thread.set_force_stop(True)
