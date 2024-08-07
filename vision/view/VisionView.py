from functools import partial

from PIL import Image
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QSizePolicy, QScrollArea, QSplitter, \
    QTabWidget, QGroupBox, QFormLayout, QLabel, QComboBox, QCheckBox, QTextEdit, QFileDialog, QListWidget, QMessageBox

from chat.view.ChatWidget import ChatWidget
from custom.CheckComboBox import CheckComboBox
from custom.CheckSpinBox import CheckSpinBox
from custom.PromptTextEdit import PromptTextEdit
from util.ChatType import ChatType
from util.Constants import AIProviderName, Constants, UI
from util.SettingsManager import SettingsManager
from util.Utility import Utility
from vision.view.ImageListWidget import ImageListWidget
from vision.view.VisionHistory import VisionHistory


class VisionView(QWidget):
    submitted_signal = pyqtSignal(str, list)
    stop_signal = pyqtSignal()
    current_llm_signal = pyqtSignal(str)

    def __init__(self, model):
        super().__init__()
        self.model = model
        self._settings = SettingsManager.get_settings()
        self._current_llm = Utility.get_settings_value(section="AI_Provider", prop="llm",
                                                       default="OpenAI", save=True)

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
        self.prompt_text.setPlaceholderText(UI.CHAT_PROMPT_PLACEHOLDER)
        self.prompt_text.submitted_signal.connect(self.handle_submitted_signal)

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
        vision_icon = QIcon(Utility.get_icon_path('ico', 'picture--pencil.png'))
        self.config_tabs.addTab(self.create_parameters_tab(), vision_icon, UI.VISION)
        self.config_tabs.addTab(self.create_visiondb_tab(), vision_icon, UI.VISION_LIST)

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

    def adjust_scroll_bar(self, min_val, max_val):
        self.ai_answer_scroll_area.verticalScrollBar().setSliderPosition(max_val)

    def create_visiondb_tab(self):
        layoutWidget = QWidget()
        layout = QVBoxLayout()

        self._vision_history = VisionHistory(self.model)

        layout.addWidget(self._vision_history)

        layoutWidget.setLayout(layout)
        return layoutWidget

    def create_parameters_tab(self):
        layoutWidget = QWidget()
        layout = QVBoxLayout()

        # Tabs for LLM
        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_openai_tabcontent(AIProviderName.OPENAI.value), AIProviderName.OPENAI.value)
        self.tabs.addTab(self.create_gemini_tabcontent(AIProviderName.GEMINI.value), AIProviderName.GEMINI.value)
        self.tabs.addTab(self.create_claude_tabcontent(AIProviderName.CLAUDE.value), AIProviderName.CLAUDE.value)
        self.tabs.currentChanged.connect(self.on_tab_change)
        layout.addWidget(self.tabs)

        layoutWidget.setLayout(layout)
        return layoutWidget

    def on_tab_change(self, index):
        self._current_llm = self.tabs.tabText(index)
        self._settings.setValue('AI_Provider/llm', self._current_llm)
        self.current_llm_signal.emit(self._current_llm)

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

        # detail : only dall-e-3 have vivid or natural option
        detailComboBox = CheckComboBox()
        detailComboBox.setObjectName(f"{name}_detailComboBox")
        detailComboBox.combo_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        detailComboBox.combo_box.addItems(Constants.VISION_DETAIL_LIST)
        detailComboBox.combo_box.setCurrentText(
            Utility.get_settings_value(section=f"{name}_Vision_Parameter", prop="detail",
                                       default="auto", save=True)
        )
        detailComboBox.currentTextChanged.connect(lambda value: self.detail_changed(value, name))
        paramLayout.addRow('Style', detailComboBox)

        max_tokensSpinBox = CheckSpinBox()
        max_tokensSpinBox.setObjectName(f"{name}_max_tokensSpinBox")
        max_tokensSpinBox.spin_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        max_tokensSpinBox.spin_box.setRange(0, 128000)
        max_tokensSpinBox.spin_box.setAccelerated(True)
        max_tokensSpinBox.spin_box.setSingleStep(1)
        max_tokensSpinBox.spin_box.setValue(
            int(
                Utility.get_settings_value(section=f"{name}_Vision_Parameter", prop="max_tokens",
                                           default="2048", save=True)))
        max_tokensSpinBox.check_box.setEnabled(False)
        max_tokensSpinBox.valueChanged.connect(lambda value: self.maxtokens_changed(value, name))
        paramLayout.addRow('Max Tokens', max_tokensSpinBox)

        groupParam.setLayout(paramLayout)
        layoutMain.addWidget(groupParam)

        optionGroup = QGroupBox(f"{name} Options")
        optionLayout = QVBoxLayout()

        streamCheckbox = QCheckBox("Stream")
        streamCheckbox.setObjectName(f"{name}_streamCheckbox")
        streamCheckbox.setChecked(
            (Utility.get_settings_value(section=f"{name}_Vision_Parameter", prop="stream", default="True",
                                        save=True)) == "True")
        streamCheckbox.toggled.connect(lambda value: self.stream_changed(value, name))
        optionLayout.addWidget(streamCheckbox)
        optionGroup.setLayout(optionLayout)
        layoutMain.addWidget(optionGroup)

        # Add QListWidget to show selected image list
        fileListGroup = QGroupBox(f"{name} Image List")
        fileListLayout = QVBoxLayout()
        fileListGroup.setLayout(fileListLayout)

        # Add QListWidget to show selected image list
        imageListWidget = QListWidget()
        imageListWidget.setObjectName(f"{name}_ImageList")
        fileListLayout.addWidget(imageListWidget)

        # Add buttons
        buttonLayout = QHBoxLayout()
        selectButton = QPushButton(QIcon(Utility.get_icon_path('ico', 'folder-open-image.png')), "Images")
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

        selectButton.clicked.connect(partial(self.select_image_files, name))
        deleteButton.clicked.connect(partial(self.delete_image_list, name))
        submitButton.clicked.connect(partial(self.submit_file, name, None))

        imageListWidget.itemSelectionChanged.connect(partial(self.on_item_selection_changed, name))

        layoutMain.addWidget(fileListGroup)

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

        max_output_tokensSpinBox = CheckSpinBox()
        max_output_tokensSpinBox.setObjectName(f"{name}_max_output_tokensSpinBox")
        max_output_tokensSpinBox.spin_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        max_output_tokensSpinBox.spin_box.setRange(0, 2048)
        max_output_tokensSpinBox.spin_box.setAccelerated(True)
        max_output_tokensSpinBox.spin_box.setSingleStep(1)
        max_output_tokensSpinBox.spin_box.setValue(
            int(
                Utility.get_settings_value(section=f"{name}_Vision_Parameter", prop="max_output_tokens",
                                           default="2048", save=True)))
        max_output_tokensSpinBox.check_box.setEnabled(False)
        max_output_tokensSpinBox.valueChanged.connect(lambda value: self.maxoutput_tokens_changed(value, name))
        paramLayout.addRow('Max Tokens', max_output_tokensSpinBox)

        groupParam.setLayout(paramLayout)
        layoutMain.addWidget(groupParam)

        optionGroup = QGroupBox(f"{name} Options")
        optionLayout = QVBoxLayout()

        streamCheckbox = QCheckBox("Stream")
        streamCheckbox.setObjectName(f"{name}_streamCheckbox")
        streamCheckbox.setChecked(
            (Utility.get_settings_value(section=f"{name}_Vision_Parameter", prop="stream", default="True",
                                        save=True)) == "True")
        streamCheckbox.toggled.connect(lambda value: self.stream_changed(value, name))
        optionLayout.addWidget(streamCheckbox)
        optionGroup.setLayout(optionLayout)

        layoutMain.addWidget(optionGroup)

        fileListGroup = QGroupBox(f"{name} Image List")
        fileListLayout = QVBoxLayout()
        fileListGroup.setLayout(fileListLayout)

        # Add QListWidget to show selected image list
        imageListWidget = QListWidget()
        imageListWidget.setObjectName(f"{name}_ImageList")
        fileListLayout.addWidget(imageListWidget)

        # Add buttons
        buttonLayout = QHBoxLayout()
        selectButton = QPushButton(QIcon(Utility.get_icon_path('ico', 'folder-open-image.png')), "Images")
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

        selectButton.clicked.connect(partial(self.select_image_files, name))
        deleteButton.clicked.connect(partial(self.delete_image_list, name))
        submitButton.clicked.connect(partial(self.submit_file, name, None))

        imageListWidget.itemSelectionChanged.connect(partial(self.on_item_selection_changed, name))

        layoutMain.addWidget(fileListGroup)

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

        max_tokensSpinBox = CheckSpinBox()
        max_tokensSpinBox.setObjectName(f"{name}_max_tokensSpinBox")
        max_tokensSpinBox.spin_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        max_tokensSpinBox.spin_box.setRange(0, 4096)
        max_tokensSpinBox.spin_box.setAccelerated(True)
        max_tokensSpinBox.spin_box.setSingleStep(1)
        max_tokensSpinBox.spin_box.setValue(
            int(
                Utility.get_settings_value(section=f"{name}_Vision_Parameter", prop="max_tokens",
                                           default="2048", save=True)))
        max_tokensSpinBox.check_box.setEnabled(False)
        max_tokensSpinBox.valueChanged.connect(lambda value: self.maxtokens_changed(value, name))
        paramLayout.addRow('Max Tokens', max_tokensSpinBox)

        groupParam.setLayout(paramLayout)
        layoutMain.addWidget(groupParam)

        optionGroup = QGroupBox(f"{name} Options")
        optionLayout = QVBoxLayout()

        streamCheckbox = QCheckBox("Stream")
        streamCheckbox.setObjectName(f"{name}_streamCheckbox")
        streamCheckbox.setChecked(
            (Utility.get_settings_value(section=f"{name}_Vision_Parameter", prop="stream", default="True",
                                        save=True)) == "True")
        streamCheckbox.toggled.connect(lambda value: self.stream_changed(value, name))
        optionLayout.addWidget(streamCheckbox)
        optionGroup.setLayout(optionLayout)
        layoutMain.addWidget(optionGroup)

        # Add QListWidget to show selected image list
        fileListGroup = QGroupBox(f"{name} Image List")
        fileListLayout = QVBoxLayout()
        fileListGroup.setLayout(fileListLayout)

        # Add QListWidget to show selected image list
        imageListWidget = QListWidget()
        imageListWidget.setObjectName(f"{name}_ImageList")
        fileListLayout.addWidget(imageListWidget)

        # Add buttons
        buttonLayout = QHBoxLayout()
        selectButton = QPushButton(QIcon(Utility.get_icon_path('ico', 'folder-open-image.png')), "Images")
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

        selectButton.clicked.connect(partial(self.select_image_files, name))
        deleteButton.clicked.connect(partial(self.delete_image_list, name))
        submitButton.clicked.connect(partial(self.submit_file, name, None))

        imageListWidget.itemSelectionChanged.connect(partial(self.on_item_selection_changed, name))

        layoutMain.addWidget(fileListGroup)

        tabWidget.setLayout(layoutMain)

        return tabWidget

    def select_image_files(self, llm):
        imageListWidget = self.findChild(QListWidget, f"{llm}_ImageList")
        selected_files = self.show_image_files_dialog(llm)
        for file in selected_files:
            imageListWidget.addItem(file)
        self.update_submit_status(llm)

    def delete_image_list(self, llm):
        imageListWidget = self.findChild(QListWidget, f"{llm}_ImageList")
        for item in imageListWidget.selectedItems():
            imageListWidget.takeItem(imageListWidget.row(item))
        self.update_submit_status(llm)

    def update_submit_status(self, llm):
        imageListWidget = self.findChild(QListWidget,
                                         f"{llm}_ImageList")
        submitButton = self.findChild(QPushButton,
                                      f"{llm}_SubmitButton")
        submitButton.setEnabled(bool(imageListWidget.count()))

    def on_item_selection_changed(self, llm):
        imageListWidget = self.findChild(QListWidget,
                                         f"{llm}_ImageList")
        deleteButton = self.findChild(QPushButton,
                                      f"{llm}_DeleteButton")
        deleteButton.setEnabled(bool(imageListWidget.selectedItems()))

        submitButton = self.findChild(QPushButton,
                                      f"{llm}_SubmitButton")
        submitButton.setEnabled(bool(imageListWidget.count()))

    def show_image_files_dialog(self, llm=None):
        file_filter = UI.VISION_IMAGE_FILTER

        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
        file_dialog.setNameFilter(file_filter)

        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            return selected_files
        else:
            return [] if llm != AIProviderName.GEMINI.value else None

    def get_selected_files(self, llm):
        imageListWidget = self.findChild(QListWidget, f"{llm}_ImageList")
        return [imageListWidget.item(i).text() for i in range(imageListWidget.count())]

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

        detailComboBox = self.findChild(CheckComboBox,
                                        f'{self._current_llm}_detailComboBox').combo_box
        detail = detailComboBox.currentText() if detailComboBox.isEnabled() else 'auto'

        max_tokens_spin_box = self.findChild(CheckSpinBox,
                                             f'{llm}_max_tokensSpinBox').spin_box
        max_tokens = max_tokens_spin_box.value() if max_tokens_spin_box.isEnabled() else None

        stream = self.findChild(QCheckBox,
                                f'{llm}_streamCheckbox').isChecked()

        file_list = self.get_selected_files(llm)

        content = []
        if file_list:
            for file in file_list:
                content.append(
                    {
                        'type': 'image_url',
                        'image_url': {
                            'url': f'data:image/jpeg;base64,{Utility.base64_encode_file(file)}',
                            'detail': detail
                        }
                    }
                )
        content.append({
            'type': 'text',
            'text': text
        })

        messages = [
            {"role": "user", "content": content}
        ]

        ai_arg = {
            'model': model,
            'messages': messages,
            'max_tokens': max_tokens,
            'stream': stream,
        }

        args = {
            'api_key': api_key,
            'ai_arg': ai_arg,
        }

        return args

    def create_args_claude(self, text, llm):
        api_key = self._settings.value(f'AI_Provider/{llm}')
        model = self.findChild(QComboBox, f'{llm}_ModelList').currentText()
        system = self.findChild(QTextEdit, f'{llm}_current_system').toPlainText()
        max_tokens_spin_box = self.findChild(CheckSpinBox,
                                             f'{llm}_max_tokensSpinBox').spin_box
        max_tokens = max_tokens_spin_box.value() if max_tokens_spin_box.isEnabled() else None
        stream = self.findChild(QCheckBox,
                                f'{llm}_streamCheckbox').isChecked()

        file_list = self.get_selected_files(llm)

        content = []
        if file_list:
            media_type_mapping = {
                'jpeg': 'image/jpeg',
                'jpg': 'image/jpg',
                'png': 'image/png',
                'gif': 'image/gif',
                'webp': 'image/webp'
            }
            for index, file_name in enumerate(file_list):
                file_extension = file_name.split('.')[-1].lower()
                media_type = media_type_mapping.get(file_extension)
                image_data = Utility.base64_encode_file(file_name)
                content.append({
                    'type': 'text',
                    'text': f'Image {index + 1}:'
                })
                content.append({
                    'type': 'image',
                    'source': {
                        'type': 'base64',
                        'media_type': media_type,
                        'data': image_data
                    }
                })
        content.append({
            'type': 'text',
            'text': text
        })

        messages = [
            {"role": "user", "content": content}
        ]

        ai_arg = {
            'model': model,
            'messages': messages,
            'system': system,
            'max_tokens': max_tokens,
            'stream': stream,
        }

        args = {
            'api_key': api_key,
            'ai_arg': ai_arg,
        }

        return args

    def create_args_gemini(self, text, llm):
        api_key = self._settings.value(f'AI_Provider/{llm}')
        model = self.findChild(QComboBox, f'{llm}_ModelList').currentText()
        file = self.get_selected_files(llm)
        img = Image.open(file[0])

        messages = [text, img]

        stream = self.findChild(QCheckBox,
                                f'{llm}_streamCheckbox').isChecked()

        max_output_tokens_spin_box = self.findChild(CheckSpinBox,
                                                    f'{llm}_max_output_tokensSpinBox').spin_box
        max_output_tokens = max_output_tokens_spin_box.value() if max_output_tokens_spin_box.isEnabled() else None

        system = self.findChild(QTextEdit, f'{llm}_current_system').toPlainText()

        config = {
            'max_output_tokens': max_output_tokens,
        }

        ai_arg = {
            'model': model,
            'messages': messages,
            'config': config,
            'system': system,
            'stream': stream,
        }

        args = {
            'api_key': api_key,
            'ai_arg': ai_arg,
        }

        return args

    def set_model_list(self, modelList, name):
        if name == AIProviderName.OPENAI.value:
            modelList.addItems(Constants.VISION_MODEL_LIST)
            current_model = Utility.get_settings_value(section=f"{name}_Vision_Parameter", prop="vision_model",
                                                       default="gpt-4o", save=True)
            modelList.setCurrentText(current_model)
            modelList.currentTextChanged.connect(lambda current_text: self.model_list_changed(current_text, name))
        elif name == AIProviderName.CLAUDE.value:
            api_key = self._settings.value(f'AI_Provider/{name}')
            modelList.addItems(Utility.get_claude_ai_model_list(api_key))
            current_model = Utility.get_settings_value(section=f"{name}_Vision_Parameter", prop="vision_model",
                                                       default="claude-3-opus-20240229", save=True)
            modelList.setCurrentText(current_model)
            modelList.currentTextChanged.connect(lambda current_text: self.model_list_changed(current_text, name))
        elif name == AIProviderName.GEMINI.value:
            api_key = self._settings.value(f'AI_Provider/{name}')
            modelList.addItems(Utility.get_gemini_vision_model_list(api_key))
            current_model = Utility.get_settings_value(section=f"{name}_Vision_Parameter", prop="vision_model",
                                                       default="gemini-1.5-pro", save=True)
            modelList.setCurrentText(current_model)
            modelList.currentTextChanged.connect(lambda current_text: self.model_list_changed(current_text, name))

    def model_list_changed(self, model, llm):
        self._settings.setValue(f"{llm}_Vision_Parameter/vision_model", model)

    def submit_file(self, llm, text):
        if text is None:
            text = self.prompt_text.toPlainText()
        file_list = self.get_selected_files(llm)
        if not self.validate_input(text, file_list):
            return
        if text and file_list:
            self.submitted_signal.emit(text, file_list)

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

    def handle_submitted_signal(self, text):
        file_list = self.get_selected_files(self._current_llm)
        if not file_list:
            QMessageBox.warning(self, UI.WARNING_TITLE, UI.WARNING_TITLE_SELECT_FILE_MESSAGE)
            return
        if text and file_list:
            self.submitted_signal.emit(text, file_list)

    def add_user_question(self, chatType, text, file_list):
        user_question = ImageListWidget(chatType, text, file_list)
        self.result_layout.addWidget(user_question)

    def add_ai_answer(self, chatType, text, model):
        ai_answer = ChatWidget.with_model(chatType, text, model)
        self.result_layout.addWidget(ai_answer)

    def update_ui_submit(self, chatType, text, file_list):
        self.ai_answer_scroll_area.verticalScrollBar().rangeChanged.connect(self.adjust_scroll_bar)
        self.add_user_question(chatType, text, file_list)
        self.stop_widget.setVisible(True)

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
        imageListWidget = self.findChild(QListWidget, f"{self._current_llm}_ImageList")
        imageListWidget.clear()

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

    def set_default_tab(self, name):
        index = self.tabs.indexOf(self.tabs.findChild(QWidget, name))
        if index != -1:
            self.tabs.setCurrentIndex(index)

    def get_last_ai_widget(self) -> ChatWidget | None:
        layout_item = self.result_widget.layout().itemAt(self.result_widget.layout().count() - 1)
        if layout_item:
            last_ai_widget = layout_item.widget()
            if last_ai_widget.get_chat_type() == ChatType.AI:
                return last_ai_widget
        else:
            return None

    def detail_changed(self, value, name):
        self._settings.setValue(f"{name}_Vision_Parameter/detail", value)

    def maxtokens_changed(self, value, name):
        self._settings.setValue(f"{name}_Vision_Parameter/max_tokens", value)

    def maxoutput_tokens_changed(self, value, name):
        self._settings.setValue(f"{name}_Vision_Parameter/max_output_tokens", value)

    def stream_changed(self, checked, name):
        if checked:
            self._settings.setValue(f"{name}_Vision_Parameter/stream", 'True')
        else:
            self._settings.setValue(f"{name}_Vision_Parameter/stream", 'False')

    def on_system_change(self, name):
        current_text = self.findChild(QComboBox, f"{name}_systemList").currentText()
        system_values = Utility.get_system_value(section=f"{name}_System", prefix="system",
                                                 default="You are a helpful assistant.", length=5)
        current_system = self.findChild(QTextEdit, f"{name}_current_system")
        if current_text in system_values:
            current_system.set_text(system_values[current_text])
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

    def start_chat(self):
        self.prompt_text.clear()
        self.prompt_text.setEnabled(False)

    def finish_chat(self):
        self.prompt_text.setEnabled(True)
        self.prompt_text.setFocus()

        imageListWidget = self.findChild(QListWidget, f"{self._current_llm}_ImageList")
        imageListWidget.clear()

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
                if widget is not None:
                    widget.deleteLater()

    @property
    def vision_history(self):
        return self._vision_history

    @property
    def vision_model(self):
        return self.findChild(QComboBox, f'{self._current_llm}_ModelList').currentText()
