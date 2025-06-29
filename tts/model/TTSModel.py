from PyQt6.QtCore import QObject, pyqtSignal

from tts.model.OpenAITTSThread import OpenAITTSThread
from util.Constants import AIProviderName, MODEL_MESSAGE


class AIThreadFactory:
    @staticmethod
    def create_thread(args, llm):
        if llm == AIProviderName.OPENAI.value:
            return OpenAITTSThread(args)
        else:
            raise ValueError(f"{MODEL_MESSAGE.MODEL_UNSUPPORTED} {llm}")


class TTSModel(QObject):
    thread_started_signal = pyqtSignal()
    thread_finished_signal = pyqtSignal()
    response_signal = pyqtSignal(bytes, str)
    response_finished_signal = pyqtSignal(str, str, float, bool)

    def __init__(self):
        super().__init__()
        self.tts_thread = None

    def send_user_input(self, args, llm):
        if self.tts_thread is not None and self.tts_thread.isRunning():
            print(f"{MODEL_MESSAGE.THREAD_RUNNING}")
            self.tts_thread.wait()

        self.tts_thread = AIThreadFactory.create_thread(args, llm)
        self.tts_thread.started.connect(self.thread_started_signal.emit)
        self.tts_thread.finished.connect(self.handle_thread_finished)
        self.tts_thread.response_signal.connect(self.response_signal.emit)
        self.tts_thread.response_finished_signal.connect(self.response_finished_signal.emit)
        self.tts_thread.start()

    def handle_thread_finished(self):
        print(f"{MODEL_MESSAGE.THREAD_FINISHED}")
        self.thread_finished_signal.emit()
        self.tts_thread = None

    def force_stop(self):
        if self.tts_thread is not None:
            self.tts_thread.set_force_stop(True)
