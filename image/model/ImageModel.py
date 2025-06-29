from PyQt6.QtCore import QObject, pyqtSignal

from image.model.OpenAIImageThread import OpenAIImageThread
from util.Constants import AIProviderName, MODEL_MESSAGE


class AIThreadFactory:
    @staticmethod
    def create_thread(args, llm):
        if llm == AIProviderName.OPENAI.value:
            return OpenAIImageThread(args)
        else:
            raise ValueError(f"{MODEL_MESSAGE.MODEL_UNSUPPORTED} {llm}")


class ImageModel(QObject):
    thread_started_signal = pyqtSignal()
    thread_finished_signal = pyqtSignal()
    response_signal = pyqtSignal(str, str)
    response_finished_signal = pyqtSignal(str, str, float, bool)

    def __init__(self):
        super().__init__()
        self.image_thread = None

    def send_user_input(self, args, llm):
        if self.image_thread is not None and self.image_thread.isRunning():
            print(f"{MODEL_MESSAGE.THREAD_RUNNING}")
            self.image_thread.wait()

        self.image_thread = AIThreadFactory.create_thread(args, llm)
        self.image_thread.started.connect(self.thread_started_signal.emit)
        self.image_thread.finished.connect(self.handle_thread_finished)
        self.image_thread.response_signal.connect(self.response_signal.emit)
        self.image_thread.response_finished_signal.connect(self.response_finished_signal.emit)
        self.image_thread.start()

    def handle_thread_finished(self):
        print(f"{MODEL_MESSAGE.THREAD_FINISHED}")
        self.thread_finished_signal.emit()
        self.image_thread = None

    def force_stop(self):
        if self.image_thread is not None:
            self.image_thread.set_force_stop(True)
