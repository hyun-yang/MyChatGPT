from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QSizePolicy, QSplitter, QComboBox, QLabel, QTabWidget, \
    QGroupBox, QFormLayout, QCheckBox, QPushButton, QHBoxLayout, QApplication, QTextEdit

from chat.view.ChatHistory import ChatHistory
from chat.view.ChatPromptListWidget import ChatPromptListWidget
from chat.view.ChatWidget import ChatWidget
from custom.CheckDoubleSpinBox import CheckDoubleSpinBox
from custom.CheckLineEdit import CheckLineEdit
from custom.CheckSpinBox import CheckSpinBox
from custom.PromptTextEdit import PromptTextEdit
from util.ChatType import ChatType
from util.Constants import AIProviderName, UI
from util.Constants import Constants
from util.SettingsManager import SettingsManager
from util.Utility import Utility


class ChatView(QWidget):
    submitted_signal = pyqtSignal(str)
    stop_signal = pyqtSignal()
    chat_llm_signal = pyqtSignal(str)
    reload_chat_detail_signal = pyqtSignal(int)

    def __init__(self, model):
        super().__init__()
        self.model = model
        self._settings = SettingsManager.get_settings()
        self._current_chat_llm = Utility.get_settings_value(section="AI_Provider", prop="llm",
                                                            default="OpenAI", save=True)
        self.found_text_positions = []

        self.initialize_ui()

    def initialize_ui(self):

        # Top layout
        self.top_layout = QVBoxLayout()
        self.top_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Create buttons
        self.clear_all_button = QPushButton(QIcon(Utility.get_icon_path('ico', 'bin.png')), UI.CLEAR_ALL)
        self.clear_all_button.clicked.connect(lambda: self.clear_all())

        self.copy_all_button = QPushButton(QIcon(Utility.get_icon_path('ico', 'cards-stack.png')), UI.COPY_ALL)
        self.copy_all_button.clicked.connect(lambda: QApplication.clipboard().setText(self.get_all_text()))

        self.reload_button = QPushButton(QIcon(Utility.get_icon_path('ico', 'cards-address.png')), UI.RELOAD_ALL)
        self.reload_button.clicked.connect(lambda: self.reload_chat_detail_signal.emit(-1))

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
        button_layout.addWidget(self.copy_all_button)
        button_layout.addWidget(self.clear_all_button)
        button_layout.addWidget(self.reload_button)
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
        self.stop_button = QPushButton(QIcon(Utility.get_icon_path('ico', 'minus-circle.png')), 'Stop')
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
        self.prompt_text.submitted_signal.connect(self.handle_submitted_signal)
        self.prompt_text.setPlaceholderText(UI.CHAT_PROMPT_PLACEHOLDER)

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
        chat_icon = QIcon(Utility.get_icon_path('ico', 'users.png'))
        self.config_tabs.addTab(self.create_parameters_tab(), chat_icon, UI.CHAT)
        self.config_tabs.addTab(self.create_chatdb_tab(), chat_icon, UI.CHAT_LIST)
        self.config_tabs.addTab(self.create_prompt_tab(), chat_icon, UI.PROMPT)

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

    def create_parameters_tab(self):
        layoutWidget = QWidget()
        layout = QVBoxLayout()

        # Tabs for LLM
        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_openai_tabcontent(AIProviderName.OPENAI.value), AIProviderName.OPENAI.value)
        self.tabs.addTab(self.create_gemini_tabcontent(AIProviderName.GEMINI.value), AIProviderName.GEMINI.value)
        self.tabs.addTab(self.create_claude_tabcontent(AIProviderName.CLAUDE.value), AIProviderName.CLAUDE.value)
        self.tabs.addTab(self.create_ollama_tabcontent(AIProviderName.OLLAMA.value), AIProviderName.OLLAMA.value)
        self.tabs.currentChanged.connect(self.on_tab_change)
        layout.addWidget(self.tabs)

        layoutWidget.setLayout(layout)
        return layoutWidget

    def on_tab_change(self, index):
        self._current_chat_llm = self.tabs.tabText(index)
        self._settings.setValue('AI_Provider/llm', self._current_chat_llm)
        self.chat_llm_signal.emit(self._current_chat_llm)

    def set_default_tab(self, name):
        index = self.tabs.indexOf(self.tabs.findChild(QWidget, name))
        if index != -1:
            self.tabs.setCurrentIndex(index)

    def on_system_change(self, name):
        current_text = self.findChild(QComboBox, f"{name}_systemList").currentText()
        system_values = Utility.get_system_value(section=f"{name}_System", prefix="system",
                                                 default="You are a helpful assistant.", length=5)
        current_system = self.findChild(QTextEdit, f"{name}_current_system")
        if current_text in system_values:
            current_system.setText(system_values[current_text])
        else:
            current_system.clear()

    def save_system_value(self, name):
        current_systemList = self.findChild(QComboBox, f"{name}_systemList")
        current_system = self.findChild(QTextEdit, f"{name}_current_system")
        selected_key = current_systemList.currentText()
        value = current_system.toPlainText()
        self._settings.setValue(f"{name}_System/{selected_key}", value)
        self.update_system_list(name, Utility.extract_number_from_end(selected_key) - 1)

    def update_system_list(self, name, index=0):
        current_systemList = self.findChild(QComboBox, f"{name}_systemList")
        system_values = Utility.get_system_value(section=f"{name}_System", prefix="system",
                                                 default="You are a helpful assistant.", length=5)
        if current_systemList:
            current_systemList.clear()
            current_systemList.addItems(system_values.keys())

        if system_values and current_systemList:
            current_systemList.setCurrentIndex(index)

    def create_ollama_tabcontent(self, name):
        tabWidget = QWidget()
        tabWidget.setObjectName(name)
        layoutMain = QVBoxLayout()

        groupSystem = self.create_system_layout(name)
        layoutMain.addWidget(groupSystem)

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

        stop_sequencesLineEdit = CheckLineEdit()
        stop_sequencesLineEdit.setObjectName(f"{name}_stop_sequencesLineEdit")
        stop_sequencesLineEdit.line_edit.setPlaceholderText('stop sequence')
        stop_sequencesLineEdit.line_edit.setText(
            Utility.get_settings_value(section=f"{name}_Model_Parameter", prop="stop",
                                       default="", save=True))
        stop_sequencesLineEdit.check_box.setChecked(True)
        stop_sequencesLineEdit.textChanged.connect(lambda value: self.stopsequences_changed(value, name))
        paramLayout.addRow('Stop Sequence', stop_sequencesLineEdit)

        num_predictSpinBox = CheckSpinBox()
        num_predictSpinBox.setObjectName(f"{name}_num_predictSpinBox")
        num_predictSpinBox.spin_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        num_predictSpinBox.spin_box.setRange(-2, 128000)
        num_predictSpinBox.spin_box.setAccelerated(True)
        num_predictSpinBox.spin_box.setSingleStep(1)
        num_predictSpinBox.spin_box.setValue(
            int(
                Utility.get_settings_value(section=f"{name}_Model_Parameter", prop="num_predict",
                                           default="2048", save=True)))
        num_predictSpinBox.check_box.setChecked(True)
        num_predictSpinBox.valueChanged.connect(lambda value: self.numpredict_changed(value, name))
        # Maximum number of tokens to predict when generating text. (Default: 128, -1 = infinite generation, -2 = fill context)
        paramLayout.addRow('Max Tokens', num_predictSpinBox)

        temperatureSpinBox = CheckDoubleSpinBox()
        temperatureSpinBox.setObjectName(f"{name}_temperatureSpinBox")
        temperatureSpinBox.spin_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        temperatureSpinBox.spin_box.setRange(0, 2)
        temperatureSpinBox.spin_box.setAccelerated(True)
        temperatureSpinBox.spin_box.setSingleStep(0.1)
        temperatureSpinBox.spin_box.setValue(
            float(Utility.get_settings_value(section=f"{name}_Model_Parameter", prop="temperature", default="0.2",
                                             save=True)))
        temperatureSpinBox.valueChanged.connect(lambda value: self.temperature_changed(value, name))
        paramLayout.addRow('Temperature', temperatureSpinBox)

        top_pSpinBox = CheckDoubleSpinBox()
        top_pSpinBox.setObjectName(f"{name}_top_pSpinBox")
        top_pSpinBox.spin_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        top_pSpinBox.spin_box.setRange(0, 1)
        top_pSpinBox.spin_box.setAccelerated(True)
        top_pSpinBox.spin_box.setSingleStep(0.1)
        top_pSpinBox.spin_box.setValue(
            float(
                Utility.get_settings_value(section=f"{name}_Model_Parameter", prop="top_p", default="0.1", save=True)))
        top_pSpinBox.check_box.setChecked(True)
        top_pSpinBox.valueChanged.connect(lambda value: self.topp_changed(value, name))
        paramLayout.addRow('Top_P', top_pSpinBox)

        top_kSpinBox = CheckSpinBox()
        top_kSpinBox.setObjectName(f"{name}_top_kSpinBox")
        top_kSpinBox.spin_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        top_kSpinBox.spin_box.setRange(0, 1000)
        top_kSpinBox.spin_box.setAccelerated(True)
        top_kSpinBox.spin_box.setSingleStep(1)
        top_kSpinBox.spin_box.setValue(
            int(
                Utility.get_settings_value(section=f"{name}_Model_Parameter", prop="top_k", default="1", save=True)))
        top_kSpinBox.check_box.setChecked(True)
        top_kSpinBox.valueChanged.connect(lambda value: self.topk_changed(value, name))
        paramLayout.addRow('Top_K', top_kSpinBox)

        frequencyPenaltySpinBox = CheckDoubleSpinBox()
        frequencyPenaltySpinBox.setObjectName(f"{name}_frequencyPenaltySpinBox")
        frequencyPenaltySpinBox.spin_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        frequencyPenaltySpinBox.spin_box.setRange(-2, 2)
        frequencyPenaltySpinBox.spin_box.setAccelerated(True)
        frequencyPenaltySpinBox.spin_box.setSingleStep(0.1)
        frequencyPenaltySpinBox.spin_box.setValue(
            float(Utility.get_settings_value(section=f"{name}_Model_Parameter", prop="frequency_penalty", default="0.0",
                                             save=True)))
        frequencyPenaltySpinBox.check_box.setChecked(True)
        frequencyPenaltySpinBox.valueChanged.connect(lambda value: self.frequency_penalty_changed(value, name))
        paramLayout.addRow('Frequency Penalty', frequencyPenaltySpinBox)

        presencePenaltySpinBox = CheckDoubleSpinBox()
        presencePenaltySpinBox.setObjectName(f"{name}_presencePenaltySpinBox")
        presencePenaltySpinBox.spin_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        presencePenaltySpinBox.spin_box.setRange(-2, 2)
        presencePenaltySpinBox.spin_box.setAccelerated(True)
        presencePenaltySpinBox.spin_box.setSingleStep(0.1)
        presencePenaltySpinBox.spin_box.setValue(
            float(Utility.get_settings_value(section=f"{name}_Model_Parameter", prop="presence_penalty", default="0.0",
                                             save=True)))
        presencePenaltySpinBox.check_box.setChecked(True)
        presencePenaltySpinBox.valueChanged.connect(lambda value: self.presence_penalty_changed(value, name))
        paramLayout.addRow('Presence Penalty', presencePenaltySpinBox)

        seedSpinBox = CheckSpinBox()
        seedSpinBox.setObjectName(f"{name}_seedSpinBox")
        seedSpinBox.spin_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        seedSpinBox.spin_box.setRange(1, 100000000)
        seedSpinBox.spin_box.setAccelerated(True)
        seedSpinBox.spin_box.setSingleStep(1)
        seedSpinBox.spin_box.setValue(
            int(
                Utility.get_settings_value(section=f"{name}_Model_Parameter", prop="seed", default="1234567",
                                           save=True)))
        seedSpinBox.check_box.setChecked(True)
        seedSpinBox.valueChanged.connect(lambda value: self.seed_changed(value, name))
        paramLayout.addRow('Seed', seedSpinBox)

        groupParam.setLayout(paramLayout)
        layoutMain.addWidget(groupParam)

        optionGroup = QGroupBox(f"{name} Options")
        optionLayout = QVBoxLayout()

        streamCheckbox = QCheckBox("Stream")
        streamCheckbox.setObjectName(f"{name}_streamCheckbox")
        streamCheckbox.setChecked(
            (Utility.get_settings_value(section=f"{name}_Model_Parameter", prop="stream", default="True",
                                        save=True)) == "True")
        streamCheckbox.toggled.connect(lambda value: self.stream_changed(value, name))
        optionLayout.addWidget(streamCheckbox)
        optionGroup.setLayout(optionLayout)

        layoutMain.addWidget(optionGroup)

        tabWidget.setLayout(layoutMain)

        return tabWidget

    def create_openai_tabcontent(self, name):
        tabWidget = QWidget()
        tabWidget.setObjectName(name)
        layoutMain = QVBoxLayout()

        groupSystem = self.create_system_layout(name)
        layoutMain.addWidget(groupSystem)

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

        stop_sequencesLineEdit = CheckLineEdit()
        stop_sequencesLineEdit.setObjectName(f"{name}_stop_sequencesLineEdit")
        stop_sequencesLineEdit.line_edit.setPlaceholderText('stop sequence')
        stop_sequencesLineEdit.line_edit.setText(
            Utility.get_settings_value(section=f"{name}_Model_Parameter", prop="stop",
                                       default="", save=True))
        stop_sequencesLineEdit.check_box.setChecked(True)
        stop_sequencesLineEdit.textChanged.connect(lambda value: self.stopsequences_changed(value, name))
        paramLayout.addRow('Stop Sequence', stop_sequencesLineEdit)

        max_tokensSpinBox = CheckSpinBox()
        max_tokensSpinBox.setObjectName(f"{name}_max_tokensSpinBox")
        max_tokensSpinBox.spin_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        max_tokensSpinBox.spin_box.setRange(0, 128000)
        max_tokensSpinBox.spin_box.setAccelerated(True)
        max_tokensSpinBox.spin_box.setSingleStep(1)
        max_tokensSpinBox.spin_box.setValue(
            int(
                Utility.get_settings_value(section=f"{name}_Model_Parameter", prop="max_tokens",
                                           default="2048", save=True)))
        max_tokensSpinBox.check_box.setChecked(True)
        max_tokensSpinBox.valueChanged.connect(lambda value: self.maxtokens_changed(value, name))
        paramLayout.addRow('Max Tokens', max_tokensSpinBox)

        temperatureSpinBox = CheckDoubleSpinBox()
        temperatureSpinBox.setObjectName(f"{name}_temperatureSpinBox")
        temperatureSpinBox.spin_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        temperatureSpinBox.spin_box.setRange(0, 2)
        temperatureSpinBox.spin_box.setAccelerated(True)
        temperatureSpinBox.spin_box.setSingleStep(0.1)
        temperatureSpinBox.spin_box.setValue(
            float(Utility.get_settings_value(section=f"{name}_Model_Parameter", prop="temperature", default="0.2",
                                             save=True)))
        temperatureSpinBox.valueChanged.connect(lambda value: self.temperature_changed(value, name))
        paramLayout.addRow('Temperature', temperatureSpinBox)

        top_pSpinBox = CheckDoubleSpinBox()
        top_pSpinBox.setObjectName(f"{name}_top_pSpinBox")
        top_pSpinBox.spin_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        top_pSpinBox.spin_box.setRange(0, 1)
        top_pSpinBox.spin_box.setAccelerated(True)
        top_pSpinBox.spin_box.setSingleStep(0.1)
        top_pSpinBox.spin_box.setValue(
            float(
                Utility.get_settings_value(section=f"{name}_Model_Parameter", prop="top_p", default="0.1", save=True)))
        top_pSpinBox.check_box.setChecked(True)
        top_pSpinBox.valueChanged.connect(lambda value: self.topp_changed(value, name))
        paramLayout.addRow('Top P', top_pSpinBox)

        frequencyPenaltySpinBox = CheckDoubleSpinBox()
        frequencyPenaltySpinBox.setObjectName(f"{name}_frequencyPenaltySpinBox")
        frequencyPenaltySpinBox.spin_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        frequencyPenaltySpinBox.spin_box.setRange(-2, 2)
        frequencyPenaltySpinBox.spin_box.setAccelerated(True)
        frequencyPenaltySpinBox.spin_box.setSingleStep(0.1)
        frequencyPenaltySpinBox.spin_box.setValue(
            float(Utility.get_settings_value(section=f"{name}_Model_Parameter", prop="frequency_penalty", default="0.0",
                                             save=True)))
        frequencyPenaltySpinBox.check_box.setChecked(True)
        frequencyPenaltySpinBox.valueChanged.connect(lambda value: self.frequency_penalty_changed(value, name))
        paramLayout.addRow('Frequency Penalty', frequencyPenaltySpinBox)

        presencePenaltySpinBox = CheckDoubleSpinBox()
        presencePenaltySpinBox.setObjectName(f"{name}_presencePenaltySpinBox")
        presencePenaltySpinBox.spin_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        presencePenaltySpinBox.spin_box.setRange(-2, 2)
        presencePenaltySpinBox.spin_box.setAccelerated(True)
        presencePenaltySpinBox.spin_box.setSingleStep(0.1)
        presencePenaltySpinBox.spin_box.setValue(
            float(Utility.get_settings_value(section=f"{name}_Model_Parameter", prop="presence_penalty", default="0.0",
                                             save=True)))
        presencePenaltySpinBox.check_box.setChecked(True)
        presencePenaltySpinBox.valueChanged.connect(lambda value: self.presence_penalty_changed(value, name))
        paramLayout.addRow('Presence Penalty', presencePenaltySpinBox)

        seedSpinBox = CheckSpinBox()
        seedSpinBox.setObjectName(f"{name}_seedSpinBox")
        seedSpinBox.spin_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        seedSpinBox.spin_box.setRange(1, 100000000)
        seedSpinBox.spin_box.setAccelerated(True)
        seedSpinBox.spin_box.setSingleStep(1)
        seedSpinBox.spin_box.setValue(
            int(
                Utility.get_settings_value(section=f"{name}_Model_Parameter", prop="seed", default="1234567",
                                           save=True)))
        seedSpinBox.check_box.setChecked(True)
        seedSpinBox.valueChanged.connect(lambda value: self.seed_changed(value, name))
        paramLayout.addRow('Seed', seedSpinBox)

        groupParam.setLayout(paramLayout)
        layoutMain.addWidget(groupParam)

        optionGroup = QGroupBox(f"{name} Options")
        optionLayout = QVBoxLayout()

        streamCheckbox = QCheckBox("Stream")
        streamCheckbox.setObjectName(f"{name}_streamCheckbox")
        streamCheckbox.setChecked(
            (Utility.get_settings_value(section=f"{name}_Model_Parameter", prop="stream", default="True",
                                        save=True)) == "True")
        streamCheckbox.toggled.connect(lambda value: self.stream_changed(value, name))
        optionLayout.addWidget(streamCheckbox)
        optionGroup.setLayout(optionLayout)

        layoutMain.addWidget(optionGroup)

        tabWidget.setLayout(layoutMain)

        return tabWidget

    def create_gemini_tabcontent(self, name):
        tabWidget = QWidget()
        tabWidget.setObjectName(name)
        layoutMain = QVBoxLayout()

        groupSystem = self.create_system_layout(name)
        layoutMain.addWidget(groupSystem)

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

        candidate_countSpinBox = CheckSpinBox()
        candidate_countSpinBox.setObjectName(f"{name}_candidate_countSpinBox")
        candidate_countSpinBox.spin_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        candidate_countSpinBox.spin_box.setValue(
            int(Utility.get_settings_value(section=f"{name}_Model_Parameter", prop="candidate_count", default="1",
                                           save=True)))
        candidate_countSpinBox.setEnabled(False)
        paramLayout.addRow('Candidate', candidate_countSpinBox)

        stop_sequencesLineEdit = CheckLineEdit()
        stop_sequencesLineEdit.setObjectName(f"{name}_stop_sequencesLineEdit")
        stop_sequencesLineEdit.line_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        stop_sequencesLineEdit.line_edit.setPlaceholderText('stop sequence')
        stop_sequencesLineEdit.line_edit.setText(
            Utility.get_settings_value(section=f"{name}_Model_Parameter", prop="stop_sequences",
                                       default="", save=True))
        stop_sequencesLineEdit.check_box.setChecked(True)
        stop_sequencesLineEdit.textChanged.connect(lambda value: self.stopsequences_changed(value, name))
        paramLayout.addRow('Stop Sequence', stop_sequencesLineEdit)

        max_output_tokensSpinBox = CheckSpinBox()
        max_output_tokensSpinBox.setObjectName(f"{name}_max_output_tokensSpinBox")
        max_output_tokensSpinBox.spin_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        max_output_tokensSpinBox.spin_box.setRange(0, 2048)
        max_output_tokensSpinBox.spin_box.setAccelerated(True)
        max_output_tokensSpinBox.spin_box.setSingleStep(1)
        max_output_tokensSpinBox.spin_box.setValue(
            int(
                Utility.get_settings_value(section=f"{name}_Model_Parameter", prop="max_output_tokens",
                                           default="2048", save=True)))
        max_output_tokensSpinBox.valueChanged.connect(lambda value: self.maxoutputtokens_changed(value, name))
        paramLayout.addRow('Max Tokens', max_output_tokensSpinBox)

        temperatureSpinBox = CheckDoubleSpinBox()
        temperatureSpinBox.setObjectName(f"{name}_temperatureSpinBox")
        temperatureSpinBox.spin_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        temperatureSpinBox.spin_box.setRange(0, 2)
        temperatureSpinBox.spin_box.setAccelerated(True)
        temperatureSpinBox.spin_box.setSingleStep(0.1)
        temperatureSpinBox.spin_box.setValue(
            float(Utility.get_settings_value(section=f"{name}_Model_Parameter", prop="temperature", default="0.2",
                                             save=True)))
        temperatureSpinBox.valueChanged.connect(lambda value: self.temperature_changed(value, name))
        paramLayout.addRow('Temperature', temperatureSpinBox)

        top_pSpinBox = CheckDoubleSpinBox()
        top_pSpinBox.setObjectName(f"{name}_top_pSpinBox")
        top_pSpinBox.spin_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        top_pSpinBox.spin_box.setRange(0, 1)
        top_pSpinBox.spin_box.setAccelerated(True)
        top_pSpinBox.spin_box.setSingleStep(0.1)
        top_pSpinBox.spin_box.setValue(
            float(
                Utility.get_settings_value(section=f"{name}_Model_Parameter", prop="top_p", default="0.1", save=True)))
        top_pSpinBox.check_box.setChecked(True)
        top_pSpinBox.valueChanged.connect(lambda value: self.topp_changed(value, name))
        paramLayout.addRow('Top_P', top_pSpinBox)

        top_kSpinBox = CheckSpinBox()
        top_kSpinBox.setObjectName(f"{name}_top_kSpinBox")
        top_kSpinBox.spin_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        top_kSpinBox.spin_box.setRange(0, 1000)
        top_kSpinBox.spin_box.setAccelerated(True)
        top_kSpinBox.spin_box.setSingleStep(1)
        top_kSpinBox.spin_box.setValue(
            int(
                Utility.get_settings_value(section=f"{name}_Model_Parameter", prop="top_k", default="1", save=True)))
        top_kSpinBox.check_box.setChecked(True)
        top_kSpinBox.valueChanged.connect(lambda value: self.topk_changed(value, name))
        paramLayout.addRow('Top_K', top_kSpinBox)

        groupParam.setLayout(paramLayout)
        layoutMain.addWidget(groupParam)

        optionGroup = QGroupBox(f"{name} Options")
        optionLayout = QVBoxLayout()

        streamCheckbox = QCheckBox("Stream")
        streamCheckbox.setObjectName(f"{name}_streamCheckbox")
        streamCheckbox.setChecked(
            (Utility.get_settings_value(section=f"{name}_Model_Parameter", prop="stream", default="True",
                                        save=True)) == "True")
        streamCheckbox.toggled.connect(lambda value: self.stream_changed(value, name))
        optionLayout.addWidget(streamCheckbox)
        optionGroup.setLayout(optionLayout)

        layoutMain.addWidget(optionGroup)

        tabWidget.setLayout(layoutMain)

        return tabWidget

    def create_claude_tabcontent(self, name):
        tabWidget = QWidget()
        tabWidget.setObjectName(name)
        layoutMain = QVBoxLayout()

        groupSystem = self.create_system_layout(name)
        layoutMain.addWidget(groupSystem)

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

        stop_sequencesLineEdit = CheckLineEdit()
        stop_sequencesLineEdit.setObjectName(f"{name}_stop_sequencesLineEdit")
        stop_sequencesLineEdit.line_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        stop_sequencesLineEdit.line_edit.setPlaceholderText('stop sequence')
        stop_sequencesLineEdit.line_edit.setText(
            Utility.get_settings_value(section=f"{name}_Model_Parameter", prop="stop_sequences",
                                       default="", save=True))
        stop_sequencesLineEdit.check_box.setChecked(True)
        stop_sequencesLineEdit.textChanged.connect(lambda value: self.stopsequences_changed(value, name))
        paramLayout.addRow('Stop Sequence', stop_sequencesLineEdit)

        max_tokensSpinBox = CheckSpinBox()
        max_tokensSpinBox.setObjectName(f"{name}_max_tokensSpinBox")
        max_tokensSpinBox.spin_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        max_tokensSpinBox.spin_box.setRange(0, 4096)
        max_tokensSpinBox.spin_box.setAccelerated(True)
        max_tokensSpinBox.spin_box.setSingleStep(1)
        max_tokensSpinBox.spin_box.setValue(
            int(
                Utility.get_settings_value(section=f"{name}_Model_Parameter", prop="max_tokens",
                                           default="2048", save=True)))
        max_tokensSpinBox.check_box.setEnabled(False)
        max_tokensSpinBox.valueChanged.connect(lambda value: self.maxtokens_changed(value, name))
        paramLayout.addRow('Max Tokens', max_tokensSpinBox)

        temperatureSpinBox = CheckDoubleSpinBox()
        temperatureSpinBox.setObjectName(f"{name}_temperatureSpinBox")
        temperatureSpinBox.spin_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        temperatureSpinBox.spin_box.setRange(0, 2)
        temperatureSpinBox.spin_box.setAccelerated(True)
        temperatureSpinBox.spin_box.setSingleStep(0.1)
        temperatureSpinBox.spin_box.setValue(
            float(Utility.get_settings_value(section=f"{name}_Model_Parameter", prop="temperature", default="0.2",
                                             save=True)))
        temperatureSpinBox.valueChanged.connect(lambda value: self.temperature_changed(value, name))
        paramLayout.addRow('Temperature', temperatureSpinBox)

        top_pSpinBox = CheckDoubleSpinBox()
        top_pSpinBox.setObjectName(f"{name}_top_pSpinBox")
        top_pSpinBox.spin_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        top_pSpinBox.spin_box.setRange(0, 1)
        top_pSpinBox.spin_box.setAccelerated(True)
        top_pSpinBox.spin_box.setSingleStep(0.1)
        top_pSpinBox.spin_box.setValue(
            float(
                Utility.get_settings_value(section=f"{name}_Model_Parameter", prop="top_p", default="0.1", save=True)))
        top_pSpinBox.check_box.setChecked(True)
        top_pSpinBox.valueChanged.connect(lambda value: self.topp_changed(value, name))
        paramLayout.addRow('Top_P', top_pSpinBox)

        top_kSpinBox = CheckSpinBox()
        top_kSpinBox.setObjectName(f"{name}_top_kSpinBox")
        top_kSpinBox.spin_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        top_kSpinBox.spin_box.setRange(0, 1000)
        top_kSpinBox.spin_box.setAccelerated(True)
        top_kSpinBox.spin_box.setSingleStep(1)
        top_kSpinBox.spin_box.setValue(
            int(
                Utility.get_settings_value(section=f"{name}_Model_Parameter", prop="top_k", default="1", save=True)))
        top_kSpinBox.check_box.setChecked(True)
        top_kSpinBox.valueChanged.connect(lambda value: self.topk_changed(value, name))
        paramLayout.addRow('Top_K', top_kSpinBox)

        groupParam.setLayout(paramLayout)
        layoutMain.addWidget(groupParam)

        optionGroup = QGroupBox(f"{name} Options")
        optionLayout = QVBoxLayout()

        streamCheckbox = QCheckBox("Stream")
        streamCheckbox.setObjectName(f"{name}_streamCheckbox")
        streamCheckbox.setChecked(
            (Utility.get_settings_value(section=f"{name}_Model_Parameter", prop="stream", default="True",
                                        save=True)) == "True")
        streamCheckbox.toggled.connect(lambda value: self.stream_changed(value, name))
        optionLayout.addWidget(streamCheckbox)
        optionGroup.setLayout(optionLayout)

        layoutMain.addWidget(optionGroup)

        tabWidget.setLayout(layoutMain)

        return tabWidget

    def set_model_list(self, modelList, name):
        if name == AIProviderName.OPENAI.value:
            api_key = self._settings.value('AI_Provider/OpenAI')
            if api_key:
                modelList.addItems(Utility.get_openai_model_list(api_key))
                llm_model = Utility.get_settings_value(
                    section=f"{name}_Model_Parameter",
                    prop="model_name",
                    default='gpt-3.5-turbo',
                    save=True
                )
                modelList.setCurrentIndex(modelList.findText(llm_model))
                modelList.currentTextChanged.connect(lambda current_text: self.model_list_changed(current_text, name))

        elif name == AIProviderName.GEMINI.value:
            api_key = self._settings.value('AI_Provider/Gemini')
            if api_key:
                modelList.addItems(Utility.get_gemini_model_list(api_key))
                llm_model = Utility.get_settings_value(
                    section=f"{name}_Model_Parameter",
                    prop="model_name",
                    default='gemini-pro',
                    save=True
                )
                modelList.setCurrentIndex(modelList.findText(llm_model))
                modelList.currentTextChanged.connect(lambda current_text: self.model_list_changed(current_text, name))

        elif name == AIProviderName.CLAUDE.value:
            api_key = self._settings.value('AI_Provider/Claude')
            if api_key:
                modelList.addItems(Utility.get_claude_ai_model_list(api_key))
                llm_model = Utility.get_settings_value(
                    section=f"{name}_Model_Parameter",
                    prop="model_name",
                    default='claude-3-opus-20240229',
                    save=True
                )
                modelList.setCurrentIndex(modelList.findText(llm_model))
                modelList.currentTextChanged.connect(lambda current_text: self.model_list_changed(current_text, name))

        elif name == AIProviderName.OLLAMA.value:
            api_key = self._settings.value('AI_Provider/Ollama')
            if api_key:
                modelList.addItems(Utility.get_ollama_ai_model_list(api_key))
                llm_model = Utility.get_settings_value(
                    section=f"{name}_Model_Parameter",
                    prop="model_name",
                    default='llama3:8b',
                    save=True
                )
                modelList.setCurrentIndex(modelList.findText(llm_model))
                modelList.currentTextChanged.connect(lambda current_text: self.model_list_changed(current_text, name))

    def model_list_changed(self, current_text, name):
        self._settings.setValue(f"{name}_Model_Parameter/model_name", current_text)

    def stopsequences_changed(self, value, name):
        if name == AIProviderName.OPENAI.value or name == AIProviderName.OLLAMA.value:
            self._settings.setValue(f"{name}_Model_Parameter/stop", value)
        else:
            self._settings.setValue(f"{name}_Model_Parameter/stop_sequences", value)

    def temperature_changed(self, value, name):
        self._settings.setValue(f"{name}_Model_Parameter/temperature", value)

    def topp_changed(self, value, name):
        self._settings.setValue(f"{name}_Model_Parameter/top_p", value)

    def topk_changed(self, value, name):
        self._settings.setValue(f"{name}_Model_Parameter/top_k", value)

    def numpredict_changed(self, value, name):
        self._settings.setValue(f"{name}_Model_Parameter/num_predict", value)

    def maxtokens_changed(self, value, name):
        self._settings.setValue(f"{name}_Model_Parameter/max_tokens", value)

    def maxoutputtokens_changed(self, value, name):
        self._settings.setValue(f"{name}_Model_Parameter/max_output_tokens", value)

    def frequency_penalty_changed(self, value, name):
        self._settings.setValue(f"{name}_Model_Parameter/frequency_penalty", value)

    def presence_penalty_changed(self, value, name):
        self._settings.setValue(f"{name}_Model_Parameter/presence_penalty", value)

    def seed_changed(self, value, name):
        self._settings.setValue(f"{name}_Model_Parameter/seed", value)

    def stream_changed(self, checked, name):
        if checked:
            self._settings.setValue(f"{name}_Model_Parameter/stream", 'True')
        else:
            self._settings.setValue(f"{name}_Model_Parameter/stream", 'False')

    def create_system_layout(self, name):
        groupSystem = QGroupBox(f"{name} System")
        systemLayout = QFormLayout()
        systemLabel = QLabel("Select System")
        systemList = QComboBox()
        systemList.setObjectName(f"{name}_systemList")
        system_values = Utility.get_system_value(section=f"{name}_System", prefix="system",
                                                 default="You are a helpful assistant.", length=5)
        systemList.addItems(system_values.keys())
        systemList.currentIndexChanged.connect(lambda: self.on_system_change(name))

        current_system = QTextEdit()
        current_system.setObjectName(f"{name}_current_system")
        current_system.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Preferred)
        current_system.setText(system_values['system1'])

        save_system_button = QPushButton(QIcon(Utility.get_icon_path('ico', 'disk-black.png')), 'Save')
        save_system_button.clicked.connect(lambda: self.save_system_value(name))

        systemLayout.addRow(systemLabel)
        systemLayout.addRow(systemList)
        systemLayout.addRow(current_system)
        systemLayout.addRow(save_system_button)
        groupSystem.setLayout(systemLayout)
        return groupSystem

    def create_chatdb_tab(self):
        layoutWidget = QWidget()
        layout = QVBoxLayout()

        self._chat_history = ChatHistory(self.model)

        layout.addWidget(self._chat_history)

        layoutWidget.setLayout(layout)
        return layoutWidget

    def create_prompt_tab(self):
        layoutWidget = QWidget()
        layout = QVBoxLayout()

        self._prompt_list = ChatPromptListWidget()
        layout.addWidget(self.prompt_list)

        layoutWidget.setLayout(layout)
        return layoutWidget

    def create_system_tab(self):
        layoutWidget = QWidget()
        layout = QVBoxLayout()

        layout.addWidget(QLabel("System"))

        layoutWidget.setLayout(layout)
        return layoutWidget

    def update_ui_submit(self, chatType, text):
        self.ai_answer_scroll_area.verticalScrollBar().rangeChanged.connect(self.adjust_scroll_bar)
        self.add_user_question(chatType, text)
        self.stop_widget.setVisible(True)

    def add_user_question(self, chatType, text):
        user_question = ChatWidget(chatType, text)
        self.result_layout.addWidget(user_question)

    def adjust_scroll_bar(self, min_val, max_val):
        self.ai_answer_scroll_area.verticalScrollBar().setSliderPosition(max_val)

    def update_ui(self, result, stream):
        if stream:
            chatWidget = self.get_last_ai_widget()

            if chatWidget:
                chatWidget.add_text(result)
            else:
                chatWidget = ChatWidget(ChatType.AI)
                chatWidget.add_text(result)
                self.result_layout.addWidget(chatWidget)

        else:
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
                Constants.MODEL_PREFIX + model + " | Response Time : " + format(elapsed_time, ".2f"))

    def get_last_ai_widget(self) -> ChatWidget | None:
        layout_item = self.result_widget.layout().itemAt(self.result_widget.layout().count() - 1)
        if layout_item:
            last_ai_widget = layout_item.widget()
            if last_ai_widget.get_chat_type() == ChatType.AI:
                return last_ai_widget
        else:
            return None

    def handle_submitted_signal(self, text):
        if text:
            self.submitted_signal.emit(text)

    def start_chat(self):
        self.prompt_text.clear()
        self.prompt_text.setEnabled(False)

    def finish_chat(self):
        self.prompt_text.setEnabled(True)
        self.prompt_text.setFocus()

    def clear_prompt(self):
        self.prompt_text.clear()

    def set_focus(self):
        self.prompt_text.setFocus()

    def set_prompt(self, prompt):
        self.prompt_text.setText(prompt)

    def get_all_text(self):
        question = Utility.get_settings_value(section="AI_Provider", prop="question",
                                              default="[Question]", save=True)

        answer = Utility.get_settings_value(section="AI_Provider", prop="answer",
                                            default="[Answer]", save=True)

        all_previous_qa = []
        for i in range(self.result_layout.count()):
            current_widget = self.result_layout.itemAt(i).widget()
            if current_widget.get_chat_type() == ChatType.HUMAN and len(current_widget.get_text()) > 0:
                all_previous_qa.append(f'{question}: {current_widget.get_text()}')
            elif current_widget.get_chat_type() == ChatType.AI and len(current_widget.get_text()) > 0:
                all_previous_qa.append(f'{answer}: {current_widget.get_text()}')
        return '\n'.join(all_previous_qa)

    def create_args(self, text, chat_llm):
        method_name = f'create_args_{chat_llm.lower()}'
        method = getattr(self, method_name, None)
        if callable(method):
            return method(text, chat_llm)
        else:
            raise ValueError(f'{UI.METHOD} {method_name} {UI.NOT_FOUND}')

    def create_args_ollama(self, text, chat_llm):
        api_key = self._settings.value(f'AI_Provider/{chat_llm}')
        model = self.findChild(QComboBox, f'{chat_llm}_ModelList').currentText()

        messages = [
            {"role": "system",
             "content": self.findChild(QTextEdit, f'{chat_llm}_current_system').toPlainText()},
            {"role": "assistant", "content": self.get_all_text()},
            {"role": "user", "content": text}
        ]

        stream = self.findChild(QCheckBox,
                                f'{chat_llm}_streamCheckbox').isChecked()

        stop_line_edit = self.findChild(CheckLineEdit,
                                        f'{chat_llm}_stop_sequencesLineEdit')
        stop = stop_line_edit.line_edit.text() if stop_line_edit.line_edit.isEnabled() else None

        num_predict_spin_box = self.findChild(CheckSpinBox,
                                              f'{chat_llm}_num_predictSpinBox').spin_box
        num_predict = num_predict_spin_box.value() if num_predict_spin_box.isEnabled() else None

        temperature_spin_box = self.findChild(CheckDoubleSpinBox,
                                              f'{chat_llm}_temperatureSpinBox').spin_box
        temperature = temperature_spin_box.value() if temperature_spin_box.isEnabled() else None

        top_p_spin_box = self.findChild(CheckDoubleSpinBox,
                                        f'{chat_llm}_top_pSpinBox').spin_box
        top_p = top_p_spin_box.value() if top_p_spin_box.isEnabled() else None

        top_k_spin_box = self.findChild(CheckSpinBox,
                                        f'{chat_llm}_top_kSpinBox').spin_box
        top_k = top_k_spin_box.value() if top_k_spin_box.isEnabled() else None

        frequency_penalty_spin_box = self.findChild(CheckDoubleSpinBox,
                                                    f'{chat_llm}_frequencyPenaltySpinBox').spin_box
        frequency_penalty = frequency_penalty_spin_box.value() if frequency_penalty_spin_box.isEnabled() else None

        presence_penalty_spin_box = self.findChild(CheckDoubleSpinBox,
                                                   f'{chat_llm}_presencePenaltySpinBox').spin_box
        presence_penalty = presence_penalty_spin_box.value() if presence_penalty_spin_box.isEnabled() else None

        seed_check_spin_box = self.findChild(CheckSpinBox,
                                             f'{chat_llm}_seedSpinBox').spin_box
        seed = seed_check_spin_box.value() if seed_check_spin_box.isEnabled() else None

        options = {
            'num_predict': num_predict,
            'temperature:': temperature,
            'top_p': top_p,
            'top_k': top_k,
            'frequency_penalty': frequency_penalty,
            'presence_penalty': presence_penalty,
            'seed': seed,
        }

        if stop:
            options['stop'] = [stop]

        ai_arg = {
            'model': model,
            'messages': messages,
            'stream': stream,
            'options': options,
        }

        args = {
            'api_key': api_key,
            'ai_arg': ai_arg
        }

        return args

    def create_args_claude(self, text, chat_llm):
        api_key = self._settings.value(f'AI_Provider/{chat_llm}')
        model = self.findChild(QComboBox, f'{chat_llm}_ModelList').currentText()

        messages = [
            {"role": "user", "content": text},
            {"role": "assistant", "content": self.get_all_text()},
        ]

        system = self.findChild(QTextEdit, f'{chat_llm}_current_system').toPlainText()

        stream = self.findChild(QCheckBox,
                                f'{chat_llm}_streamCheckbox').isChecked()

        stop_sequences_line_edit = self.findChild(CheckLineEdit,
                                                  f'{chat_llm}_stop_sequencesLineEdit')
        stop_sequences = stop_sequences_line_edit.line_edit.text() if stop_sequences_line_edit.line_edit.isEnabled() else []

        max_tokens_spin_box = self.findChild(CheckSpinBox,
                                             f'{chat_llm}_max_tokensSpinBox').spin_box
        max_tokens = max_tokens_spin_box.value() if max_tokens_spin_box.isEnabled() else None

        temperature_spin_box = self.findChild(CheckDoubleSpinBox,
                                              f'{chat_llm}_temperatureSpinBox').spin_box
        temperature = temperature_spin_box.value() if temperature_spin_box.isEnabled() else None

        top_p_spin_box = self.findChild(CheckDoubleSpinBox,
                                        f'{chat_llm}_top_pSpinBox').spin_box
        top_p = top_p_spin_box.value() if top_p_spin_box.isEnabled() else None

        top_k_spin_box = self.findChild(CheckSpinBox,
                                        f'{chat_llm}_top_kSpinBox').spin_box
        top_k = top_k_spin_box.value() if top_k_spin_box.isEnabled() else None

        ai_arg = {
            'model': model,
            'messages': messages,
            'stream': stream,
            'max_tokens': max_tokens,
            'system': system,
        }

        if stop_sequences:
            ai_arg['stop_sequences'] = [stop_sequences]

        if temperature:
            ai_arg['temperature'] = temperature

        if top_p:
            ai_arg['top_p'] = top_p

        if top_k:
            ai_arg['top_k'] = top_k

        args = {
            'api_key': api_key,
            'ai_arg': ai_arg
        }

        return args

    def create_args_openai(self, text, chat_llm):
        api_key = self._settings.value(f'AI_Provider/{chat_llm}')
        model = self.findChild(QComboBox, f'{chat_llm}_ModelList').currentText()

        messages = [
            {"role": "system",
             "content": self.findChild(QTextEdit, f'{chat_llm}_current_system').toPlainText()},
            {"role": "assistant", "content": self.get_all_text()},
            {"role": "user", "content": text}
        ]

        stream = self.findChild(QCheckBox,
                                f'{chat_llm}_streamCheckbox').isChecked()

        stop_line_edit = self.findChild(CheckLineEdit,
                                        f'{chat_llm}_stop_sequencesLineEdit')
        stop = stop_line_edit.line_edit.text() if stop_line_edit.line_edit.isEnabled() else None

        max_tokens_spin_box = self.findChild(CheckSpinBox,
                                             f'{chat_llm}_max_tokensSpinBox').spin_box
        max_tokens = max_tokens_spin_box.value() if max_tokens_spin_box.isEnabled() else None

        temperature_spin_box = self.findChild(CheckDoubleSpinBox,
                                              f'{chat_llm}_temperatureSpinBox').spin_box
        temperature = temperature_spin_box.value() if temperature_spin_box.isEnabled() else None

        top_p_spin_box = self.findChild(CheckDoubleSpinBox,
                                        f'{chat_llm}_top_pSpinBox').spin_box
        top_p = top_p_spin_box.value() if top_p_spin_box.isEnabled() else None

        frequency_penalty_spin_box = self.findChild(CheckDoubleSpinBox,
                                                    f'{chat_llm}_frequencyPenaltySpinBox').spin_box
        frequency_penalty = frequency_penalty_spin_box.value() if frequency_penalty_spin_box.isEnabled() else None

        presence_penalty_spin_box = self.findChild(CheckDoubleSpinBox,
                                                   f'{chat_llm}_presencePenaltySpinBox').spin_box
        presence_penalty = presence_penalty_spin_box.value() if presence_penalty_spin_box.isEnabled() else None

        seed_check_spin_box = self.findChild(CheckSpinBox,
                                             f'{chat_llm}_seedSpinBox').spin_box
        seed = seed_check_spin_box.value() if seed_check_spin_box.isEnabled() else None

        ai_arg = {
            'model': model,
            'messages': messages,
            'stream': stream,
            'max_tokens': max_tokens,
            'temperature': temperature,
            'top_p': top_p,
            'frequency_penalty': frequency_penalty,
            'presence_penalty': presence_penalty,
            'seed': seed
        }

        if stop:
            ai_arg['stop'] = [stop]

        args = {
            'api_key': api_key,
            'ai_arg': ai_arg
        }

        return args

    def create_args_gemini(self, text, chat_llm):
        api_key = self._settings.value(f'AI_Provider/{chat_llm}')
        model = self.findChild(QComboBox, f'{chat_llm}_ModelList').currentText()

        messages = [
            {"role": "model", "parts": self.get_all_text()},
            {"role": "user", "parts": text}
        ]

        stream = self.findChild(QCheckBox,
                                f'{chat_llm}_streamCheckbox').isChecked()

        candidate_count = self.findChild(CheckSpinBox,
                                         f'{chat_llm}_candidate_countSpinBox').spin_box.value()

        stop_sequences_line_edit = self.findChild(CheckLineEdit,
                                                  f'{chat_llm}_stop_sequencesLineEdit')
        stop_sequences = stop_sequences_line_edit.line_edit.text() if stop_sequences_line_edit.line_edit.isEnabled() else None

        max_output_tokens_spin_box = self.findChild(CheckSpinBox,
                                                    f'{chat_llm}_max_output_tokensSpinBox').spin_box
        max_output_tokens = max_output_tokens_spin_box.value() if max_output_tokens_spin_box.isEnabled() else None

        temperatue_spin_box = self.findChild(CheckDoubleSpinBox,
                                             f'{chat_llm}_temperatureSpinBox').spin_box
        temperature = temperatue_spin_box.value() if temperatue_spin_box.isEnabled() else None

        top_p_spin_box = self.findChild(CheckDoubleSpinBox,
                                        f'{chat_llm}_top_pSpinBox').spin_box
        top_p = top_p_spin_box.value() if top_p_spin_box.isEnabled() else None

        top_k_spin_box = self.findChild(CheckSpinBox,
                                        f'{chat_llm}_top_kSpinBox').spin_box
        top_k = top_k_spin_box.value() if top_k_spin_box.isEnabled() else None

        config = {
            'candidate_count': candidate_count,
            'max_output_tokens': max_output_tokens,
            'temperature': temperature,
            'top_p': top_p,
            'top_k': top_k,
        }

        if stop_sequences:
            config['stop_sequences'] = [stop_sequences]

        # REVIEW : set BLOCK_NONE for all category
        safety_settings = self.create_safety_settings()

        ai_arg = {
            'model': model,
            'messages': messages,
            'stream': stream,
            'config': config,
            'safety_settings': safety_settings,
            'system': self.findChild(QTextEdit, f'{chat_llm}_current_system').toPlainText()
        }

        args = {
            'api_key': api_key,
            'ai_arg': ai_arg
        }

        return args

    def create_safety_settings(self):
        safety_settings = [
            {
                'category': 'HARM_CATEGORY_HARASSMENT',
                'threshold': 'BLOCK_NONE'
            },
            {
                'category': 'HARM_CATEGORY_HATE_SPEECH',
                'threshold': 'BLOCK_NONE'
            },
            {
                'category': 'HARM_CATEGORY_DANGEROUS_CONTENT',
                'threshold': 'BLOCK_NONE'
            },
            {
                'category': 'HARM_CATEGORY_SEXUALLY_EXPLICIT',
                'threshold': 'BLOCK_NONE'
            },
        ]
        return safety_settings

    def clear_all(self):
        target_layout = self.result_layout
        if target_layout is not None:
            while target_layout.count():
                item = target_layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()

    def force_stop(self):
        self.stop_signal.emit()
        self.stop_widget.setVisible(False)

    @property
    def chat_history(self):
        return self._chat_history

    @property
    def prompt_list(self):
        return self._prompt_list
