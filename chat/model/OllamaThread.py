import time

import ollama
from PyQt6.QtCore import QThread, pyqtSignal

from util.Constants import Constants


class OllamaThread(QThread):
    response_signal = pyqtSignal(str, bool)
    response_finished_signal = pyqtSignal(str, str, float, bool)

    def __init__(self, args):
        super().__init__()
        self.ai_arg = args['ai_arg']
        self.ollama = ollama
        self.stream = self.ai_arg['stream']
        self.force_stop = False
        self.start_time = None

    def run(self):
        self.start_time = time.time()
        try:
            response = self.get_response(self.ai_arg)
            if self.stream:
                self.handle_stream_response(response)
            else:
                self.handle_response(response)
        except Exception as e:
            self.response_signal.emit(str(e), self.stream)

    def get_response(self, ai_arg):
        response = self.ollama.chat(**ai_arg)
        return response

    def set_force_stop(self, force_stop):
        self.force_stop = force_stop

    def handle_response(self, response):
        if self.force_stop:
            self.finish_run(response['model'], Constants.FORCE_STOP, self.stream)
        else:
            result = response['message']['content']
            model = response['model']
            finish_reason = response['done_reason']
            self.response_signal.emit(result, self.stream)
            self.finish_run(model, finish_reason, self.stream)

    def handle_stream_response(self, response):
        for chunk in response:
            if self.force_stop:
                self.finish_run(chunk['model'], Constants.FORCE_STOP, self.stream)
                break
            else:
                content = chunk['message']['content']
                done = chunk['done']
                if not done:
                    self.response_signal.emit(content, self.stream)
                else:
                    finish_reason = chunk['done_reason']
                    if finish_reason is not None:
                        self.finish_run(chunk['model'], finish_reason, self.stream)

    def finish_run(self, model, finish_reason, stream):
        end_time = time.time()
        elapsed_time = end_time - self.start_time
        self.response_finished_signal.emit(model, finish_reason, elapsed_time, stream)
