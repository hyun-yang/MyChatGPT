import io
from functools import partial

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QSizePolicy, QScrollArea, QSplitter, \
    QTabWidget, QGroupBox, QFormLayout, QLabel, QComboBox, QCheckBox, QFileDialog, QListWidget, QMessageBox

from chat.view.ChatWidget import ChatWidget
from custom.CheckComboBox import CheckComboBox
from custom.CheckDoubleSpinBox import CheckDoubleSpinBox
from custom.CheckLineEdit import CheckLineEdit
from custom.PromptTextEdit import PromptTextEdit
from stt.view.STTHistory import STTHistory
from stt.view.STTWidget import STTWidget
from util.ChatType import ChatType
from util.Constants import AIProviderName, Constants, UI, MODEL_MESSAGE
from util.SettingsManager import SettingsManager
from util.Utility import Utility


class STTView(QWidget):
    submitted_signal = pyqtSignal(str, str)
    stop_signal = pyqtSignal()
    current_llm_signal = pyqtSignal(str)

    def __init__(self, model):
        super().__init__()
        self.model = model
        self._settings = SettingsManager.get_settings()
        self._current_llm = AIProviderName.OPENAI.value

        self.found_text_positions = []

        self.initialize_ui()

    def initialize_ui(self):
        # Top layout
        self.top_layout = QVBoxLayout()
        self.top_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.clear_all_button = QPushButton(QIcon(Utility.get_icon_path('ico', 'bin.png')), UI.CLEAR_ALL)
        self.clear_all_button.clicked.connect(lambda: self.clear_all())

        self.search_text = PromptTextEdit()
        self.search_text.submitted_signal.connect(self.search)
        self.search_text.setPlaceholderText(UI.SEARCH_PROMPT_PLACEHOLDER)

        self.search_text.setFixedHeight(self.clear_all_button.sizeHint().height())
        self.search_text.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.search_result = QLabel()

        # Create navigation buttons
        self.prev_button = QPushButton(QIcon(Utility.get_icon_path('ico', 'arrow-180.png')), '')
        self.prev_button.clicked.connect(self.scroll_to_previous_match_widget)
        self.next_button = QPushButton(QIcon(Utility.get_icon_path('ico', 'arrow.png')), '')
        self.next_button.clicked.connect(self.scroll_to_next_match_widget)

        # Create a horizontal layout and add the buttons
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.search_text)
        button_layout.addWidget(self.search_result)
        button_layout.addWidget(self.prev_button)
        button_layout.addWidget(self.next_button)
        button_layout.addWidget(self.clear_all_button)
        button_layout.setAlignment(Qt.AlignmentFlag.AlignRight)

        # Add the button layout to the result layout
        self.top_layout.addLayout(button_layout)

        self.top_widget = QWidget()
        self.top_widget.setLayout(self.top_layout)
        self.top_widget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)

        # Result View
        self.result_layout = QVBoxLayout()
        self.result_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.result_layout.setSpacing(0)
        self.result_layout.setContentsMargins(0, 0, 0, 0)

        self.result_widget = QWidget()
        self.result_widget.setLayout(self.result_layout)

        # Scroll Area
        self.ai_answer_scroll_area = QScrollArea()
        self.ai_answer_scroll_area.setWidgetResizable(True)
        self.ai_answer_scroll_area.setWidget(self.result_widget)

        # Stop Button
        self.stop_button = QPushButton(QIcon(Utility.get_icon_path('ico', 'minus-circle.png')), UI.STOP)
        self.stop_button.clicked.connect(self.force_stop)

        stop_layout = QHBoxLayout()
        stop_layout.setContentsMargins(0, 0, 0, 0)
        stop_layout.setSpacing(0)
        stop_layout.addWidget(self.stop_button)
        stop_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.stop_widget = QWidget()
        self.stop_widget.setLayout(stop_layout)
        self.stop_widget.setVisible(False)

        # Prompt View
        self.prompt_text = PromptTextEdit()
        self.prompt_text.setPlaceholderText(UI.VISION_PROMPT_PLACEHOLDER)
        self.prompt_text.submitted_signal.connect(partial(self.submit_file, self._current_llm))

        prompt_layout = QVBoxLayout()
        prompt_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        prompt_layout.addWidget(self.prompt_text)
        prompt_layout.setSpacing(0)
        prompt_layout.setContentsMargins(0, 0, 0, 0)

        self.prompt_widget = QWidget()
        self.prompt_widget.setLayout(prompt_layout)
        self.prompt_widget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)

        chat_layout = QVBoxLayout()
        chat_layout.addWidget(self.top_widget)
        chat_layout.addWidget(self.ai_answer_scroll_area)
        chat_layout.addWidget(self.stop_widget)
        chat_layout.addWidget(self.prompt_widget)

        chatWidget = QWidget()
        chatWidget.setLayout(chat_layout)

        config_layout = QVBoxLayout()

        self.config_tabs = QTabWidget()
        stt_icon = QIcon(Utility.get_icon_path('ico', 'microphone--pencil.png'))
        self.config_tabs.addTab(self.create_parameters_tab(), stt_icon, UI.STT)
        self.config_tabs.addTab(self.create_sttdb_tab(), stt_icon, UI.STT_LIST)

        config_layout.addWidget(self.config_tabs)

        configWidget = QWidget()
        configWidget.setLayout(config_layout)

        mainWidget = QSplitter(Qt.Orientation.Horizontal)
        mainWidget.addWidget(configWidget)
        mainWidget.addWidget(chatWidget)
        mainWidget.setSizes([UI.QSPLITTER_LEFT_WIDTH, UI.QSPLITTER_RIGHT_WIDTH])
        mainWidget.setHandleWidth(UI.QSPLITTER_HANDLEWIDTH)

        main_layout = QVBoxLayout()
        main_layout.addWidget(mainWidget)

        self.setLayout(main_layout)

    def reset_search_bar(self):
        self.found_text_positions = []
        self.search_result.clear()
        self.current_position_index = -1
        self.update_navigation_buttons()

    def search(self, text: str):
        if text and text.strip() and len(text) >= 2:
            self.found_text_positions = []
            self.current_position_index = -1

            search_text_lower = text.lower()

            for i in range(self.result_layout.count()):
                current_widget = self.result_layout.itemAt(i).widget()
                if isinstance(current_widget, ChatWidget):
                    current_text = current_widget.get_original_text()
                    current_text_lower = current_text.lower()

                    if search_text_lower in current_text_lower:
                        self.found_text_positions.append(i)
                        highlight_text = current_widget.highlight_search_text(current_text, text)
                        current_widget.apply_highlight(highlight_text)
                    else:
                        current_widget.show_original_text()

            if self.found_text_positions:
                self.current_position_index = 0
                self.scroll_to_match_widget(self.found_text_positions[self.current_position_index])
        if len(self.found_text_positions) > 0:
            self.search_result.setText(f'{len(self.found_text_positions)} {UI.FOUNDS}')
        else:
            self.search_result.clear()
        self.update_navigation_buttons()
        self.search_text.clear()

    def scroll_to_match_widget(self, position):
        self.ai_answer_scroll_area.ensureWidgetVisible(self.result_layout.itemAt(position).widget())

    def scroll_to_previous_match_widget(self):
        if len(self.found_text_positions) > 0 and self.current_position_index > 0:
            self.current_position_index -= 1
            self.scroll_to_match_widget(self.found_text_positions[self.current_position_index])
            self.update_navigation_buttons()

    def scroll_to_next_match_widget(self):
        if len(self.found_text_positions) > 0 and self.current_position_index < len(self.found_text_positions) - 1:
            self.current_position_index += 1
            self.scroll_to_match_widget(self.found_text_positions[self.current_position_index])
            self.update_navigation_buttons()

    def update_navigation_buttons(self):
        self.prev_button.setEnabled(self.current_position_index > 0)
        self.next_button.setEnabled(self.current_position_index < len(self.found_text_positions) - 1)

    def adjust_scroll_bar(self, min_val, max_val):
        self.ai_answer_scroll_area.verticalScrollBar().setSliderPosition(max_val)

    def create_sttdb_tab(self):
        layoutWidget = QWidget()
        layout = QVBoxLayout()

        self._stt_history = STTHistory(self.model)

        layout.addWidget(self._stt_history)

        layoutWidget.setLayout(layout)
        return layoutWidget

    def create_parameters_tab(self):
        layoutWidget = QWidget()
        layout = QVBoxLayout()

        # Tabs for LLM
        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_openai_tabcontent(AIProviderName.OPENAI.value), AIProviderName.OPENAI.value)
        self.tabs.currentChanged.connect(self.on_tab_change)
        layout.addWidget(self.tabs)

        layoutWidget.setLayout(layout)
        return layoutWidget

    def create_openai_tabcontent(self, name):
        tabWidget = QWidget()
        tabWidget.setObjectName(name)
        layoutMain = QVBoxLayout()

        groupModel = QGroupBox(f"{name} Model")
        modelLayout = QFormLayout()
        modelLabel = QLabel(f"{name} Model List")
        modelList = QComboBox()
        modelList.setObjectName(f"{name}_ModelList")
        modelList.clear()

        self.set_model_list(modelList, name)

        modelLayout.addRow(modelLabel)
        modelLayout.addRow(modelList)
        groupModel.setLayout(modelLayout)
        layoutMain.addWidget(groupModel)

        # Parameters Group
        groupParam = QGroupBox(f"{name} Parameters")
        paramLayout = QFormLayout()

        # language : Supplying the input language in ISO-639-1 format will improve accuracy and latency.
        languageComboBox = CheckComboBox()
        languageComboBox.setObjectName(f"{name}_languageComboBox")
        languageComboBox.combo_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.languages = Constants.STT_LANGUAGE_LIST
        languageComboBox.combo_box.addItems(self.languages.keys())
        languageComboBox.combo_box.setCurrentText(
            Utility.get_settings_value(section=f"{name}_STT_Parameter", prop="language",
                                       default="English", save=True))
        languageComboBox.currentTextChanged.connect(lambda value: self.language_changed(value, name))
        paramLayout.addRow('Language', languageComboBox)

        temperatureSpinBox = CheckDoubleSpinBox()
        temperatureSpinBox.setObjectName(f"{name}_temperatureSpinBox")
        temperatureSpinBox.spin_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        temperatureSpinBox.spin_box.setRange(0, 1)
        temperatureSpinBox.spin_box.setAccelerated(True)
        temperatureSpinBox.spin_box.setSingleStep(0.1)
        temperatureSpinBox.spin_box.setValue(
            float(Utility.get_settings_value(section=f"{name}_STT_Parameter", prop="temperature", default="0",
                                             save=True)))
        temperatureSpinBox.valueChanged.connect(lambda value: self.temperature_changed(value, name))
        paramLayout.addRow('Temperature', temperatureSpinBox)

        response_formatComboBox = CheckComboBox()
        response_formatComboBox.setObjectName(f"{name}_response_formatComboBox")
        response_formatComboBox.combo_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        response_formatComboBox.combo_box.addItems(Constants.STT_RESPONSE_FORMAT_LIST)
        response_formatComboBox.combo_box.setCurrentText(
            Utility.get_settings_value(section=f"{name}_STT_Parameter", prop="response_format", default="text",
                                       save=True))
        response_formatComboBox.combo_box.currentTextChanged.connect(
            lambda value: self.response_format_changed(value, name))
        paramLayout.addRow('Response Format', response_formatComboBox)

        # Either or both of these options are supported: word, or segment
        timestampLineEdit = CheckLineEdit()
        timestampLineEdit.setObjectName(f"{name}_timestampLineEdit")
        timestampLineEdit.line_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        timestampLineEdit.line_edit.setPlaceholderText('segment or word or segment, word')
        timestampLineEdit.line_edit.setText(
            Utility.get_settings_value(section=f"{name}_STT_Parameter", prop="timestamp",
                                       default="segment", save=True))
        timestampLineEdit.textChanged.connect(lambda value: self.timestamp_changed(value, name))
        paramLayout.addRow('Timestamp', timestampLineEdit)

        groupParam.setLayout(paramLayout)
        layoutMain.addWidget(groupParam)

        # Option, translation
        optionGroup = QGroupBox(f"{name} Options")
        optionLayout = QVBoxLayout()

        translation = Utility.get_settings_value(section=f"{name}_STT_Parameter", prop="translation", default="True",
                                                 save=True)
        translationCheckbox = QCheckBox("Translation")
        translationCheckbox.setObjectName(f"{name}_translationCheckbox")
        translationCheckbox.setChecked(translation == "True")
        translationCheckbox.toggled.connect(lambda value: self.translation_changed(value, name))

        optionLayout.addWidget(translationCheckbox)
        optionGroup.setLayout(optionLayout)
        layoutMain.addWidget(optionGroup)

        # Add QListWidget to show selected image list
        fileListGroup = QGroupBox(f"{name} STT List")
        fileListLayout = QVBoxLayout()
        fileListGroup.setLayout(fileListLayout)

        # Add QListWidget to show selected image list
        fileListWidget = QListWidget()
        fileListWidget.setObjectName(f"{name}_STTList")
        fileListLayout.addWidget(fileListWidget)

        # Add buttons
        buttonLayout = QHBoxLayout()
        selectButton = QPushButton(QIcon(Utility.get_icon_path('ico', 'folder-open-image.png')), "File")
        selectButton.setObjectName(f"{name}_SelectButton")

        deleteButton = QPushButton(QIcon(Utility.get_icon_path('ico', 'folder--minus.png')), "Remove")
        deleteButton.setObjectName(f"{name}_DeleteButton")
        deleteButton.setEnabled(False)

        buttonLayout.addWidget(selectButton)
        buttonLayout.addWidget(deleteButton)

        fileListLayout.addLayout(buttonLayout)

        submitLayout = QHBoxLayout()
        submitButton = QPushButton(QIcon(Utility.get_icon_path('ico', 'inbox-document-text.png')), "Submit")
        submitButton.setObjectName(f"{name}_SubmitButton")
        submitButton.setEnabled(False)
        submitLayout.addWidget(submitButton)

        fileListLayout.addLayout(submitLayout)

        selectButton.clicked.connect(partial(self.select_audio_file, name))
        deleteButton.clicked.connect(partial(self.delete_file_list, name))
        submitButton.clicked.connect(partial(self.submit_file, name, None))

        fileListWidget.itemSelectionChanged.connect(partial(self.on_item_selection_changed, name))

        layoutMain.addWidget(fileListGroup)

        tabWidget.setLayout(layoutMain)

        return tabWidget

    def on_tab_change(self, index):
        self._current_llm = self.tabs.tabText(index)
        self._settings.setValue('AI_Provider/llm', self._current_llm)
        self.current_llm_signal.emit(self._current_llm)

    def set_default_tab(self, name):
        index = self.tabs.indexOf(self.tabs.findChild(QWidget, name))
        if index != -1:
            self.tabs.setCurrentIndex(index)

    def set_model_list(self, modelList, name):
        if name == AIProviderName.OPENAI.value:
            modelList.addItems(Constants.STT_MODEL_LIST)
            current_model = Utility.get_settings_value(section=f"{name}_STT_Parameter", prop="stt_model",
                                                       default="whisper-1", save=True)
            modelList.setCurrentText(current_model)
            modelList.currentTextChanged.connect(lambda current_text: self.model_list_changed(current_text, name))
        else:
            raise ValueError(MODEL_MESSAGE.MODEL_UNSUPPORTED_TYPE)

    def select_audio_file(self, llm):
        fileListWidget = self.findChild(QListWidget, f"{llm}_STTList")
        selected_file = self.show_audio_file_dialog()
        if selected_file:
            fileListWidget.clear()
            fileListWidget.addItem(selected_file)
            self.update_submit_status(llm)

    def show_audio_file_dialog(self):
        file_filter = UI.STT_FILTER

        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        file_dialog.setNameFilter(file_filter)

        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            return selected_files[0]
        else:
            return None

    def delete_file_list(self, llm):
        fileListWidget = self.findChild(QListWidget, f"{llm}_STTList")
        for item in fileListWidget.selectedItems():
            fileListWidget.takeItem(fileListWidget.row(item))
        self.update_submit_status(llm)

    def submit_file(self, llm, text):
        if text is None:
            text = self.prompt_text.toPlainText()
        fileListWidget = self.findChild(QListWidget, f"{llm}_STTList")
        if fileListWidget.count():
            items = [fileListWidget.item(i) for i in range(fileListWidget.count())]
            file_item = items[0]
            if file_item:
                file_name = file_item.text()
                self.submitted_signal.emit(text, file_name)
            else:
                return None
        else:
            QMessageBox.warning(self, UI.WARNING_TITLE, UI.WARNING_TITLE_SELECT_FILE_MESSAGE)

    def update_submit_status(self, llm):
        fileListWidget = self.findChild(QListWidget,
                                        f"{llm}_STTList")
        submitButton = self.findChild(QPushButton,
                                      f"{llm}_SubmitButton")
        submitButton.setEnabled(bool(fileListWidget.count()))

    def on_item_selection_changed(self, llm):
        fileListWidget = self.findChild(QListWidget,
                                        f"{llm}_STTList")
        deleteButton = self.findChild(QPushButton,
                                      f"{llm}_DeleteButton")
        deleteButton.setEnabled(bool(fileListWidget.selectedItems()))

        submitButton = self.findChild(QPushButton,
                                      f"{llm}_SubmitButton")
        submitButton.setEnabled(bool(fileListWidget.count()))

    def create_args(self, llm, text, filepath):
        method_name = f'create_args_{llm.lower()}'
        method = getattr(self, method_name, None)
        if callable(method):
            return method(llm, text, filepath)
        else:
            raise ValueError(f'{UI.METHOD} {method_name} {UI.NOT_FOUND}')

    def create_args_openai(self, llm, text, filepath):
        api_key = self._settings.value(f'AI_Provider/{llm}')
        model = self.findChild(QComboBox, f'{llm}_ModelList').currentText()

        translation = self.findChild(QCheckBox, f'{llm}_translationCheckbox').isChecked()

        languageComboBox = self.findChild(CheckComboBox,
                                          f'{llm}_languageComboBox').combo_box
        language = self.languages[languageComboBox.currentText()] if languageComboBox.isEnabled() else None

        temperatureSpinBox = self.findChild(CheckDoubleSpinBox,
                                            f'{llm}_temperatureSpinBox').spin_box
        temperature = temperatureSpinBox.value() if temperatureSpinBox.isEnabled() else None

        response_formatComboBox = self.findChild(CheckComboBox,
                                                 f'{self._current_llm}_response_formatComboBox').combo_box
        response_format = response_formatComboBox.currentText() if response_formatComboBox.isEnabled() else None

        timestampLineEdit = self.findChild(CheckLineEdit,
                                           f'{self._current_llm}_timestampLineEdit')
        timestamp_value = timestampLineEdit.line_edit.text() if timestampLineEdit.line_edit.isEnabled() else None
        if timestamp_value:
            timestamp = timestamp_value.strip().split(',')
        else:
            timestamp = None

        try:
            with open(filepath, UI.FILE_READ_IN_BINARY_MODE) as file:
                content = file.read()
                audio_file = io.BytesIO(content)
                audio_file.name = filepath
        except FileNotFoundError:
            print(UI.FAILED_TO_OPEN_FILE)
            return

        ai_arg = {
            'model': model,
            'prompt': text,
            'temperature': temperature,
            'response_format': response_format,
            'file': audio_file,
        }

        if not translation and language:
            ai_arg['language'] = language

        if not translation and timestamp:
            ai_arg['timestamp_granularities'] = timestamp

        args = {
            'api_key': api_key,
            'ai_arg': ai_arg,
            'translation': translation,
            'stream': False
        }
        return args

    def get_last_ai_widget(self) -> ChatWidget | None:
        layout_item = self.result_widget.layout().itemAt(self.result_widget.layout().count() - 1)
        if layout_item:
            last_ai_widget = layout_item.widget()
            if last_ai_widget.get_chat_type() == ChatType.AI:
                return last_ai_widget
        else:
            return None

    def add_user_question(self, chatType, text, filepath):
        user_question = STTWidget(chatType, text, filepath)
        self.result_layout.addWidget(user_question)

    def add_ai_answer(self, chatType, text, model):
        ai_answer = ChatWidget.with_model(chatType, text, model)
        self.result_layout.addWidget(ai_answer)

    def update_ui_submit(self, chatType, text, filepath):
        self.ai_answer_scroll_area.verticalScrollBar().rangeChanged.connect(self.adjust_scroll_bar)
        self.add_user_question(chatType, text, filepath)
        self.stop_widget.setVisible(True)

    def update_ui(self, result):
        ai_answer = ChatWidget(ChatType.AI, result)
        self.result_layout.addWidget(ai_answer)

    def update_ui_finish(self, model, finish_reason, elapsed_time, stream):
        self.ai_answer_scroll_area.verticalScrollBar().rangeChanged.disconnect()
        chatWidget = self.get_last_ai_widget()
        if stream:
            if chatWidget:
                chatWidget.apply_style()
                self.stop_widget.setVisible(False)
        else:
            self.stop_widget.setVisible(False)

        if chatWidget and chatWidget.get_chat_type() == ChatType.AI:
            chatWidget.set_model_name(
                Constants.MODEL_PREFIX + model + Constants.RESPONSE_TIME + format(elapsed_time, ".2f"))

    def model_list_changed(self, model, llm):
        self._settings.setValue(f"{llm}_STT_Parameter/stt_model", model)

    def response_format_changed(self, value, name):
        self._settings.setValue(f"{name}_STT_Parameter/response_format", value)

    def timestamp_changed(self, value, name):
        self._settings.setValue(f"{name}_STT_Parameter/timestamp", value)

    def translation_changed(self, checked, name):
        if checked:
            self._settings.setValue(f"{name}_STT_Parameter/translation", 'True')
        else:
            self._settings.setValue(f"{name}_STT_Parameter/translation", 'False')

    def temperature_changed(self, value, name):
        self._settings.setValue(f"{name}_STT_Parameter/temperature", value)

    def language_changed(self, value, name):
        self._settings.setValue(f"{name}_STT_Parameter/language", value)

    def start_chat(self):
        self.prompt_text.clear()
        self.prompt_text.setEnabled(False)

    def finish_chat(self):
        self.prompt_text.setEnabled(True)
        self.prompt_text.setFocus()

        fileListWidget = self.findChild(QListWidget, f"{self._current_llm}_STTList")
        fileListWidget.clear()

        submitButton = self.findChild(QPushButton, f"{self._current_llm}_SubmitButton")
        submitButton.setEnabled(False)

    def force_stop(self):
        self.stop_signal.emit()
        self.stop_widget.setVisible(False)

    def clear_all(self):
        target_layout = self.result_layout
        if target_layout is not None:
            while target_layout.count():
                item = target_layout.takeAt(0)
                widget = item.widget()
                if isinstance(widget, STTWidget):
                    widget.audio_player.stop_audio()
                if widget is not None:
                    widget.deleteLater()

    @property
    def stt_history(self):
        return self._stt_history

    @property
    def stt_model(self):
        return self.findChild(QComboBox, f'{self._current_llm}_ModelList').currentText()

    @property
    def stt_response_format(self):
        return self.findChild(CheckComboBox, f'{self._current_llm}_response_formatComboBox').combo_box.currentText()
