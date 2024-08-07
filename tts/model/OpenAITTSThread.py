import time

from PyQt6.QtCore import QThread, pyqtSignal
from openai import OpenAI

from util.Constants import Constants


class OpenAITTSThread(QThread):
    response_signal = pyqtSignal(bytes, str)
    response_finished_signal = pyqtSignal(str, str, float, bool)

    def __init__(self, args):
        super().__init__()
        self.openai_arg = args['ai_arg']
        self.openai = OpenAI(api_key=args['api_key'])
        self.model = self.openai_arg['model']
        self.response_format = self.openai_arg['response_format']
        self.stream = args['stream']
        self.force_stop = False
        self.start_time = None

    def run(self):
        self.start_time = time.time()
        try:
            response = self.get_response(self.openai_arg)
            self.handle_response(response)
        except Exception as e:
            self.response_signal.emit(str(e), self.response_format)

    def get_response(self, openai_arg):
        response = self.openai.audio.speech.create(**openai_arg)
        return response

    def set_force_stop(self, force_stop):
        self.force_stop = force_stop

    def handle_response(self, response):
        if self.force_stop:
            self.finish_run(self.model, Constants.FORCE_STOP, self.stream)
        else:
            result = response.content
            self.response_signal.emit(result, self.response_format)
            self.finish_run(self.model, Constants.NORMAL_STOP, self.stream)

    def finish_run(self, model, finish_reason, stream):
        end_time = time.time()
        elapsed_time = end_time - self.start_time
        self.response_finished_signal.emit(model, finish_reason, elapsed_time, stream)
