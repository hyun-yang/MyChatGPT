import tempfile
from functools import partial

from PyQt6.QtCore import Qt, pyqtSignal, QFile, QTextStream
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QSizePolicy, QScrollArea, QSplitter, \
    QTabWidget, QGroupBox, QFormLayout, QLabel, QComboBox, QFileDialog, QListWidget, QMessageBox

from chat.view.ChatWidget import ChatWidget
from custom.CheckComboBox import CheckComboBox
from custom.CheckDoubleSpinBox import CheckDoubleSpinBox
from custom.PromptTextEdit import PromptTextEdit
from tts.view.TTSHistory import TTSHistory
from tts.view.TTSWidget import TTSWidget
from util.ChatType import ChatType
from util.Constants import AIProviderName, Constants, UI, MODEL_MESSAGE
from util.SettingsManager import SettingsManager
from util.Utility import Utility


class TTSView(QWidget):
    submitted_signal = pyqtSignal(str)
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

        # Connect the rangeChanged signal
        self.ai_answer_scroll_area.verticalScrollBar().rangeChanged.connect(self.adjust_scroll_bar)

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
        self.prompt_text.setPlaceholderText(UI.TTS_PROMPT_PLACEHOLDER)
        self.prompt_text.submitted_signal.connect(self.handle_submitted_signal)

        prompt_layout = QVBoxLayout()
        prompt_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        prompt_layout.addWidget(self.prompt_text)
        prompt_layout.setSpacing(0)
        prompt_layout.setContentsMargins(0, 0, 0, 0)

        self.prompt_widget = QWidget()
        self.prompt_widget.setLayout(prompt_layout)
        self.prompt_widget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)

        tts_layout = QVBoxLayout()

        tts_layout.addWidget(self.top_widget)
        tts_layout.addWidget(self.ai_answer_scroll_area)
        tts_layout.addWidget(self.stop_widget)
        tts_layout.addWidget(self.prompt_widget)

        ttsWidget = QWidget()
        ttsWidget.setLayout(tts_layout)

        config_layout = QVBoxLayout()

        self.config_tabs = QTabWidget()
        tts_icon = QIcon(Utility.get_icon_path('ico', 'script-export.png'))
        self.config_tabs.addTab(self.create_parameters_tab(), tts_icon, UI.TTS)
        self.config_tabs.addTab(self.create_ttsdb_tab(), tts_icon, UI.TTS_LIST)

        config_layout.addWidget(self.config_tabs)

        configWidget = QWidget()
        configWidget.setLayout(config_layout)

        mainWidget = QSplitter(Qt.Orientation.Horizontal)
        mainWidget.addWidget(configWidget)
        mainWidget.addWidget(ttsWidget)
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

    def create_ttsdb_tab(self):
        layoutWidget = QWidget()
        layout = QVBoxLayout()

        self._tts_history = TTSHistory(self.model)

        layout.addWidget(self._tts_history)

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

        voiceComboBox = CheckComboBox()
        voiceComboBox.setObjectName(f"{name}_voiceComboBox")
        voiceComboBox.combo_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        voiceComboBox.combo_box.addItems(Constants.TTS_VOICE_LIST)
        voiceComboBox.combo_box.setCurrentText(
            Utility.get_settings_value(section=f"{name}_TTS_Parameter", prop="voice", default="alloy", save=True))
        voiceComboBox.combo_box.currentTextChanged.connect(lambda value: self.voice_changed(value, name))
        paramLayout.addRow('Voice', voiceComboBox)

        response_formatComboBox = CheckComboBox()
        response_formatComboBox.setObjectName(f"{name}_response_formatComboBox")
        response_formatComboBox.combo_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        response_formatComboBox.combo_box.addItems(Constants.TTS_OUTPUT_FORMAT_LIST)
        response_formatComboBox.combo_box.setCurrentText(
            Utility.get_settings_value(section=f"{name}_TTS_Parameter", prop="response_format", default="txt",
                                       save=True))
        response_formatComboBox.combo_box.currentTextChanged.connect(
            lambda value: self.response_format_changed(value, name))
        paramLayout.addRow('Output Format', response_formatComboBox)

        speedSpinBox = CheckDoubleSpinBox()
        speedSpinBox.setObjectName(f"{name}_speedSpinBox")
        speedSpinBox.spin_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        speedSpinBox.spin_box.setRange(-5, 5)
        speedSpinBox.spin_box.setAccelerated(True)
        speedSpinBox.spin_box.setSingleStep(0.5)
        speedSpinBox.spin_box.setValue(
            float(
                Utility.get_settings_value(section=f"{name}_TTS_Parameter", prop="speed",
                                           default="1", save=True)))
        speedSpinBox.valueChanged.connect(lambda value: self.speed_changed(value, name))
        paramLayout.addRow('Speed', speedSpinBox)

        groupParam.setLayout(paramLayout)
        layoutMain.addWidget(groupParam)

        # Add QListWidget to show selected image list
        fileListGroup = QGroupBox(f"{name} TTS List")
        fileListLayout = QVBoxLayout()
        fileListGroup.setLayout(fileListLayout)

        # Add QListWidget to show selected image list
        fileListWidget = QListWidget()
        fileListWidget.setObjectName(f"{name}_TTSList")
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

        filetype = Utility.get_settings_value(section=f"{name}_TTS_Parameter", prop="filetype", default="txt",
                                              save=True)
        selectButton.clicked.connect(partial(self.select_text_file, name, filetype))
        deleteButton.clicked.connect(partial(self.delete_file_list, name))
        submitButton.clicked.connect(partial(self.submit_file, self._current_llm))

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
            modelList.addItems(Constants.TTS_MODEL_LIST)
            current_model = Utility.get_settings_value(section=f"{name}_TTS_Parameter", prop="tts_model",
                                                       default="tts-1", save=True)
            modelList.setCurrentText(current_model)
            modelList.currentTextChanged.connect(lambda current_text: self.model_list_changed(current_text, name))
        else:
            raise ValueError(MODEL_MESSAGE.MODEL_UNSUPPORTED_TYPE)

    def select_text_file(self, llm, filetype):
        fileListWidget = self.findChild(QListWidget, f"{llm}_TTSList")
        selected_file = self.show_select_file_dialog(filetype)
        if selected_file and Utility.is_over_4k_limit(selected_file):
            fileListWidget.clear()
            fileListWidget.addItem(selected_file)
            self.update_submit_status(llm)
        else:
            QMessageBox.information(self, UI.TTS_CHARACTER_LIMIT_TITLE,
                                    UI.TTS_CHARACTER_LIMIT_INFO_MESSAGE,
                                    QMessageBox.StandardButton.Ok)

    def show_select_file_dialog(self, filetype):
        file_filter = None
        if filetype == "txt":
            file_filter = UI.TEXT_FILTER
        elif filetype == "pdf":
            file_filter = UI.PDF_FILTER
        elif filetype == "docx":
            file_filter = UI.WORD_FILTER
        else:
            raise ValueError(UI.UNSUPPORTED_FILE_TYPE)

        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        file_dialog.setNameFilter(file_filter)

        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            return selected_files[0]
        else:
            return None

    def delete_file_list(self, llm):
        fileListWidget = self.findChild(QListWidget, f"{llm}_TTSList")
        for item in fileListWidget.selectedItems():
            fileListWidget.takeItem(fileListWidget.row(item))
        self.update_submit_status(llm)

    def submit_file(self, llm):
        fileListWidget = self.findChild(QListWidget, f"{llm}_TTSList")
        items = [fileListWidget.item(i) for i in range(fileListWidget.count())]
        file_item = items[0]
        if file_item:
            file_name = file_item.text()
            file = QFile(file_name)
            if file.open(QFile.OpenModeFlag.ReadOnly | QFile.OpenModeFlag.Text):
                stream = QTextStream(file)
                file_content = stream.readAll()
                file.close()
                self.submitted_signal.emit(file_content)
        else:
            return None

    def update_submit_status(self, llm):
        fileListWidget = self.findChild(QListWidget,
                                        f"{llm}_TTSList")
        submitButton = self.findChild(QPushButton,
                                      f"{llm}_SubmitButton")
        submitButton.setEnabled(bool(fileListWidget.count()))

    def on_item_selection_changed(self, llm):
        fileListWidget = self.findChild(QListWidget,
                                        f"{llm}_TTSList")
        deleteButton = self.findChild(QPushButton,
                                      f"{llm}_DeleteButton")
        deleteButton.setEnabled(bool(fileListWidget.selectedItems()))

        submitButton = self.findChild(QPushButton,
                                      f"{llm}_SubmitButton")
        submitButton.setEnabled(bool(fileListWidget.count()))

    def create_args(self, text, llm):
        method_name = f'create_args_{llm.lower()}'
        method = getattr(self, method_name, None)
        if callable(method):
            return method(text, llm)
        else:
            raise ValueError(f'{UI.METHOD} {method_name} {UI.NOT_FOUND}')

    def create_args_openai(self, text, llm):
        api_key = self._settings.value(f'AI_Provider/{llm}')
        model = self.findChild(QComboBox, f'{llm}_ModelList').currentText()

        voiceComboBox = self.findChild(CheckComboBox,
                                       f'{self._current_llm}_voiceComboBox').combo_box
        voice = voiceComboBox.currentText() if voiceComboBox.isEnabled() else None

        response_formatComboBox = self.findChild(CheckComboBox,
                                                 f'{self._current_llm}_response_formatComboBox').combo_box
        self.response_format = response_formatComboBox.currentText() if response_formatComboBox.isEnabled() else None

        speedSpinBox = self.findChild(CheckDoubleSpinBox,
                                      f'{self._current_llm}_speedSpinBox').spin_box
        speed = speedSpinBox.value() if speedSpinBox.isEnabled() else None

        ai_arg = {
            'model': model,
            'voice': voice,
            'speed': speed,
            'response_format': self.response_format,
            'input': text,
        }

        args = {
            'api_key': api_key,
            'ai_arg': ai_arg,
            'stream': False,
        }

        return args

    def get_last_ai_widget(self) -> TTSWidget | None:
        layout_item = self.result_widget.layout().itemAt(self.result_widget.layout().count() - 1)
        if layout_item:
            last_ai_widget = layout_item.widget()
            if last_ai_widget.get_chat_type() == ChatType.AI:
                return last_ai_widget
        else:
            return None

    def add_user_question(self, chatType, text):
        user_question = ChatWidget(chatType, text)
        self.result_layout.addWidget(user_question)

    def add_ai_answer(self, chatType, tts_data, tts_response_format):
        with tempfile.NamedTemporaryFile(delete=False, suffix='.' + tts_response_format) as temp_file:
            temp_file.write(tts_data)
            temp_file.flush()
            temp_file_name = temp_file.name

        ai_answer = TTSWidget(chatType, temp_file_name)
        self.result_layout.addWidget(ai_answer)

    def update_ui_submit(self, chatType, text):
        self.add_user_question(chatType, text)
        self.stop_widget.setVisible(True)

    def update_ui(self, result):
        temp_file_name = Utility.create_temp_file(result, self.response_format, False)
        ai_answer = TTSWidget(ChatType.AI, temp_file_name)
        self.result_layout.addWidget(ai_answer)

    def update_ui_finish(self, model, finish_reason, elapsed_time, stream):
        ttsWidget = self.get_last_ai_widget()
        self.stop_widget.setVisible(False)
        if ttsWidget and ttsWidget.get_chat_type() == ChatType.AI:
            ttsWidget.set_model_name(
                Constants.MODEL_PREFIX + model + " | Response Time : " + format(elapsed_time, ".2f"))

    def model_list_changed(self, model, llm):
        self._settings.setValue(f"{llm}_TTS_Parameter/tts_model", model)

    def voice_changed(self, value, name):
        self._settings.setValue(f"{name}_TTS_Parameter/voice", value)

    def speed_changed(self, value, name):
        self._settings.setValue(f"{name}_TTS_Parameter/speed", value)

    def response_format_changed(self, value, name):
        self._settings.setValue(f"{name}_TTS_Parameter/response_format", value)

    def handle_submitted_signal(self, text):
        if text:
            self.submitted_signal.emit(text)

    def start_chat(self):
        self.prompt_text.clear()
        self.prompt_text.setEnabled(False)

    def finish_chat(self):
        self.prompt_text.setEnabled(True)
        self.prompt_text.setFocus()

        fileListWidget = self.findChild(QListWidget, f"{self._current_llm}_TTSList")
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
                if isinstance(widget, TTSWidget):
                    widget.audio_player.stop_audio()
                if widget is not None:
                    widget.deleteLater()

    @property
    def tts_history(self):
        return self._tts_history
