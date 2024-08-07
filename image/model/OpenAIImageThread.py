import time

import openai
from PyQt6.QtCore import QThread, pyqtSignal
from openai import OpenAI

from util.Constants import Constants, MODEL_MESSAGE


class OpenAIImageThread(QThread):
    response_signal = pyqtSignal(str, str)
    response_finished_signal = pyqtSignal(str, str, float, bool)

    def __init__(self, args):
        super().__init__()
        self.openai_arg = args['ai_arg']
        self.stream = args['stream']
        self.openai = OpenAI(api_key=args['api_key'])
        self.model = self.openai_arg['model']
        self.number_of_images = self.openai_arg['n']
        self.creation_type = args['creation_type']
        self.force_stop = False
        self.start_time = None

    def run(self):
        self.start_time = time.time()
        try:
            response = self.get_response(self.openai_arg)
            self.handle_response(response)
        except openai.OpenAIError as e:
            self.response_signal.emit(str(e.error), None)

    def get_response(self, openai_arg):
        if self.creation_type == Constants.DALLE_CREATE:
            return self.openai.images.generate(**openai_arg)
        elif self.creation_type == Constants.DALLE_EDIT:
            return self.openai.images.edit(**openai_arg)
        elif self.creation_type == Constants.DALLE_VARIATION:
            return self.openai.images.create_variation(**openai_arg)
        else:
            raise ValueError(f"{MODEL_MESSAGE.INVALID_CREATION_TYPE} {self.creation_type}")

    def set_force_stop(self, force_stop):
        self.force_stop = force_stop

    def handle_response(self, response):
        if self.force_stop:
            self.finish_run(self.model, Constants.FORCE_STOP, self.stream)
        else:
            count = len(response.data)
            for i in range(count):
                item = response.data[i]
                self.response_signal.emit(item.b64_json, item.revised_prompt)
                self.finish_run(self.model, Constants.NORMAL_STOP, self.stream)

    def finish_run(self, model, finish_reason, stream):
        end_time = time.time()
        elapsed_time = end_time - self.start_time
        self.response_finished_signal.emit(model, finish_reason, elapsed_time, stream)
