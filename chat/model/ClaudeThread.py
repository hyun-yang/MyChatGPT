import time
import anthropic

from PyQt6.QtCore import QThread, pyqtSignal
from anthropic.types import ContentBlockDeltaEvent, MessageStopEvent, MessageStartEvent
from util.Constants import Constants


class ClaudeThread(QThread):
    response_signal = pyqtSignal(str, bool)
    response_finished_signal = pyqtSignal(str, str, float, bool)

    def __init__(self, args):
        super().__init__()
        self.ai_arg = args['ai_arg']
        self.claude = anthropic.Anthropic(api_key=args['api_key'])
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
        response = self.claude.messages.create(**ai_arg)
        return response

    def set_force_stop(self, force_stop):
        self.force_stop = force_stop

    def handle_response(self, response):
        if self.force_stop:
            self.finish_run(response.model, Constants.FORCE_STOP, self.stream)
        else:
            result = response.content[0].text
            self.response_signal.emit(result, self.stream)
            self.finish_run(response.model, response.stop_reason, self.stream)

    def handle_stream_response(self, response):
        current_model = None
        for chunk in response:
            if self.force_stop:
                self.finish_run(current_model, Constants.FORCE_STOP, self.stream)
                break
            else:
                if isinstance(chunk, MessageStartEvent):
                    current_model = chunk.message.model
                elif isinstance(chunk, ContentBlockDeltaEvent):
                    self.response_signal.emit(chunk.delta.text, self.stream)
                elif isinstance(chunk, MessageStopEvent):
                    self.finish_run(current_model, chunk.type, self.stream)

    def finish_run(self, model, finish_reason, stream):
        end_time = time.time()
        elapsed_time = end_time - self.start_time
        self.response_finished_signal.emit(model, finish_reason, elapsed_time, stream)

