import re
import time

from PyQt6.QtCore import QThread, pyqtSignal
from openai import OpenAI

from util.Constants import Constants


class EvaluatorOpenAIThread(QThread):
    response_signal = pyqtSignal(str, bool)
    response_finished_signal = pyqtSignal(str, str, float, bool)

    def __init__(self, args):
        super().__init__()
        self.ai_arg = args['ai_arg']
        self.stream = self.ai_arg['stream']
        self.user_query = args['user_query']
        self.max_retries = args['max_retries']
        self.model = self.ai_arg['model']

        self.evaluator_prompt = args['evaluator_prompt']
        self.generator_prompt = args['generator_prompt']
        self.task_prompt = args['task_prompt']

        self.openai = OpenAI(api_key=args['api_key'])
        self.force_stop = False
        self.start_time = None

    def run(self):
        self.start_time = time.time()
        try:
            result, chain_of_thought = self.loop(
                self.task_prompt,
                self.evaluator_prompt,
                self.generator_prompt
            )

            if not self.force_stop:
                self.response_signal.emit(result, self.stream)
                self.finish_run(self.model, Constants.FORCE_STOP, self.stream)

        except Exception as e:
            self.response_signal.emit(str(e), self.stream)
            self.finish_run(self.model, Constants.ERROR_STOP, self.stream)

    def loop(self, task: str, evaluator_prompt: str, generator_prompt: str) -> tuple[str, list[dict]]:
        memory = []
        chain_of_thought = []
        attempt_count = 0

        thoughts, result = self.generate(generator_prompt, task)
        if self.force_stop:
            self.finish_run(self.model, Constants.FORCE_STOP, self.stream)
            return result, chain_of_thought

        memory.append(result)
        chain_of_thought.append({Constants.THOUGHTS_TAG: thoughts, Constants.RESULT_TAG: result})
        attempt_count += 1

        while not self.force_stop and attempt_count < self.max_retries:
            evaluation, feedback = self.evaluate(evaluator_prompt, result, task)
            if self.force_stop:
                self.finish_run(self.model, Constants.FORCE_STOP, self.stream)
                break

            if evaluation == Constants.EVALUATION_PASS:
                return result, chain_of_thought

            context = "\n".join([
                Constants.EVALUATION_PREVIOUS_ATTEMPTS,
                *[f"- {m}" for m in memory],
                f"\n{Constants.EVALUATION_FEEDBACK}: {feedback}"
            ])

            thoughts, result = self.generate(generator_prompt, task, context)
            if self.force_stop:
                self.finish_run(self.model, Constants.FORCE_STOP, self.stream)
                break

            memory.append(result)
            chain_of_thought.append(
                {Constants.THOUGHTS_TAG: thoughts, Constants.RESULT_TAG: result})

            attempt_count += 1

            retry_info = f"\n[Attempt {attempt_count} of {self.max_retries}]\n"
            self.response_signal.emit(retry_info, self.stream)

        if attempt_count >= self.max_retries and not self.force_stop:
            max_retry_message = f"\n[Maximum retry limit of {self.max_retries} reached. Stopping iterations.]\n"
            self.response_signal.emit(max_retry_message, self.stream)

        return result, chain_of_thought

    def get_response(self, prompt: str, system_prompt: str = "") -> str:
        if self.force_stop:
            self.finish_run(self.model, Constants.FORCE_STOP, self.stream)
            return ""

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        if self.stream:
            return self.dispatch_response(messages)
        else:
            params = self.build_api_params(messages)
            response = self.openai.chat.completions.create(**params)
            return response.choices[0].message.content

    def dispatch_response(self, messages: list) -> str:
        if self.force_stop:
            self.finish_run(self.model, Constants.FORCE_STOP, self.stream)
            return ""

        params = self.build_api_params(messages, stream=True)
        response_stream = self.openai.chat.completions.create(**params)

        current_model = None
        full_text = ""

        for chunk in response_stream:
            if self.force_stop:
                if current_model:
                    self.finish_run(current_model, Constants.FORCE_STOP, self.stream)
                return full_text

            if chunk.choices and len(chunk.choices) > 0:
                choice = chunk.choices[0]
                if hasattr(chunk, 'model') and chunk.model:
                    current_model = chunk.model

                if choice.delta and choice.delta.content:
                    chunk_text = choice.delta.content
                    self.response_signal.emit(chunk_text, self.stream)
                    full_text += chunk_text
                elif choice.finish_reason is not None:
                    # Stream finished
                    pass

        return full_text

    def build_api_params(self, messages: list, stream: bool = False) -> dict:
        params = {
            "model": self.ai_arg['model'],
            "messages": messages,
        }

        if 'max_tokens' in self.ai_arg and self.ai_arg['max_tokens'] is not None:
            params["max_tokens"] = self.ai_arg['max_tokens']

        if 'temperature' in self.ai_arg and self.ai_arg['temperature'] is not None:
            params["temperature"] = self.ai_arg['temperature']

        if stream:
            params["stream"] = True

        return params

    def extract_xml(self, text: str, tag: str) -> str:
        match = re.search(f'<{tag}>(.*?)</{tag}>', text, re.DOTALL)
        return match.group(1).strip() if match else ""

    def generate(self, prompt: str, task: str, context: str = "") -> tuple[str, str]:
        if self.force_stop:
            self.finish_run(self.model, Constants.FORCE_STOP, self.stream)
            return "", ""

        full_prompt = f"{prompt}\n{context}\n{Constants.EVALUATION_TASK} {task}" if context else f"{prompt}\n{Constants.EVALUATION_TASK} {task}"

        # Stream progress header before the actual response
        if self.stream:
            generation_header = f"\n{Constants.GENERATION_START}\n"
            self.response_signal.emit(generation_header, self.stream)

        response = self.get_response(full_prompt)
        thoughts = self.extract_xml(response, Constants.THOUGHTS_TAG)
        result = self.extract_xml(response, Constants.RESPONSE_TAG)

        # Emit generation summary
        if self.stream:
            # Only emit the summary information since the content was already streamed
            generation_info = f"\n{Constants.GENERATION_THOUGHTS}\n{thoughts}\n\n{Constants.GENERATION_GENERATED}\n{result}\n{Constants.GENERATION_END}\n"
        else:
            # Emit the full information for non-streaming mode
            generation_info = f"\n{Constants.GENERATION_START}\n{Constants.GENERATION_THOUGHTS}\n{thoughts}\n\n{Constants.GENERATION_GENERATED}\n{result}\n{Constants.GENERATION_END}\n"

        self.response_signal.emit(generation_info, self.stream)

        return thoughts, result

    def evaluate(self, prompt: str, content: str, task: str) -> tuple[str, str]:
        if self.force_stop:
            self.finish_run(self.model, Constants.FORCE_STOP, self.stream)
            return "", ""

        full_prompt = f"{prompt}\n{Constants.ORIGINAL_TASK} {task}\n{Constants.CONTENT_TO_EVALUATE} {content}"

        # Stream evaluation header before the actual response
        if self.stream:
            evaluation_header = f"{Constants.EVALUATION_START}\n"
            self.response_signal.emit(evaluation_header, self.stream)

        response = self.get_response(full_prompt)
        evaluation = self.extract_xml(response, Constants.EVALUATION_TAG)
        feedback = self.extract_xml(response, Constants.FEEDBACK_TAG)

        # Emit evaluation summary
        if self.stream:
            # Only emit the summary information since the content was already streamed
            evaluation_info = f"{Constants.EVALUATION_STATUS_EX} {evaluation}\n{Constants.EVALUATION_FEEDBACK_EX} {feedback}\n{Constants.EVALUATION_END}\n"
        else:
            # Emit the full information for non-streaming mode
            evaluation_info = f"{Constants.EVALUATION_START}\n{Constants.EVALUATION_STATUS_EX} {evaluation}\n{Constants.EVALUATION_FEEDBACK_EX} {feedback}\n{Constants.EVALUATION_END}\n"

        self.response_signal.emit(evaluation_info, self.stream)

        return evaluation, feedback

    def set_force_stop(self, force_stop):
        self.force_stop = force_stop

    def finish_run(self, model, finish_reason, stream):
        end_time = time.time()
        elapsed_time = end_time - self.start_time
        self.response_finished_signal.emit(model, finish_reason, elapsed_time, stream)
