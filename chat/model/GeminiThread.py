import time

import google.genai as genai
from PyQt6.QtCore import QThread, pyqtSignal

from util.Constants import Constants
from google.genai import types


class GeminiThread(QThread):
    response_signal = pyqtSignal(str, bool)
    response_finished_signal = pyqtSignal(str, str, float, bool)

    def __init__(self, args):
        super().__init__()
        self.initialize_gemini(args)
        self.force_stop = False
        self.start_time = None

    def initialize_gemini(self, args):
        self.client = genai.Client(api_key=args['api_key'])
        self.ai_arg = args['ai_arg']
        self.config = types.GenerateContentConfig(**self.ai_arg['config'])
        self.contents = self.ai_arg['messages']
        self.stream = self.ai_arg['stream']
        self.model = self.ai_arg['model']

    def run(self):
        self.start_time = time.time()
        try:
            if self.stream:
                self.handle_stream_response(
                    self.client.models.generate_content_stream(model=self.model, contents=self.contents,
                                                               config=self.config))
            else:
                self.handle_response(
                    self.client.models.generate_content(model=self.model, contents=self.contents, config=self.config))
        except Exception as e:
            self.response_signal.emit(str(e), self.stream)

    def get_response(self, contents, stream):
        response = self.client.models.generate_content(model=self.model, contents=contents, config=self.config)
        return response

    def set_force_stop(self, force_stop):
        self.force_stop = force_stop

    def handle_response(self, response):
        if self.force_stop:
            self.finish_run(self.model, Constants.FORCE_STOP, self.stream)
        else:
            result = response.text
            self.response_signal.emit(result, self.stream)
            self.finish_run(self.model, response.candidates[0].finish_reason, self.stream)

    def handle_stream_response(self, response):
        finish_reason = None
        for chunk in response:
            if self.force_stop:
                self.finish_run(self.model, Constants.FORCE_STOP, self.stream)
                break
            else:
                result = chunk.text
                if result:
                    self.response_signal.emit(result, self.stream)
                    finish_reason = chunk.candidates[0].finish_reason
        self.finish_run(self.model, finish_reason, self.stream)

    def finish_run(self, model, finish_reason, stream):
        end_time = time.time()
        elapsed_time = end_time - self.start_time
        self.response_finished_signal.emit(model, finish_reason, elapsed_time, stream)
