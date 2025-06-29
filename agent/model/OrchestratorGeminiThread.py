import asyncio
import json
import re
import time

import google.genai as genai
from PyQt6.QtCore import QThread, pyqtSignal
from google.genai import types

from util.Constants import Constants


class OrchestratorGeminiThread(QThread):
    response_signal = pyqtSignal(str, bool)
    response_finished_signal = pyqtSignal(str, str, float, bool)

    def __init__(self, args):
        super().__init__()
        self.ai_arg = args['ai_arg']
        self.stream = self.ai_arg['stream']
        self.user_query = args['user_query']

        self.orchestrator_prompt = args['orchestrator_prompt']
        self.worker_prompt = args['worker_prompt']
        self.aggregator_prompt = args['aggregator_prompt']

        self.model_name = self.ai_arg['model']
        self.client = genai.Client(api_key=args['api_key'])
        self.config = types.GenerateContentConfig(**self.ai_arg['config'])

        self.force_stop = False
        self.start_time = None

    def run(self):
        self.start_time = time.time()
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._async_run())
        except Exception as e:
            self.response_signal.emit(f"{Constants.ERROR_STOP} : {str(e)}", self.stream)
            self.response_finished_signal.emit(self.ai_arg['model'], Constants.ERROR_STOP, 0.00, self.stream)
        finally:
            if 'loop' in locals() and loop.is_running():
                loop.close()

    async def _async_run(self):
        try:
            # Orchestrator response
            if self.stream:
                self.response_signal.emit(Constants.ORCHESTRATOR_ANALYSIS_TASK, self.stream)
                response_stream = await self.get_response(self.ai_arg)
                full_response_stream = await self.dispatch_response_with_header(
                    response_stream, self.stream, Constants.ORCHESTRATOR_ANALYSIS
                )
                clean_result = self._clean_json_string(full_response_stream)
            else:
                response = await self.get_async_response(self.ai_arg)
                full_response_not_stream = self._extract_text_from_response(response)
                clean_result = self._clean_json_string(full_response_not_stream)

            try:
                response_json = json.loads(clean_result)
                tasks = response_json.get("tasks", [])
                print(f"Tasks count: {len(tasks)}")

                worker_prompts = []
                for i, task in enumerate(tasks):
                    prompt = self.get_worker_prompt(self.user_query,
                                                    task["task"],
                                                    task["description"])
                    worker_prompts.append(prompt)
                    print(f"Task {i + 1} prompt generation completed")

                # Worker response
                if self.stream:
                    self.response_signal.emit(Constants.ORCHESTRATOR_EXECUTING_TASKS, self.stream)
                    worker_responses = await self.run_llm_sequential_stream(worker_prompts, tasks, self.ai_arg)
                else:
                    print("Parallel LLM calls start")
                    worker_responses = await self.run_llm_parallel(worker_prompts, self.ai_arg)
                    print("Parallel LLM calls completed")

                # Aggregator response
                if self.stream:
                    self.response_signal.emit(Constants.ORCHESTRATOR_GENERATING_FINAL_RESULTS, self.stream)
                    aggregator_prompt = self.get_aggregator_prompt(self.user_query)
                    for i in range(len(worker_responses)):
                        aggregator_prompt += f"\n{i + 1}. {Constants.ORCHESTRATOR_TASK_QUESTION} {tasks[i]['task']}\n"
                        aggregator_prompt += f"\n{Constants.ORCHESTRATOR_RESPONSE} {worker_responses[i]}\n\n"

                    aggregator_parts = [types.Part.from_text(text=aggregator_prompt)]
                    aggregator_messages = [{"role": "user", "parts": aggregator_parts}]
                    aggregator_ai_args = self.ai_arg.copy()
                    aggregator_ai_args['messages'] = aggregator_messages

                    final_response = await self.get_response(aggregator_ai_args)
                    final_full_response = await self.dispatch_response_with_header(
                        final_response, self.stream, Constants.ORCHESTRATOR_FINAL_ANSWER
                    )
                    print(f"\n\n{final_full_response}")

                    self.finish_run(self.ai_arg['model'], Constants.NORMAL_STOP, self.stream)
                else:
                    aggregator_prompt = self.get_aggregator_prompt(self.user_query)
                    for i in range(len(worker_responses)):
                        aggregator_prompt += f"\n{i + 1}. {Constants.ORCHESTRATOR_TASK_QUESTION} {tasks[i]['task']}\n"
                        aggregator_prompt += f"\n{Constants.ORCHESTRATOR_RESPONSE} {worker_responses[i]}\n\n"

                    aggregator_parts = [types.Part.from_text(text=aggregator_prompt)]
                    aggregator_messages = [{"role": "user", "parts": aggregator_parts}]
                    aggregator_ai_args = self.ai_arg.copy()
                    aggregator_ai_args['messages'] = aggregator_messages

                    final_response = await self.get_async_response(aggregator_ai_args)
                    final_full_response = self._extract_text_from_response(final_response)

                    combined_result = '\n\n'.join([full_response_not_stream] + worker_responses + [final_full_response])
                    self.response_signal.emit(combined_result, self.stream)
                    self.finish_run(self.ai_arg['model'], Constants.NORMAL_STOP, self.stream)

            except json.JSONDecodeError as je:
                self.response_signal.emit(
                    f"{Constants.ORCHESTRATOR_JSON_PARSING_ERROR} {je}\n{Constants.ORCHESTRATOR_ORIGINAL_RESPONSE} {clean_result}",
                    self.stream)
                self.response_finished_signal.emit(self.ai_arg['model'], Constants.ERROR_STOP, 0.00, self.stream)

        except Exception as e:
            self.response_signal.emit(f"{Constants.ORCHESTRATOR_ERROR_PROCESSING} {str(e)}", self.stream)
            self.response_finished_signal.emit(self.ai_arg['model'], Constants.ERROR_STOP, 0.00, self.stream)

    async def get_response(self, gemini_arg):
        contents = gemini_arg['messages']
        response_coroutine = self.client.aio.models.generate_content_stream(
            model=gemini_arg['model'],
            contents=contents,
            config=self.config
        )
        response = await response_coroutine
        return response

    async def dispatch_response_with_header(self, response, stream, header_text):
        full_content = ""
        async for chunk in response:
            content = self._extract_text_from_response(chunk)
            if content:
                full_content += content
                self.response_signal.emit(content, stream)
            if self.force_stop:
                break

        self.response_signal.emit(f"\n--- {header_text} {Constants.ORCHESTRATOR_COMPLETED} ---\n\n", stream)
        return full_content

    async def dispatch_response(self, response, stream):
        full_content = ""
        async for chunk in response:
            content = self._extract_text_from_response(chunk)
            if content:
                full_content += content
                self.response_signal.emit(content, stream)
            if self.force_stop:
                break

        return full_content

    async def get_async_response(self, gemini_arg):
        contents = gemini_arg['messages']

        response = await self.client.aio.models.generate_content(
            model=gemini_arg['model'],
            contents=contents,
            config=self.config
        )

        return response

    def _extract_text_from_response(self, response):
        try:
            if hasattr(response, "text") and response.text:
                return response.text
            if hasattr(response, "candidates") and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, "content") and hasattr(candidate.content, "parts"):
                    parts = candidate.content.parts
                    if parts and hasattr(parts[0], "text"):
                        return parts[0].text
            return str(response)
        except Exception as e:
            print(f"Failed to extract text from response: {e}")
            return ""

    async def run_llm_parallel(self, prompt_list, ai_arg):
        tasks = []
        responses = []

        try:
            for prompt in prompt_list:
                task = self.call_llm_async(prompt, ai_arg)
                tasks.append(task)

            for task in asyncio.as_completed(tasks):
                try:
                    result = await task
                    responses.append(result)
                except Exception as e:
                    print(f"{Constants.ORCHESTRATOR_ERROR_PARALLEL}{str(e)}")
                    responses.append(f"{Constants.ORCHESTRATOR_ERROR} {str(e)}")
        except Exception as e:
            print(f"{Constants.ORCHESTRATOR_ERROR_PARALLEL_PROCESSING} {str(e)}")

        return responses

    async def run_llm_sequential_stream(self, prompt_list, sub_tasks, ai_arg):
        responses = []

        try:
            for i, prompt in enumerate(prompt_list):
                try:
                    # Worker start
                    task_header = f"\n--- {Constants.ORCHESTRATOR_SUBTASK} {i + 1}: {sub_tasks[i]['task']} ---\n"
                    self.response_signal.emit(task_header, self.stream)

                    result = await self.call_llm_async_stream_sequential(prompt, ai_arg)
                    responses.append(result)

                    # Worker completed
                    self.response_signal.emit(
                        f"\n--- {Constants.ORCHESTRATOR_TASK} {i + 1} {Constants.ORCHESTRATOR_COMPLETED} ---\n",
                        self.stream)

                except Exception as e:
                    print(f"{Constants.ORCHESTRATOR_WORKER} {i} {Constants.ORCHESTRATOR_ERROR}{str(e)}")
                    responses.append(f"{Constants.ORCHESTRATOR_ERROR} {str(e)}")

        except Exception as e:
            print(f"{Constants.ORCHESTRATOR_ERROR_SEQUENTIAL_PROCESSING} {str(e)}")

        return responses

    async def call_llm_async(self, prompt: str, ai_arg: dict) -> str:
        try:
            model_name = ai_arg.get('model', 'gemini-2.0-flash-exp')

            parts = [types.Part.from_text(text=prompt)]
            messages = [{"role": "user", "parts": parts}]

            response = await self.client.aio.models.generate_content(
                model=model_name,
                contents=messages,
                config=self.config
            )

            print(f"{model_name} Completed")
            return self._extract_text_from_response(response)
        except Exception as e:
            print(f"LLM call error: {str(e)}")
            return f"{Constants.ORCHESTRATOR_ERROR_OCCURRED} {str(e)}"

    async def call_llm_async_stream_sequential(self, prompt: str, ai_arg: dict) -> str:
        try:
            model_name = ai_arg.get('model', 'gemini-2.0-flash-exp')

            parts = [types.Part.from_text(text=prompt)]
            messages = [{"role": "user", "parts": parts}]

            response_coroutine = self.client.aio.models.generate_content_stream(
                model=model_name,
                contents=messages,
                config=self.config
            )

            response = await response_coroutine
            full_response = await self.dispatch_response(response, self.stream)
            print(f"Sequential Worker ({model_name}) completed")
            return full_response
        except Exception as e:
            print(f"Sequential streaming LLM call error: {str(e)}")
            return f"{Constants.ORCHESTRATOR_ERROR_OCCURRED} {str(e)}"

    def _clean_json_string(self, json_str):
        json_str = json_str.replace('```json', '').replace('```', '')
        json_str = json_str.replace('{{', '{').replace('}}', '}')
        json_str = re.sub(r'//.*', '', json_str)
        json_str = json_str.strip()
        return json_str

    def get_worker_prompt(self, user_query, task, description):
        return self.worker_prompt.format(
            user_query=user_query,
            task=task,
            description=description
        )

    def get_aggregator_prompt(self, user_query):
        return self.aggregator_prompt.format(
            user_query=user_query
        )

    def set_force_stop(self, force_stop):
        self.force_stop = force_stop

    def finish_run(self, model, finish_reason, stream):
        end_time = time.time()
        elapsed_time = end_time - self.start_time
        self.response_finished_signal.emit(model, finish_reason, elapsed_time, stream)
