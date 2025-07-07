from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QSizePolicy, QSplitter, QComboBox, QLabel, QTabWidget, \
    QGroupBox, QFormLayout, QCheckBox, QPushButton, QHBoxLayout, QApplication, QTextEdit, QListWidget, QFileDialog, \
    QMessageBox
from google.genai import types

from agent.view.AgentHistory import AgentHistory
from agent.view.AgentWidget import AgentWidget
from custom.CheckDoubleSpinBox import CheckDoubleSpinBox
from custom.CheckSpinBox import CheckSpinBox
from custom.PromptListWidget import PromptListWidget
from custom.PromptTextEdit import PromptTextEdit
from util.ChatType import ChatType
from util.Constants import AIProviderName, UI, AgentPattern
from util.Constants import Constants
from util.SettingsManager import SettingsManager
from util.Utility import Utility


class AgentView(QWidget):
    submitted_signal = pyqtSignal(str, str)
    stop_signal = pyqtSignal()
    current_llm_signal = pyqtSignal(str)
    reload_agent_detail_signal = pyqtSignal(int)
    new_agent_signal = pyqtSignal(str)

    def __init__(self, model):
        super().__init__()
        self.model = model
        self._settings = SettingsManager.get_settings()
        self._current_llm = Utility.get_settings_value(section="Agent_Pattern", prop="llm",
                                                       default="Claude", save=True)

        self._current_agent_pattern = Utility.get_settings_value(section="Agent_Pattern", prop="agent_pattern",
                                                                 default="Orchestrator", save=True)

        self.found_text_positions = []
        self.current_position_index = -1

        self.initialize_ui()

    def initialize_ui(self):
        self.create_all_ui_components()
        self.setup_layouts()
        self.initialize_data()
        self.connect_signals()

    def create_all_ui_components(self):
        self.create_top_control_components()
        self.create_agent_display_components()
        self.create_user_input_components()
        self.create_config_tab_components()
        self.create_bottom_control_components()

    def create_top_control_components(self):
        # Top layout
        self.top_layout = QVBoxLayout()
        self.top_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Create buttons
        self.clear_all_button = QPushButton(QIcon(Utility.get_icon_path('ico', 'bin.png')), UI.CLEAR_ALL)
        self.copy_all_button = QPushButton(QIcon(Utility.get_icon_path('ico', 'cards-stack.png')), UI.COPY_ALL)
        self.reload_button = QPushButton(QIcon(Utility.get_icon_path('ico', 'cards-address.png')), UI.RELOAD_ALL)

        # Search components
        self.search_text = PromptTextEdit()
        self.search_text.setPlaceholderText(UI.SEARCH_PROMPT_PLACEHOLDER)
        self.search_text.setFixedHeight(self.clear_all_button.sizeHint().height())
        self.search_text.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.search_result = QLabel()

        # Navigation buttons
        self.prev_button = QPushButton(QIcon(Utility.get_icon_path('ico', 'arrow-180.png')), '')
        self.next_button = QPushButton(QIcon(Utility.get_icon_path('ico', 'arrow.png')), '')

        # Create the top widget container
        self.top_widget = QWidget()
        self.top_widget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)

    def create_agent_display_components(self):
        # Result layout for agent messages
        self.result_layout = QVBoxLayout()
        self.result_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.result_layout.setSpacing(0)
        self.result_layout.setContentsMargins(0, 0, 0, 0)

        self.result_widget = QWidget()

        # Scroll area for agent messages
        self.ai_answer_scroll_area = QScrollArea()
        self.ai_answer_scroll_area.setWidgetResizable(True)

        # Stop button and its container
        self.stop_button = QPushButton(QIcon(Utility.get_icon_path('ico', 'minus-circle.png')), UI.STOP)

        self.stop_widget = QWidget()
        self.stop_widget.setVisible(False)

    def create_user_input_components(self):
        # Prompt text input
        self.prompt_text = PromptTextEdit()
        self.prompt_text.setPlaceholderText(UI.CHAT_PROMPT_PLACEHOLDER)

        # Prompt container
        self.prompt_widget = QWidget()
        self.prompt_widget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)

    def create_bottom_control_components(self):
        # Model selector components
        self.main_model_combo = QComboBox()
        self.main_model_combo.setMinimumWidth(150)

        # New chat button
        self.new_chat_button = QPushButton(QIcon(Utility.get_icon_path('ico', 'plus.png')), Constants.NEW_CHAT)

        # Container for bottom controls
        self.bottom_control_widget = QWidget()
        self.bottom_control_widget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)

    def create_config_tab_components(self):
        # Config tabs
        self.config_tabs = QTabWidget()

        # Tabs for agent patterns
        self.tabs = QTabWidget()

    def setup_layouts(self):
        self.setup_top_control_layout()
        self.setup_agent_display_layout()
        self.setup_user_input_layout()
        self.setup_config_tabs_layout()
        self.setup_bottom_control_layout()
        self.setup_main_layout()

    def setup_top_control_layout(self):
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.search_text)
        button_layout.addWidget(self.search_result)
        button_layout.addWidget(self.prev_button)
        button_layout.addWidget(self.next_button)
        button_layout.addWidget(self.copy_all_button)
        button_layout.addWidget(self.clear_all_button)
        button_layout.addWidget(self.reload_button)
        button_layout.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.top_layout.addLayout(button_layout)
        self.top_widget.setLayout(self.top_layout)

    def setup_agent_display_layout(self):
        self.result_widget.setLayout(self.result_layout)
        self.ai_answer_scroll_area.setWidget(self.result_widget)

        stop_layout = QHBoxLayout()
        stop_layout.setContentsMargins(0, 0, 0, 0)
        stop_layout.setSpacing(0)
        stop_layout.addWidget(self.stop_button)
        stop_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.stop_widget.setLayout(stop_layout)

    def setup_user_input_layout(self):
        prompt_layout = QVBoxLayout()
        prompt_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        prompt_layout.addWidget(self.prompt_text)
        prompt_layout.setSpacing(0)
        prompt_layout.setContentsMargins(0, 0, 0, 0)
        self.prompt_widget.setLayout(prompt_layout)

    def setup_bottom_control_layout(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 5, 0, 0)

        model_label = QLabel("Model")
        layout.addWidget(model_label)
        layout.addWidget(self.main_model_combo)
        layout.addStretch()
        layout.addWidget(self.new_chat_button)

        self.bottom_control_widget.setLayout(layout)

    def setup_config_tabs_layout(self):
        agent_icon = QIcon(Utility.get_icon_path('ico', 'robot.png'))
        self.config_tabs.addTab(self.create_parameters_tab(), agent_icon, UI.AGENT)
        self.config_tabs.addTab(self.create_agentdb_tab(), agent_icon, UI.AGENT_LIST)
        self.config_tabs.addTab(self.create_prompt_tab(), agent_icon, UI.PROMPT)

    def setup_main_layout(self):
        # Agent section layout
        agent_layout = QVBoxLayout()
        agent_layout.addWidget(self.top_widget)
        agent_layout.addWidget(self.ai_answer_scroll_area)
        agent_layout.addWidget(self.stop_widget)
        agent_layout.addWidget(self.prompt_widget)
        agent_layout.addWidget(self.bottom_control_widget)

        agentWidget = QWidget()
        agentWidget.setLayout(agent_layout)

        # Config section layout
        config_layout = QVBoxLayout()
        config_layout.addWidget(self.config_tabs)

        configWidget = QWidget()
        configWidget.setLayout(config_layout)

        # Main splitter
        mainWidget = QSplitter(Qt.Orientation.Horizontal)
        mainWidget.addWidget(configWidget)
        mainWidget.addWidget(agentWidget)
        mainWidget.setSizes([UI.QSPLITTER_LEFT_WIDTH, UI.QSPLITTER_RIGHT_WIDTH])
        mainWidget.setHandleWidth(UI.QSPLITTER_HANDLEWIDTH)

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.addWidget(mainWidget)
        self.setLayout(main_layout)

    def initialize_data(self):
        self.set_initial_tab()
        self.update_main_model_list()
        self.reset_search_bar()

    def set_initial_tab(self):
        index = self.tabs.indexOf(self.tabs.findChild(QWidget, self._current_agent_pattern))
        if index != -1:
            self.tabs.setCurrentIndex(index)

    def connect_signals(self):
        self.connect_top_control_signals()
        self.connect_agent_display_signals()
        self.connect_user_input_signals()
        self.connect_config_tab_signals()
        self.connect_bottom_control_signals()

    def connect_top_control_signals(self):
        self.clear_all_button.clicked.connect(lambda: self.clear_all())
        self.copy_all_button.clicked.connect(lambda: QApplication.clipboard().setText(self.get_all_text()))
        self.reload_button.clicked.connect(lambda: self.reload_agent_detail_signal.emit(-1))

        self.search_text.submitted_signal.connect(self.search)
        self.prev_button.clicked.connect(self.scroll_to_previous_match_widget)
        self.next_button.clicked.connect(self.scroll_to_next_match_widget)

    def connect_agent_display_signals(self):
        self.stop_button.clicked.connect(self.force_stop)

    def connect_user_input_signals(self):
        self.prompt_text.submitted_signal.connect(self.handle_submitted_signal)

    def connect_config_tab_signals(self):
        self.tabs.currentChanged.connect(self.on_tab_change)

    def connect_bottom_control_signals(self):
        self.main_model_combo.currentTextChanged.connect(self.sync_model_selection)
        self.new_chat_button.clicked.connect(self.create_new_agent)

    def update_main_model_list(self):
        saved_model = Utility.get_settings_value(
            section=f"{self._current_agent_pattern}_Model_Parameter",
            prop="model_name",
            default=self.get_default_model_for_provider(self._current_llm),
            save=True
        )

        self.main_model_combo.blockSignals(True)
        try:
            self.main_model_combo.clear()
            current_model_combo = self.findChild(QComboBox, f"{self._current_agent_pattern}_ModelList")
            if current_model_combo:
                for i in range(current_model_combo.count()):
                    self.main_model_combo.addItem(current_model_combo.itemText(i))

                saved_model_index = self.main_model_combo.findText(saved_model)
                if saved_model_index >= 0:
                    self.main_model_combo.setCurrentIndex(saved_model_index)
        finally:
            self.main_model_combo.blockSignals(False)

    def sync_model_selection(self, model_name):
        if not model_name:
            return

        current_model_combo = self.findChild(QComboBox, f"{self._current_agent_pattern}_ModelList")
        if current_model_combo and current_model_combo.count() > 0:
            # Block signals to prevent recursive calls
            current_model_combo.blockSignals(True)
            index = current_model_combo.findText(model_name)
            if index >= 0:
                current_model_combo.setCurrentIndex(index)
            current_model_combo.blockSignals(False)

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
        layout.setContentsMargins(5, 5, 5, 5)

        # Tabs for LLM
        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_evaluator_tabcontent(AgentPattern.EVALUATOR.value),
                         AgentPattern.EVALUATOR.value)
        self.tabs.addTab(self.create_orchestrator_tabcontent(AgentPattern.ORCHESTRATOR.value),
                         AgentPattern.ORCHESTRATOR.value)
        self.tabs.currentChanged.connect(self.on_tab_change)

        layout.addWidget(self.tabs)
        layoutWidget.setLayout(layout)

        layoutWidget.setMinimumWidth(300)
        layoutWidget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(layoutWidget)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        scroll_area.setMinimumWidth(320)

        return scroll_area

    def on_tab_change(self, index):
        self._current_agent_pattern = self.tabs.tabText(index)
        self._settings.setValue('Agent_Pattern/agent_pattern', self._current_agent_pattern)
        self.update_main_model_list()

    def create_new_agent(self):
        self.new_agent_signal.emit(Constants.NEW_AGENT)

    def set_default_tab(self, name):
        index = self.tabs.indexOf(self.tabs.findChild(QWidget, name))
        if index != -1:
            self.tabs.setCurrentIndex(index)

    def on_system_change(self, name):
        current_text = self.findChild(QComboBox, f"{name}_promptList").currentText()
        system_values = Utility.get_system_value(section=f"{name}_Prompt", prefix="prompt",
                                                 default="You are a helpful assistant.", length=5)
        current_system = self.findChild(QTextEdit, f"{name}_current_prompt")
        if current_text in system_values:
            current_system.setText(system_values[current_text])
        else:
            current_system.clear()

    def save_prompt_value(self, name):
        current_systemList = self.findChild(QComboBox, f"{name}_promptList")
        current_system = self.findChild(QTextEdit, f"{name}_current_prompt")
        selected_key = current_systemList.currentText()
        value = current_system.toPlainText()
        self._settings.setValue(f"{name}_Prompt/{selected_key}", value)
        self.update_prompt_list(name, Utility.extract_number_from_end(selected_key) - 1)

    def update_prompt_list(self, name, index=0):
        current_systemList = self.findChild(QComboBox, f"{name}_promptList")
        system_values = Utility.get_system_value(section=f"{name}_Prompt", prefix="prompt",
                                                 default="You are a helpful assistant.", length=5)
        if current_systemList:
            current_systemList.clear()
            current_systemList.addItems(system_values.keys())

        if system_values and current_systemList:
            current_systemList.setCurrentIndex(index)

    def create_evaluator_tabcontent(self, name):
        tabWidget = QWidget()
        tabWidget.setObjectName(name)
        layoutMain = QVBoxLayout()
        layoutMain.setContentsMargins(10, 10, 10, 10)
        layoutMain.setSpacing(10)

        # Provider ComboBox
        providerGroup = QGroupBox("AI Provider")
        providerLayout = QFormLayout()
        providerLabel = QLabel("Select Provider")
        providerComboBox = QComboBox()
        providerComboBox.setObjectName(f"{name}_ProviderComboBox")
        providerComboBox.addItems([
            AIProviderName.OPENAI.value,
            AIProviderName.CLAUDE.value,
            AIProviderName.GEMINI.value,
            AIProviderName.OLLAMA.value
        ])

        # Default = Claude
        default_provider = self._current_llm if self._current_llm in [provider.value for provider in
                                                                      AIProviderName] else AIProviderName.CLAUDE.value
        providerComboBox.setCurrentIndex(providerComboBox.findText(default_provider))

        def on_provider_changed(new_provider):
            modelList.clear()
            self.set_model_list(modelList, new_provider, name)
            self.update_main_model_list()

        providerComboBox.currentTextChanged.connect(on_provider_changed)
        providerLayout.addRow(providerLabel, providerComboBox)
        providerGroup.setLayout(providerLayout)
        layoutMain.addWidget(providerGroup)

        groupModel = QGroupBox(f"{name} Model")
        modelLayout = QFormLayout()
        modelLabel = QLabel(f"{name} Model List")
        modelList = QComboBox()
        modelList.setObjectName(f"{name}_ModelList")
        modelList.clear()

        # Provider's model list
        self.set_model_list(modelList, default_provider, name)
        modelLayout.addRow(modelLabel, modelList)
        groupModel.setLayout(modelLayout)
        layoutMain.addWidget(groupModel)

        # Evaluator, Optimizer Prompt
        evaluatorPrompt = self.create_prompt_layout(AgentPattern.EVALUATOR.value)
        layoutMain.addWidget(evaluatorPrompt)

        generatorPrompt = self.create_prompt_layout(AgentPattern.GENERATOR.value)
        layoutMain.addWidget(generatorPrompt)

        taskPrompt = self.create_prompt_layout(AgentPattern.TASK.value)
        layoutMain.addWidget(taskPrompt)

        # Parameters Group
        groupParam = QGroupBox(f"{name} Parameters")
        paramLayout = QFormLayout()

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
        temperatureSpinBox.check_box.setChecked(True)
        temperatureSpinBox.valueChanged.connect(lambda value: self.temperature_changed(value, name))
        paramLayout.addRow('Temperature', temperatureSpinBox)

        max_retriesSpinBox = CheckSpinBox()
        max_retriesSpinBox.setObjectName(f"{name}_max_retriesSpinBox")
        max_retriesSpinBox.spin_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        max_retriesSpinBox.spin_box.setRange(1, 10)
        max_retriesSpinBox.spin_box.setAccelerated(True)
        max_retriesSpinBox.spin_box.setSingleStep(1)
        max_retriesSpinBox.spin_box.setValue(
            int(
                Utility.get_settings_value(section=f"{name}_Model_Parameter", prop="max_retries",
                                           default="3", save=True)))
        max_retriesSpinBox.check_box.setChecked(True)
        max_retriesSpinBox.valueChanged.connect(lambda value: self.maxretriess_changed(value, name))
        paramLayout.addRow('Max Retries', max_retriesSpinBox)

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
        layoutMain.addStretch()

        tabWidget.setLayout(layoutMain)
        tabWidget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)

        return tabWidget

    def create_orchestrator_tabcontent(self, name):
        tabWidget = QWidget()
        tabWidget.setObjectName(name)
        layoutMain = QVBoxLayout()
        layoutMain.setContentsMargins(10, 10, 10, 10)
        layoutMain.setSpacing(10)

        # Provider ComboBox
        providerGroup = QGroupBox("AI Provider")
        providerLayout = QFormLayout()
        providerLabel = QLabel("Select Provider")
        providerComboBox = QComboBox()
        providerComboBox.setObjectName(f"{name}_ProviderComboBox")
        providerComboBox.addItems([
            AIProviderName.OPENAI.value,
            AIProviderName.CLAUDE.value,
            AIProviderName.GEMINI.value,
            AIProviderName.OLLAMA.value
        ])

        # Default = Claude
        default_provider = self._current_llm if self._current_llm in [provider.value for provider in
                                                                      AIProviderName] else AIProviderName.CLAUDE.value
        providerComboBox.setCurrentIndex(providerComboBox.findText(default_provider))

        def on_provider_changed(new_provider):
            modelList.clear()
            self.set_model_list(modelList, new_provider, name)
            self.update_main_model_list()

        providerComboBox.currentTextChanged.connect(on_provider_changed)
        providerLayout.addRow(providerLabel, providerComboBox)
        providerGroup.setLayout(providerLayout)
        layoutMain.addWidget(providerGroup)

        groupModel = QGroupBox(f"{name} Model")
        modelLayout = QFormLayout()
        modelLabel = QLabel(f"{name} Model List")
        modelList = QComboBox()
        modelList.setObjectName(f"{name}_ModelList")
        modelList.clear()

        # Provider's model list
        self.set_model_list(modelList, default_provider, name)
        modelLayout.addRow(modelLabel, modelList)
        groupModel.setLayout(modelLayout)
        layoutMain.addWidget(groupModel)

        # Orchestrator, Worker, Aggregator Prompt
        orchestratorPrompt = self.create_prompt_layout(AgentPattern.ORCHESTRATOR.value)
        layoutMain.addWidget(orchestratorPrompt)

        workerPrompt = self.create_prompt_layout(AgentPattern.WORKER.value)
        layoutMain.addWidget(workerPrompt)

        aggregatorPrompt = self.create_prompt_layout(AgentPattern.AGGREGATOR.value)
        layoutMain.addWidget(aggregatorPrompt)

        # Parameters Group
        groupParam = QGroupBox(f"{name} Parameters")
        paramLayout = QFormLayout()

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
        temperatureSpinBox.check_box.setChecked(True)
        temperatureSpinBox.valueChanged.connect(lambda value: self.temperature_changed(value, name))
        paramLayout.addRow('Temperature', temperatureSpinBox)

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
        layoutMain.addStretch()

        tabWidget.setLayout(layoutMain)
        tabWidget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)

        return tabWidget

    def get_default_model_for_provider(self, provider_name):
        if provider_name == AIProviderName.OPENAI.value:
            return 'gpt-4.0-mini'
        elif provider_name == AIProviderName.GEMINI.value:
            return 'gemini-2.0-flash'
        elif provider_name == AIProviderName.CLAUDE.value:
            return 'claude-3-7-sonnet-20250219'
        elif provider_name == AIProviderName.OLLAMA.value:
            return ''
        else:
            return ''

    def set_model_list(self, modelList, provider, pattern_name):
        self._settings.setValue("Agent_Pattern/llm", provider)

        if provider == AIProviderName.OPENAI.value:
            api_key = self._settings.value('AI_Provider/OpenAI')
            if api_key:
                modelList.addItems(Utility.get_openai_model_list(api_key))
                llm_model = Utility.get_settings_value(
                    section=f"{pattern_name}_Model_Parameter",
                    prop="model_name",
                    default='gpt-3.5-turbo',
                    save=True
                )
                # Block signals during initial setup
                modelList.blockSignals(True)
                modelList.setCurrentIndex(modelList.findText(llm_model))
                modelList.blockSignals(False)

                # Disconnect any existing connections to avoid multiple connections
                try:
                    modelList.currentTextChanged.disconnect()
                except:
                    pass

                # Connect the signal
                modelList.currentTextChanged.connect(
                    lambda model_name: self.model_list_changed(provider, model_name, pattern_name))

        elif provider == AIProviderName.GEMINI.value:
            api_key = self._settings.value('AI_Provider/Gemini')
            if api_key:
                modelList.addItems(Utility.get_gemini_model_list(api_key))
                llm_model = Utility.get_settings_value(
                    section=f"{pattern_name}_Model_Parameter",
                    prop="model_name",
                    default='gemini-pro',
                    save=True
                )
                # Block signals during initial setup
                modelList.blockSignals(True)
                modelList.setCurrentIndex(modelList.findText(llm_model))
                modelList.blockSignals(False)

                # Disconnect any existing connections to avoid multiple connections
                try:
                    modelList.currentTextChanged.disconnect()
                except:
                    pass

                # Connect the signal
                modelList.currentTextChanged.connect(
                    lambda model_name: self.model_list_changed(provider, model_name, pattern_name))

        elif provider == AIProviderName.CLAUDE.value:
            api_key = self._settings.value('AI_Provider/Claude')
            if api_key:
                modelList.addItems(Utility.get_claude_ai_model_list(api_key))
                llm_model = Utility.get_settings_value(
                    section=f"{pattern_name}_Model_Parameter",
                    prop="model_name",
                    default='claude-3-7-sonnet-20250219',
                    save=True
                )
                # Block signals during initial setup
                modelList.blockSignals(True)
                modelList.setCurrentIndex(modelList.findText(llm_model))
                modelList.blockSignals(False)

                # Disconnect any existing connections to avoid multiple connections
                try:
                    modelList.currentTextChanged.disconnect()
                except:
                    pass

                # Connect the signal
                modelList.currentTextChanged.connect(
                    lambda model_name: self.model_list_changed(provider, model_name, pattern_name))

        elif provider == AIProviderName.OLLAMA.value:
            api_key = self._settings.value('AI_Provider/Ollama')
            if api_key:
                modelList.addItems(Utility.get_ollama_ai_model_list(api_key))
                llm_model = Utility.get_settings_value(
                    section=f"{pattern_name}_Model_Parameter",
                    prop="model_name",
                    default='llama3:8b',
                    save=True
                )
                # Block signals during initial setup
                modelList.blockSignals(True)
                modelList.setCurrentIndex(modelList.findText(llm_model))
                modelList.blockSignals(False)

                # Disconnect any existing connections to avoid multiple connections
                try:
                    modelList.currentTextChanged.disconnect()
                except:
                    pass

                # Connect the signal
                modelList.currentTextChanged.connect(
                    lambda model_name: self.model_list_changed(provider, model_name, pattern_name))

    def select_files(self, llm):
        fileListWidget = self.findChild(QListWidget, f"{llm}_FileList")
        selected_files = self.show_file_explorer(llm)
        for file in selected_files:
            fileListWidget.addItem(file)
        self.update_submit_status(llm)

    def delete_file_from_list(self, llm):
        fileListWidget = self.findChild(QListWidget, f"{llm}_FileList")
        for item in fileListWidget.selectedItems():
            fileListWidget.takeItem(fileListWidget.row(item))
        self.update_submit_status(llm)

    def update_submit_status(self, llm):
        fileListWidget = self.findChild(QListWidget,
                                        f"{llm}_FileList")
        submitButton = self.findChild(QPushButton,
                                      f"{llm}_SubmitButton")
        submitButton.setEnabled(bool(fileListWidget.count()))

    def on_item_selection_changed(self, llm):
        self.reset_file_list(llm)

    def show_file_explorer(self, llm=None):
        file_filter = UI.FILE_FILTER

        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
        file_dialog.setNameFilter(file_filter)

        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            return selected_files
        else:
            return [] if llm != AIProviderName.GEMINI.value else None

    def get_selected_files(self, llm):
        fileListWidget = self.findChild(QListWidget, f"{llm}_FileList")
        return [fileListWidget.item(i).text() for i in range(fileListWidget.count())]

    def reset_file_list(self, agent_pattern, clear: bool = False):
        fileListWidget = self.findChild(QListWidget, f"{agent_pattern}_FileList")
        deleteButton = self.findChild(QPushButton, f"{agent_pattern}_DeleteButton")
        submitButton = self.findChild(QPushButton, f"{agent_pattern}_SubmitButton")

        if fileListWidget is None:
            return

        if clear:
            fileListWidget.clear()

        deleteButton.setEnabled(bool(fileListWidget.selectedItems()))
        submitButton.setEnabled(bool(fileListWidget.count()))

    def submit_file(self, agent_pattern, text):
        if text is None:
            text = self.prompt_text.toPlainText().strip()
        self.submitted_signal.emit(text, agent_pattern)

    def validate_input(self, text, file_list):
        if not file_list:
            self.show_warning(UI.WARNING_TITLE_SELECT_FILE_MESSAGE)
            return False
        if not text:
            self.show_warning(UI.WARNING_TITLE_NO_PROMPT_MESSAGE)
            return False
        return True

    def show_warning(self, message):
        QMessageBox.warning(self, UI.WARNING_TITLE, message)

    def model_list_changed(self, provider, model_name, pattern_name):
        self._settings.setValue(f"{pattern_name}_Model_Parameter/model_name", model_name)
        self.current_llm_signal.emit(provider)
        # Sync with main model combo box if the current provider is active
        if hasattr(self, 'main_model_combo'):
            self.main_model_combo.blockSignals(True)  # Prevent recursive signal calls
            index = self.main_model_combo.findText(model_name)
            if index >= 0:
                self.main_model_combo.setCurrentIndex(index)
            self.main_model_combo.blockSignals(False)

    def maxtokens_changed(self, value, name):
        self._settings.setValue(f"{name}_Model_Parameter/max_tokens", value)

    def temperature_changed(self, value, name):
        self._settings.setValue(f"{name}_Model_Parameter/temperature", value)

    def maxretriess_changed(self, value, name):
        self._settings.setValue(f"{name}_Model_Parameter/max_retries", value)

    def stream_changed(self, checked, name):
        if checked:
            self._settings.setValue(f"{name}_Model_Parameter/stream", 'True')
        else:
            self._settings.setValue(f"{name}_Model_Parameter/stream", 'False')

    def create_prompt_layout(self, name):
        groupSystem = QGroupBox(f"{name} Prompt")
        systemLayout = QFormLayout()
        systemLabel = QLabel(f"Select {name} Prompt")
        systemList = QComboBox()
        systemList.setObjectName(f"{name}_promptList")
        system_values = Utility.get_system_value(section=f"{name}_Prompt", prefix="prompt",
                                                 default="You are a helpful assistant.", length=5)
        systemList.addItems(system_values.keys())
        systemList.currentIndexChanged.connect(lambda: self.on_system_change(name))

        current_system = QTextEdit()
        current_system.setObjectName(f"{name}_current_prompt")
        current_system.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Preferred)
        current_system.setMinimumHeight(100)
        current_system.setMaximumHeight(200)
        current_system.setText(system_values['prompt1'])

        save_system_button = QPushButton(QIcon(Utility.get_icon_path('ico', 'disk-black.png')), 'Save')
        save_system_button.clicked.connect(lambda: self.save_prompt_value(name))

        systemLayout.addRow(systemLabel)
        systemLayout.addRow(systemList)
        systemLayout.addRow(current_system)
        systemLayout.addRow(save_system_button)
        groupSystem.setLayout(systemLayout)
        return groupSystem

    def create_agentdb_tab(self):
        layoutWidget = QWidget()
        layout = QVBoxLayout()

        self._agent_history = AgentHistory(self.model)

        layout.addWidget(self._agent_history)

        layoutWidget.setLayout(layout)
        return layoutWidget

    def create_prompt_tab(self):
        layoutWidget = QWidget()
        layout = QVBoxLayout()

        self._prompt_list = PromptListWidget(table_name=Constants.AGENT_PROMPT_TABLE,
                                             db_connection_name='AgentPromptDBConnection')
        layout.addWidget(self.prompt_list)

        layoutWidget.setLayout(layout)
        return layoutWidget

    def create_system_tab(self):
        layoutWidget = QWidget()
        layout = QVBoxLayout()

        layout.addWidget(QLabel("System"))

        layoutWidget.setLayout(layout)
        return layoutWidget

    def update_ui_submit(self, agentType, text):
        self.ai_answer_scroll_area.verticalScrollBar().rangeChanged.connect(self.adjust_scroll_bar)
        self.add_user_question(agentType, text)
        self.stop_widget.setVisible(True)

    def add_user_question(self, agentType, text):
        user_question = AgentWidget(agentType, text)
        self.result_layout.addWidget(user_question)

    def adjust_scroll_bar(self, min_val, max_val):
        self.ai_answer_scroll_area.verticalScrollBar().setSliderPosition(max_val)

    def update_ui(self, result, stream):
        if stream:
            agentWidget = self.get_last_ai_widget()

            if agentWidget:
                agentWidget.add_text(result)
            else:
                agentWidget = AgentWidget(ChatType.AI)
                agentWidget.add_text(result)
                self.result_layout.addWidget(agentWidget)

        else:
            ai_answer = AgentWidget(ChatType.AI, result)
            self.result_layout.addWidget(ai_answer)

    def disconnect_scroll_range_changed(self):
        try:
            scroll_bar = self.ai_answer_scroll_area.verticalScrollBar()
            if scroll_bar.receivers(scroll_bar.rangeChanged) > 0:
                scroll_bar.rangeChanged.disconnect()
        except (TypeError, RuntimeError):
            print("Scrollbar error")
            pass

    def update_ui_finish(self, model, finish_reason, elapsed_time, stream):
        self.disconnect_scroll_range_changed()
        agentWidget = self.get_last_ai_widget()
        if stream:
            if agentWidget:
                agentWidget.apply_style()
                self.stop_widget.setVisible(False)
        else:
            self.stop_widget.setVisible(False)

        if agentWidget and agentWidget.get_chat_type() == ChatType.AI:
            agentWidget.set_model_name(
                Constants.MODEL_PREFIX + model + Constants.RESPONSE_TIME + format(elapsed_time, ".2f"))

    def get_last_ai_widget(self) -> AgentWidget | None:
        layout_item = self.result_widget.layout().itemAt(self.result_widget.layout().count() - 1)
        if layout_item:
            last_ai_widget = layout_item.widget()
            if last_ai_widget.get_chat_type() == ChatType.AI:
                return last_ai_widget
        else:
            return None

    def handle_submitted_signal(self, text):
        if text:
            self.submit_file(self._current_agent_pattern, text)

    def start_agent(self):
        self.prompt_text.clear()
        self.prompt_text.setEnabled(False)

    def finish_agent(self):
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

    def get_all_text_gemini(self):
        messages = []
        for i in range(self.result_layout.count()):
            current_widget = self.result_layout.itemAt(i).widget()
            text = current_widget.get_text()
            if not text:
                continue
            if current_widget.get_chat_type() == ChatType.HUMAN:
                role = "user"
            elif current_widget.get_chat_type() == ChatType.AI:
                role = "model"
            else:
                continue
            messages.append({
                "role": role,
                "parts": [types.Part.from_text(text=text)]
            })
        return messages

    def create_args(self, text, agent_llm, agent_pattern):
        method_name = f'create_{agent_pattern.lower()}_args_{agent_llm.lower()}'
        method = getattr(self, method_name, None)
        if callable(method):
            return method(text, agent_llm, agent_pattern)
        else:
            raise ValueError(f'{UI.METHOD} {method_name} {UI.NOT_FOUND}')

    def create_orchestrator_args_openai(self, text, agent_llm, agent_pattern):
        api_key = self._settings.value(f'AI_Provider/{agent_llm}')
        model = self.findChild(QComboBox, f'{agent_pattern}_ModelList').currentText()

        stream = self.findChild(QCheckBox,
                                f'{agent_pattern}_streamCheckbox').isChecked()

        max_tokens_spin_box = self.findChild(CheckSpinBox,
                                             f'{agent_pattern}_max_tokensSpinBox').spin_box
        max_tokens = max_tokens_spin_box.value() if max_tokens_spin_box.isEnabled() else None

        temperature_spin_box = self.findChild(CheckDoubleSpinBox,
                                              f'{agent_pattern}_temperatureSpinBox').spin_box
        temperature = temperature_spin_box.value() if temperature_spin_box.isEnabled() else None

        orchestrator_prompt = self.findChild(QTextEdit,
                                             f'{AgentPattern.ORCHESTRATOR.value}_current_prompt').toPlainText()
        worker_prompt = self.findChild(QTextEdit, f'{AgentPattern.WORKER.value}_current_prompt').toPlainText()
        aggregator_prompt = self.findChild(QTextEdit, f'{AgentPattern.AGGREGATOR.value}_current_prompt').toPlainText()

        formatted_orchestrator_prompt = orchestrator_prompt.replace("{user_query}", text)
        formatted_worker_prompt = worker_prompt.replace("{user_query}", text)
        formatted_aggregator_prompt = aggregator_prompt.replace("{user_query}", text)

        messages = [
            {"role": "user", "content": formatted_orchestrator_prompt}
        ]

        ai_arg = {
            'model': model,
            'messages': messages,
            'stream': stream,
        }

        # If the model provider starts with 'o1' or 'o3' or 'o4' then remove max_tokens,  temperature, top_p, frequency_penalty
        # presence_penalty, seed
        o1_o3_o4_model = model.lower().startswith(("o1", "o3", "o4"))
        if not o1_o3_o4_model:
            ai_arg['max_tokens'] = max_tokens
            ai_arg['temperature'] = temperature

        args = {
            'api_key': api_key,
            'ai_arg': ai_arg,
            'user_query': text,
            'orchestrator_prompt': formatted_orchestrator_prompt,
            'worker_prompt': formatted_worker_prompt,
            'aggregator_prompt': formatted_aggregator_prompt,
        }

        return args

    def create_orchestrator_args_claude(self, text, agent_llm, agent_pattern):
        api_key = self._settings.value(f'AI_Provider/{agent_llm}')
        model = self.findChild(QComboBox, f'{agent_pattern}_ModelList').currentText()

        stream = self.findChild(QCheckBox,
                                f'{agent_pattern}_streamCheckbox').isChecked()

        max_tokens_spin_box = self.findChild(CheckSpinBox,
                                             f'{agent_pattern}_max_tokensSpinBox').spin_box
        max_tokens = max_tokens_spin_box.value() if max_tokens_spin_box.isEnabled() else None

        temperature_spin_box = self.findChild(CheckDoubleSpinBox,
                                              f'{agent_pattern}_temperatureSpinBox').spin_box
        temperature = temperature_spin_box.value() if temperature_spin_box.isEnabled() else None

        orchestrator_prompt = self.findChild(QTextEdit,
                                             f'{AgentPattern.ORCHESTRATOR.value}_current_prompt').toPlainText()
        worker_prompt = self.findChild(QTextEdit, f'{AgentPattern.WORKER.value}_current_prompt').toPlainText()
        aggregator_prompt = self.findChild(QTextEdit, f'{AgentPattern.AGGREGATOR.value}_current_prompt').toPlainText()

        formatted_orchestrator_prompt = orchestrator_prompt.replace("{user_query}", text)
        formatted_worker_prompt = worker_prompt.replace("{user_query}", text)
        formatted_aggregator_prompt = aggregator_prompt.replace("{user_query}", text)

        messages = [
            {"role": "user", "content": formatted_orchestrator_prompt},
        ]

        ai_arg = {
            'model': model,
            'messages': messages,
            'stream': stream,
            'max_tokens': max_tokens,
            'temperature': temperature
        }

        args = {
            'api_key': api_key,
            'ai_arg': ai_arg,
            'user_query': text,
            'orchestrator_prompt': formatted_orchestrator_prompt,
            'worker_prompt': formatted_worker_prompt,
            'aggregator_prompt': formatted_aggregator_prompt,
        }

        return args

    def create_orchestrator_args_gemini(self, text, agent_llm, agent_pattern):
        api_key = self._settings.value(f'AI_Provider/{agent_llm}')
        model = self.findChild(QComboBox, f'{agent_pattern}_ModelList').currentText()

        stream = self.findChild(QCheckBox,
                                f'{agent_pattern}_streamCheckbox').isChecked()

        max_output_tokens_spin_box = self.findChild(CheckSpinBox,
                                                    f'{agent_pattern}_max_tokensSpinBox').spin_box
        max_output_tokens = max_output_tokens_spin_box.value() if max_output_tokens_spin_box.isEnabled() else None

        temperatue_spin_box = self.findChild(CheckDoubleSpinBox,
                                             f'{agent_pattern}_temperatureSpinBox').spin_box
        temperature = temperatue_spin_box.value() if temperatue_spin_box.isEnabled() else None

        orchestrator_prompt = self.findChild(QTextEdit,
                                             f'{AgentPattern.ORCHESTRATOR.value}_current_prompt').toPlainText()
        worker_prompt = self.findChild(QTextEdit, f'{AgentPattern.WORKER.value}_current_prompt').toPlainText()
        aggregator_prompt = self.findChild(QTextEdit, f'{AgentPattern.AGGREGATOR.value}_current_prompt').toPlainText()

        formatted_orchestrator_prompt = orchestrator_prompt.replace("{user_query}", text)
        formatted_worker_prompt = worker_prompt.replace("{user_query}", text)
        formatted_aggregator_prompt = aggregator_prompt.replace("{user_query}", text)

        content = [
            types.Part.from_text(text=text.strip()),
            types.Part.from_text(text=formatted_orchestrator_prompt)
        ]

        messages = [
            {
                "role": "user",
                "parts": content
            }
        ]

        config = {
            'max_output_tokens': max_output_tokens,
            'temperature': temperature,
            'tools': []
        }

        config['safety_settings'] = self.create_safety_settings()

        ai_arg = {
            'model': model,
            'messages': messages,
            'stream': stream,
            'config': config,
        }

        args = {
            'api_key': api_key,
            'ai_arg': ai_arg,
            'user_query': text,
            'orchestrator_prompt': formatted_orchestrator_prompt,
            'worker_prompt': formatted_worker_prompt,
            'aggregator_prompt': formatted_aggregator_prompt,
        }

        return args

    def create_orchestrator_args_ollama(self, text, agent_llm, agent_pattern):
        api_key = self._settings.value(f'AI_Provider/{agent_llm}')
        model = self.findChild(QComboBox, f'{agent_pattern}_ModelList').currentText()

        stream = self.findChild(QCheckBox,
                                f'{agent_pattern}_streamCheckbox').isChecked()

        max_tokens_spin_box = self.findChild(CheckSpinBox,
                                             f'{agent_pattern}_max_tokensSpinBox').spin_box
        max_tokens = max_tokens_spin_box.value() if max_tokens_spin_box.isEnabled() else None

        temperature_spin_box = self.findChild(CheckDoubleSpinBox,
                                              f'{agent_pattern}_temperatureSpinBox').spin_box
        temperature = temperature_spin_box.value() if temperature_spin_box.isEnabled() else None

        orchestrator_prompt = self.findChild(QTextEdit,
                                             f'{AgentPattern.ORCHESTRATOR.value}_current_prompt').toPlainText()
        worker_prompt = self.findChild(QTextEdit, f'{AgentPattern.WORKER.value}_current_prompt').toPlainText()
        aggregator_prompt = self.findChild(QTextEdit, f'{AgentPattern.AGGREGATOR.value}_current_prompt').toPlainText()

        formatted_orchestrator_prompt = orchestrator_prompt.replace("{user_query}", text)
        formatted_worker_prompt = worker_prompt.replace("{user_query}", text)
        formatted_aggregator_prompt = aggregator_prompt.replace("{user_query}", text)

        messages = [
            {"role": "user", "content": formatted_orchestrator_prompt}
        ]

        options = {
            'temperature:': temperature,
            'num_predict': max_tokens,
        }

        ai_arg = {
            'model': model,
            'messages': messages,
            'stream': stream,
            'options': options,
        }

        args = {
            'api_key': api_key,
            'ai_arg': ai_arg,
            'user_query': text,
            'orchestrator_prompt': formatted_orchestrator_prompt,
            'worker_prompt': formatted_worker_prompt,
            'aggregator_prompt': formatted_aggregator_prompt,
        }

        return args

    def create_evaluator_args_openai(self, text, agent_llm, agent_pattern):
        api_key = self._settings.value(f'AI_Provider/{agent_llm}')
        model = self.findChild(QComboBox, f'{agent_pattern}_ModelList').currentText()

        if model.startswith("o1-mini") or model.startswith("o1-preview"):
            system_role = "user"
        elif model.startswith("o1") or model.startswith("o3") or model.startswith("o4"):
            system_role = "developer"
        else:
            system_role = "system"

        stream = self.findChild(QCheckBox,
                                f'{agent_pattern}_streamCheckbox').isChecked()

        max_tokens_spin_box = self.findChild(CheckSpinBox,
                                             f'{agent_pattern}_max_tokensSpinBox').spin_box
        max_tokens = max_tokens_spin_box.value() if max_tokens_spin_box.isEnabled() else None

        temperature_spin_box = self.findChild(CheckDoubleSpinBox,
                                              f'{agent_pattern}_temperatureSpinBox').spin_box
        temperature = temperature_spin_box.value() if temperature_spin_box.isEnabled() else None

        max_retries_spin_box = self.findChild(CheckSpinBox,
                                              f'{agent_pattern}_max_retriesSpinBox').spin_box
        max_retries = max_retries_spin_box.value() if max_retries_spin_box.isEnabled() else 1

        evaluator_prompt = self.findChild(QTextEdit,
                                          f'{AgentPattern.EVALUATOR.value}_current_prompt').toPlainText()
        generator_prompt = self.findChild(QTextEdit, f'{AgentPattern.GENERATOR.value}_current_prompt').toPlainText()
        task_prompt = self.findChild(QTextEdit, f'{AgentPattern.TASK.value}_current_prompt').toPlainText()

        messages = [
            {"role": "user", "content": evaluator_prompt}
        ]

        ai_arg = {
            'model': model,
            'messages': messages,
            'stream': stream,
        }

        o1_o3_o4_model = model.lower().startswith(("o1", "o3", "o4"))
        if not o1_o3_o4_model:
            ai_arg['max_tokens'] = max_tokens
            ai_arg['temperature'] = temperature

        args = {
            'api_key': api_key,
            'ai_arg': ai_arg,
            'user_query': text,
            'max_retries': max_retries,
            'evaluator_prompt': evaluator_prompt,
            'generator_prompt': generator_prompt,
            'task_prompt': task_prompt,
        }

        return args

    def create_evaluator_args_claude(self, text, agent_llm, agent_pattern):
        api_key = self._settings.value(f'AI_Provider/{agent_llm}')
        model = self.findChild(QComboBox, f'{agent_pattern}_ModelList').currentText()

        stream = self.findChild(QCheckBox,
                                f'{agent_pattern}_streamCheckbox').isChecked()

        max_tokens_spin_box = self.findChild(CheckSpinBox,
                                             f'{agent_pattern}_max_tokensSpinBox').spin_box
        max_tokens = max_tokens_spin_box.value() if max_tokens_spin_box.isEnabled() else None

        temperature_spin_box = self.findChild(CheckDoubleSpinBox,
                                              f'{agent_pattern}_temperatureSpinBox').spin_box
        temperature = temperature_spin_box.value() if temperature_spin_box.isEnabled() else None

        max_retries_spin_box = self.findChild(CheckSpinBox,
                                              f'{agent_pattern}_max_retriesSpinBox').spin_box
        max_retries = max_retries_spin_box.value() if max_retries_spin_box.isEnabled() else 1

        evaluator_prompt = self.findChild(QTextEdit,
                                          f'{AgentPattern.EVALUATOR.value}_current_prompt').toPlainText()
        generator_prompt = self.findChild(QTextEdit, f'{AgentPattern.GENERATOR.value}_current_prompt').toPlainText()
        task_prompt = self.findChild(QTextEdit, f'{AgentPattern.TASK.value}_current_prompt').toPlainText()

        messages = [
            {"role": "user", "content": evaluator_prompt},
        ]

        ai_arg = {
            'model': model,
            'messages': messages,
            'stream': stream,
            'max_tokens': max_tokens,
            'temperature': temperature
        }

        args = {
            'api_key': api_key,
            'ai_arg': ai_arg,
            'user_query': text,
            'max_retries': max_retries,
            'evaluator_prompt': evaluator_prompt,
            'generator_prompt': generator_prompt,
            'task_prompt': task_prompt,
        }

        return args

    def create_evaluator_args_ollama(self, text, agent_llm, agent_pattern):
        api_key = self._settings.value(f'AI_Provider/{agent_llm}')
        model = self.findChild(QComboBox, f'{agent_pattern}_ModelList').currentText()

        stream = self.findChild(QCheckBox,
                                f'{agent_pattern}_streamCheckbox').isChecked()

        max_tokens_spin_box = self.findChild(CheckSpinBox,
                                             f'{agent_pattern}_max_tokensSpinBox').spin_box
        max_tokens = max_tokens_spin_box.value() if max_tokens_spin_box.isEnabled() else None

        temperature_spin_box = self.findChild(CheckDoubleSpinBox,
                                              f'{agent_pattern}_temperatureSpinBox').spin_box
        temperature = temperature_spin_box.value() if temperature_spin_box.isEnabled() else None

        max_retries_spin_box = self.findChild(CheckSpinBox,
                                              f'{agent_pattern}_max_retriesSpinBox').spin_box
        max_retries = max_retries_spin_box.value() if max_retries_spin_box.isEnabled() else 1

        evaluator_prompt = self.findChild(QTextEdit,
                                          f'{AgentPattern.EVALUATOR.value}_current_prompt').toPlainText()
        generator_prompt = self.findChild(QTextEdit, f'{AgentPattern.GENERATOR.value}_current_prompt').toPlainText()
        task_prompt = self.findChild(QTextEdit, f'{AgentPattern.TASK.value}_current_prompt').toPlainText()

        messages = [
            {"role": "user", "content": evaluator_prompt}
        ]

        options = {
            'temperature:': temperature,
            'num_predict': max_tokens,
        }

        ai_arg = {
            'model': model,
            'messages': messages,
            'stream': stream,
            'options': options,
        }

        args = {
            'api_key': api_key,
            'ai_arg': ai_arg,
            'user_query': text,
            'max_retries': max_retries,
            'evaluator_prompt': evaluator_prompt,
            'generator_prompt': generator_prompt,
            'task_prompt': task_prompt,
        }

        return args

    def create_evaluator_args_gemini(self, text, agent_llm, agent_pattern):
        api_key = self._settings.value(f'AI_Provider/{agent_llm}')
        model = self.findChild(QComboBox, f'{agent_pattern}_ModelList').currentText()

        stream = self.findChild(QCheckBox,
                                f'{agent_pattern}_streamCheckbox').isChecked()

        max_output_tokens_spin_box = self.findChild(CheckSpinBox,
                                                    f'{agent_pattern}_max_tokensSpinBox').spin_box
        max_output_tokens = max_output_tokens_spin_box.value() if max_output_tokens_spin_box.isEnabled() else None

        temperatue_spin_box = self.findChild(CheckDoubleSpinBox,
                                             f'{agent_pattern}_temperatureSpinBox').spin_box
        temperature = temperatue_spin_box.value() if temperatue_spin_box.isEnabled() else None

        max_retries_spin_box = self.findChild(CheckSpinBox,
                                              f'{agent_pattern}_max_retriesSpinBox').spin_box
        max_retries = max_retries_spin_box.value() if max_retries_spin_box.isEnabled() else 1

        evaluator_prompt = self.findChild(QTextEdit,
                                          f'{AgentPattern.EVALUATOR.value}_current_prompt').toPlainText()
        generator_prompt = self.findChild(QTextEdit, f'{AgentPattern.GENERATOR.value}_current_prompt').toPlainText()
        task_prompt = self.findChild(QTextEdit, f'{AgentPattern.TASK.value}_current_prompt').toPlainText()

        content = [
            types.Part.from_text(text=text.strip()),
            types.Part.from_text(text=evaluator_prompt)
        ]

        messages = [
            {
                "role": "user",
                "parts": content
            }
        ]

        config = {
            'max_output_tokens': max_output_tokens,
            'temperature': temperature,
            'tools': []
        }

        config['safety_settings'] = self.create_safety_settings()

        ai_arg = {
            'model': model,
            'messages': messages,
            'stream': stream,
            'config': config,
        }

        args = {
            'api_key': api_key,
            'ai_arg': ai_arg,
            'user_query': text,
            'max_retries': max_retries,
            'evaluator_prompt': evaluator_prompt,
            'generator_prompt': generator_prompt,
            'task_prompt': task_prompt,
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
    def agent_history(self):
        return self._agent_history

    @property
    def prompt_list(self):
        return self._prompt_list
