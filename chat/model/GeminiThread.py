import time

import google.generativeai as genai
from PyQt6.QtCore import QThread, pyqtSignal

from util.Constants import Constants


class GeminiThread(QThread):
    response_signal = pyqtSignal(str, bool)
    response_finished_signal = pyqtSignal(str, str, float, bool)

    def __init__(self, args):
        super().__init__()
        self.initialize_gemini(args)
        self.force_stop = False
        self.start_time = None

    def initialize_gemini(self, args):
        genai.configure(api_key=args['api_key'])
        ai_arg = args['ai_arg']
        system = ai_arg['system']
        config = genai.GenerationConfig(**ai_arg['config'])
        safety_settings = ai_arg['safety_settings']
        # REVIEW : 400 Developer instruction is not enabled for models/gemini-pro
        #           400 Add an image to use models/gemini-pro-vision, or switch your model to a text model.
        # gemini-1.5-pro-latest, gemini-1.5-flash-latest

        self.gemini = genai.GenerativeModel(model_name=ai_arg['model'], generation_config=config,
                                            safety_settings=safety_settings, system_instruction=system)
        self.contents = ai_arg['messages']
        self.stream = ai_arg['stream']
        self.model = ai_arg['model']

    def run(self):
        self.start_time = time.time()
        try:
            response = self.get_response(self.contents, self.stream)
            if self.stream:
                self.handle_stream_response(response)
            else:
                self.handle_response(response)
        except Exception as e:
            self.response_signal.emit(str(e), self.stream)

    def get_response(self, contents, stream):
        response = self.gemini.generate_content(contents=contents, stream=stream)
        return response

    def set_force_stop(self, force_stop):
        self.force_stop = force_stop

    def handle_response(self, response):
        if self.force_stop:
            self.finish_run(self.model, Constants.FORCE_STOP, self.stream)
        else:
            result = response.text
            self.response_signal.emit(result, self.stream)
            self.finish_run(self.model, response.candidates[0].finish_reason.name, self.stream)

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
                    finish_reason = chunk.candidates[0].finish_reason.name
        self.finish_run(self.model, finish_reason, self.stream)

    def finish_run(self, model, finish_reason, stream):
        end_time = time.time()
        elapsed_time = end_time - self.start_time
        self.response_finished_signal.emit(model, finish_reason, elapsed_time, stream)
