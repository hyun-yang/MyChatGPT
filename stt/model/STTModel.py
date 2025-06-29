from PyQt6.QtCore import QObject, pyqtSignal

from stt.model.OpenAISTTThread import OpenAISTTThread
from util.Constants import AIProviderName, MODEL_MESSAGE


class AIThreadFactory:
    @staticmethod
    def create_thread(args, llm):
        if llm == AIProviderName.OPENAI.value:
            return OpenAISTTThread(args)
        else:
            raise ValueError(f"{MODEL_MESSAGE.MODEL_UNSUPPORTED} {llm}")


class STTModel(QObject):
    thread_started_signal = pyqtSignal()
    thread_finished_signal = pyqtSignal()
    response_signal = pyqtSignal(str, str)
    response_finished_signal = pyqtSignal(str, str, float, bool)

    def __init__(self):
        super().__init__()
        self.stt_thread = None

    def send_user_input(self, args, llm):
        if self.stt_thread is not None and self.stt_thread.isRunning():
            print(f"{MODEL_MESSAGE.THREAD_RUNNING}")
            self.stt_thread.wait()

        self.stt_thread = AIThreadFactory.create_thread(args, llm)
        self.stt_thread.started.connect(self.thread_started_signal.emit)
        self.stt_thread.finished.connect(self.handle_thread_finished)
        self.stt_thread.response_signal.connect(self.response_signal.emit)
        self.stt_thread.response_finished_signal.connect(self.response_finished_signal.emit)
        self.stt_thread.start()

    def handle_thread_finished(self):
        print(f"{MODEL_MESSAGE.THREAD_FINISHED}")
        self.thread_finished_signal.emit()
        self.stt_thread = None

    def force_stop(self):
        if self.stt_thread is not None:
            self.stt_thread.set_force_stop(True)
