import io
import os
from functools import partial

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QSizePolicy, QScrollArea, QSplitter, \
    QTabWidget, QGroupBox, QFormLayout, QLabel, QComboBox, QListWidget, QMessageBox, QFileDialog

from chat.view.ChatWidget import ChatWidget
from custom.CheckComboBox import CheckComboBox
from custom.CheckSpinBox import CheckSpinBox
from custom.PromptTextEdit import PromptTextEdit
from image.view.ImageHistory import ImageHistory
from image.view.ImageWidget import ImageWidget
from util.ChatType import ChatType
from util.Constants import AIProviderName, Constants, UI, MODEL_MESSAGE
from util.SettingsManager import SettingsManager
from util.Utility import Utility
from vision.view.ImageListWidget import ImageListWidget


class ImageView(QWidget):
    submitted_signal = pyqtSignal(str, list)
    stop_signal = pyqtSignal()
    current_llm_signal = pyqtSignal(str)

    def __init__(self, model):
        super().__init__()
        self.model = model
        self._settings = SettingsManager.get_settings()
        self._current_llm = AIProviderName.OPENAI.value
        self._current_type = Constants.DALLE_CREATE

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
        self.prompt_text.submitted_signal.connect(partial(self.submit_file, self._current_llm))
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
        image_icon = QIcon(Utility.get_icon_path('ico', 'image-export.png'))
        self.config_tabs.addTab(self.create_parameters_tab(), image_icon, UI.IMAGE)
        self.config_tabs.addTab(self.create_imagedb_tab(), image_icon, UI.IMAGE_LIST)

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
                if isinstance(current_widget, ImageListWidget):
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

    def force_stop(self):
        self.stop_signal.emit()
        self.stop_widget.setVisible(False)

    def submit_file(self, llm, text):
        if text is None:
            text = self.prompt_text.toPlainText()
        creation_type = self.creationTypeList.currentText()
        if creation_type == Constants.DALLE_CREATE:
            self.submitted_signal.emit(text, [])
        elif creation_type == Constants.DALLE_VARIATION:
            fileListWidget = self.findChild(QListWidget, f"{creation_type}_List")
            if fileListWidget.count():
                items = [fileListWidget.item(i) for i in range(fileListWidget.count())]
                file_item = items[0]
                if file_item:
                    file_name = file_item.text()
                    self.submitted_signal.emit(text, [file_name])
                else:
                    return None
            else:
                QMessageBox.warning(self, UI.WARNING_TITLE, UI.WARNING_TITLE_SELECT_FILE_MESSAGE)
        elif creation_type == Constants.DALLE_EDIT:
            fileListWidget = self.findChild(QListWidget, f"{creation_type}_List")
            if fileListWidget.count() and text:
                item_texts = [fileListWidget.item(i).text() for i in range(fileListWidget.count())]
                if item_texts:
                    self.submitted_signal.emit(text, item_texts)
                else:
                    return None
            else:
                QMessageBox.warning(self, UI.WARNING_TITLE, UI.WARNING_TITLE_SELECT_FILE_AND_PROMPT_MESSAGE)

    def create_parameters_tab(self):
        layoutWidget = QWidget()
        layout = QVBoxLayout()

        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_openai_tabcontent(AIProviderName.OPENAI.value), AIProviderName.OPENAI.value)

        self.tabs.currentChanged.connect(self.on_tab_change)
        layout.addWidget(self.tabs)

        layoutWidget.setLayout(layout)
        return layoutWidget

    def on_tab_change(self, index):
        self._current_llm = self.tabs.tabText(index)
        self._settings.setValue('AI_Provider/llm', self._current_llm)
        self.current_llm_signal.emit(self._current_llm)

    def set_default_tab(self, name):
        index = self.tabs.indexOf(self.tabs.findChild(QWidget, name))
        if index != -1:
            self.tabs.setCurrentIndex(index)

    def create_openai_tabcontent(self, name):
        tabWidget = QWidget()
        tabWidget.setObjectName(name)
        layoutMain = QVBoxLayout()

        groupCreationType = QGroupBox("OpenAI Creation Type")
        creationTypeLayout = QFormLayout()

        creationTypeLabel = QLabel("Creation Type")
        self.creationTypeList = QComboBox()
        self.creationTypeList.setObjectName("Creation Type List")
        self.creationTypeList.addItems(Constants.DALLE_CREATION_TYPE)
        self.creationTypeList.currentTextChanged.connect(lambda text: self.set_current_type(text))

        creationTypeLayout.addRow(creationTypeLabel)
        creationTypeLayout.addRow(self.creationTypeList)
        groupCreationType.setLayout(creationTypeLayout)
        layoutMain.addWidget(groupCreationType)

        image_widget = self.create_image_widget(Constants.DALLE_CREATE)
        image_widget_container = QWidget()
        image_widget_container.setLayout(image_widget)

        edit_widget = self.create_edit_widget(Constants.DALLE_EDIT)
        edit_widget_container = QWidget()
        edit_widget_container.setLayout(edit_widget)
        edit_widget_container.hide()

        variation_widget = self.create_variation_widget(Constants.DALLE_VARIATION)
        variation_widget_container = QWidget()
        variation_widget_container.setLayout(variation_widget)
        variation_widget_container.hide()

        layoutMain.addWidget(image_widget_container)
        layoutMain.addWidget(edit_widget_container)
        layoutMain.addWidget(variation_widget_container)

        tabWidget.setLayout(layoutMain)

        def on_creation_type_changed(index):
            image_widget_container.hide()
            edit_widget_container.hide()
            variation_widget_container.hide()

            if Constants.DALLE_CREATION_TYPE[index] == Constants.DALLE_CREATE:
                image_widget_container.show()
            elif Constants.DALLE_CREATION_TYPE[index] == Constants.DALLE_EDIT:
                edit_widget_container.show()
            elif Constants.DALLE_CREATION_TYPE[index] == Constants.DALLE_VARIATION:
                variation_widget_container.show()

        self.creationTypeList.currentIndexChanged.connect(on_creation_type_changed)
        on_creation_type_changed(self.creationTypeList.currentIndex())

        return tabWidget

    def set_current_type(self, text):
        self._current_type = text
        if self._current_type == Constants.DALLE_CREATE:
            self.prompt_text.setPlaceholderText(UI.CHAT_PROMPT_PLACEHOLDER)
        elif self._current_type == Constants.DALLE_VARIATION:
            self.prompt_text.setPlaceholderText(UI.SELECT_FILE_AND_PROMPT_PLACEHOLDER)
        elif self._current_type == Constants.DALLE_EDIT:
            self.prompt_text.setPlaceholderText(UI.IMAGE_EDIT_PROMPT_PLACEHOLDER)

    def create_image_widget(self, name):
        layout = QVBoxLayout()

        groupModel = QGroupBox(f"{name} Model")
        modelLayout = QFormLayout()
        modelLabel = QLabel(f"{name} Model List")
        modelList = QComboBox()
        modelList.setObjectName(f"{name}_ModelList")
        modelList.clear()

        self.set_model_list(modelList, AIProviderName.OPENAI.value, name)

        modelLayout.addRow(modelLabel)
        modelLayout.addRow(modelList)
        groupModel.setLayout(modelLayout)
        layout.addWidget(groupModel)

        current_model = Utility.get_settings_value(section=f"{name}_Image_Parameter", prop="image_model",
                                                   default=Constants.DALLE3, save=True)

        # Parameters Group
        groupParam = QGroupBox(f"{name} Parameters")
        paramLayout = QFormLayout()

        number_of_imagesSpinBox = CheckSpinBox()
        number_of_imagesSpinBox.setObjectName(f"{name}_number_of_imagesSpinBox")
        number_of_imagesSpinBox.spin_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        number_of_imagesSpinBox.spin_box.setRange(1, 10)
        number_of_imagesSpinBox.spin_box.setAccelerated(True)
        number_of_imagesSpinBox.spin_box.setSingleStep(1)
        number_of_imagesSpinBox.spin_box.setValue(
            int(
                Utility.get_settings_value(section=f"{name}_Image_Parameter", prop="number_of_images",
                                           default="1", save=True)))
        number_of_imagesSpinBox.valueChanged.connect(lambda value: self.number_of_images_changed(value, name))
        number_of_imagesSpinBox.check_box.setEnabled(False)
        paramLayout.addRow('No. of images', number_of_imagesSpinBox)

        # size : dall-e-2: 256x256, 512x512, or 1024x1024  dall-e-3: 1024x1024, 1792x1024, or 1024x1792
        sizeComboBox = CheckComboBox()
        sizeComboBox.setObjectName(f"{name}_sizeComboBox")
        sizeComboBox.combo_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        sizeComboBox.combo_box.setCurrentText(
            Utility.get_settings_value(section=f"{name}_Image_Parameter", prop="size",
                                       default="1024x1024", save=True)
        )
        sizeComboBox.currentTextChanged.connect(lambda value: self.size_changed(value, name))
        paramLayout.addRow('Size', sizeComboBox)

        # style : only dall-e-3 have vivid or natural option
        styleComboBox = CheckComboBox()
        styleComboBox.setObjectName(f"{name}_styleComboBox")
        styleComboBox.combo_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        styleComboBox.combo_box.addItems(Constants.DALLE_STYLE_LIST)
        styleComboBox.combo_box.setCurrentText(
            Utility.get_settings_value(section=f"{name}_Image_Parameter", prop="style",
                                       default="vivid", save=True)
        )
        styleComboBox.currentTextChanged.connect(lambda value: self.style_changed(value, name))
        paramLayout.addRow('Style', styleComboBox)

        # quality : only for dall-e-3:  standard or hd
        qualityComboBox = CheckComboBox()
        qualityComboBox.setObjectName(f"{name}_qualityComboBox")
        qualityComboBox.combo_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        qualityComboBox.combo_box.addItems(Constants.DALLE_QUALITY_LIST)
        qualityComboBox.combo_box.setCurrentText(
            Utility.get_settings_value(section=f"{name}_Image_Parameter", prop="quality",
                                       default="standard", save=True)
        )
        qualityComboBox.currentTextChanged.connect(lambda value: self.quality_changed(value, name))
        paramLayout.addRow('Quality', qualityComboBox)

        self.update_open_ai_parameter(name, current_model, qualityComboBox, sizeComboBox, styleComboBox)

        groupParam.setLayout(paramLayout)
        layout.addWidget(groupParam)

        return layout

    def create_edit_widget(self, name):
        layout = QVBoxLayout()

        groupModel = QGroupBox(f"{name} Model")
        modelLayout = QFormLayout()
        modelLabel = QLabel(f"{name} Model List")
        modelList = QComboBox()
        modelList.setObjectName(f"{name}_ModelList")
        modelList.clear()

        modelList.addItems([Constants.DALLE2])

        modelLayout.addRow(modelLabel)
        modelLayout.addRow(modelList)
        groupModel.setLayout(modelLayout)
        layout.addWidget(groupModel)

        # Parameters Group
        groupParam = QGroupBox(f"{name} Parameters")
        paramLayout = QFormLayout()

        number_of_imagesSpinBox = CheckSpinBox()
        number_of_imagesSpinBox.setObjectName(f"{name}_edit_number_of_imagesSpinBox")
        number_of_imagesSpinBox.spin_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        number_of_imagesSpinBox.spin_box.setRange(1, 10)
        number_of_imagesSpinBox.spin_box.setAccelerated(True)
        number_of_imagesSpinBox.spin_box.setSingleStep(1)
        number_of_imagesSpinBox.spin_box.setValue(
            int(
                Utility.get_settings_value(section=f"{name}_Image_Parameter", prop="number_of_images",
                                           default="1", save=True)))
        number_of_imagesSpinBox.valueChanged.connect(lambda value: self.number_of_images_changed(value, name))
        number_of_imagesSpinBox.check_box.setEnabled(False)
        paramLayout.addRow('No. of images', number_of_imagesSpinBox)

        # size : dall-e-2: 256x256, 512x512, or 1024x1024  dall-e-3: 1024x1024, 1792x1024, or 1024x1792
        sizeComboBox = CheckComboBox()
        sizeComboBox.setObjectName(f"{name}_edit_sizeComboBox")
        sizeComboBox.combo_box.addItems(Constants.DALLE2_SIZE_LIST)
        sizeComboBox.combo_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        sizeComboBox.combo_box.setCurrentText(
            Utility.get_settings_value(section=f"{name}_Image_Parameter", prop="size",
                                       default="1024x1024", save=True)
        )
        sizeComboBox.currentTextChanged.connect(lambda value: self.size_changed(value, name))
        paramLayout.addRow('Size', sizeComboBox)

        groupParam.setLayout(paramLayout)
        layout.addWidget(groupParam)

        # Add QListWidget to show selected image list
        fileListGroup = QGroupBox(f"{name} List")
        fileListLayout = QVBoxLayout()
        fileListGroup.setLayout(fileListLayout)

        # Add QListWidget to show selected image list
        fileListWidget = QListWidget()
        fileListWidget.setObjectName(f"{name}_List")
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

        selectButton.clicked.connect(partial(self.select_image_files, name))
        deleteButton.clicked.connect(partial(self.delete_image_list, name))
        submitButton.clicked.connect(partial(self.submit_file, self._current_llm, None))

        fileListWidget.itemSelectionChanged.connect(partial(self.on_item_selection_changed, name))

        layout.addWidget(fileListGroup)

        return layout

    def create_variation_widget(self, name):
        layout = QVBoxLayout()

        groupModel = QGroupBox(f"{name} Model")
        modelLayout = QFormLayout()
        modelLabel = QLabel(f"{name} Model List")
        modelList = QComboBox()
        modelList.setObjectName(f"{name}_ModelList")
        modelList.clear()

        modelList.addItems([Constants.DALLE2])

        modelLayout.addRow(modelLabel)
        modelLayout.addRow(modelList)
        groupModel.setLayout(modelLayout)
        layout.addWidget(groupModel)

        # Parameters Group
        groupParam = QGroupBox(f"{name} Parameters")
        paramLayout = QFormLayout()

        number_of_imagesSpinBox = CheckSpinBox()
        number_of_imagesSpinBox.setObjectName(f"{name}_variation_number_of_imagesSpinBox")
        number_of_imagesSpinBox.spin_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        number_of_imagesSpinBox.spin_box.setRange(1, 10)
        number_of_imagesSpinBox.spin_box.setAccelerated(True)
        number_of_imagesSpinBox.spin_box.setSingleStep(1)
        number_of_imagesSpinBox.spin_box.setValue(
            int(
                Utility.get_settings_value(section=f"{name}_Image_Parameter", prop="number_of_images",
                                           default="1", save=True)))
        number_of_imagesSpinBox.valueChanged.connect(lambda value: self.number_of_images_changed(value, name))
        number_of_imagesSpinBox.check_box.setEnabled(False)
        paramLayout.addRow('No. of images', number_of_imagesSpinBox)

        # size : dall-e-2: 256x256, 512x512, or 1024x1024  dall-e-3: 1024x1024, 1792x1024, or 1024x1792
        sizeComboBox = CheckComboBox()
        sizeComboBox.setObjectName(f"{name}_variation_sizeComboBox")
        sizeComboBox.combo_box.addItems(Constants.DALLE2_SIZE_LIST)
        sizeComboBox.combo_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        sizeComboBox.combo_box.setCurrentText(
            Utility.get_settings_value(section=f"{name}_Image_Parameter", prop="size",
                                       default="1024x1024", save=True)
        )
        sizeComboBox.currentTextChanged.connect(lambda value: self.size_changed(value, name))
        paramLayout.addRow('Size', sizeComboBox)

        groupParam.setLayout(paramLayout)
        layout.addWidget(groupParam)

        # Add QListWidget to show selected image list
        fileListGroup = QGroupBox(f"{name} List")
        fileListLayout = QVBoxLayout()
        fileListGroup.setLayout(fileListLayout)

        # Add QListWidget to show selected image list
        fileListWidget = QListWidget()
        fileListWidget.setObjectName(f"{name}_List")
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

        selectButton.clicked.connect(partial(self.select_image_files, name))
        deleteButton.clicked.connect(partial(self.delete_image_list, name))
        submitButton.clicked.connect(partial(self.submit_file, self._current_llm, None))

        fileListWidget.itemSelectionChanged.connect(partial(self.on_item_selection_changed, name))

        layout.addWidget(fileListGroup)

        return layout

    def create_openai_edit_tabcontent(self, name):
        tabWidget = QWidget()
        tabWidget.setObjectName(name)
        layoutMain = QVBoxLayout()

        groupModel = QGroupBox(f"{name} Model")
        modelLayout = QFormLayout()
        modelLabel = QLabel(f"{name} Model List")
        modelList = QComboBox()
        modelList.setObjectName(f"{name}_ModelList")
        modelList.clear()

        modelList.addItems([Constants.DALLE2])

        modelLayout.addRow(modelLabel)
        modelLayout.addRow(modelList)
        groupModel.setLayout(modelLayout)
        layoutMain.addWidget(groupModel)

        # Parameters Group
        groupParam = QGroupBox(f"{name} Parameters")
        paramLayout = QFormLayout()

        number_of_imagesSpinBox = CheckSpinBox()
        number_of_imagesSpinBox.setObjectName(f"{name}_number_of_imagesSpinBox")
        number_of_imagesSpinBox.spin_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        number_of_imagesSpinBox.spin_box.setRange(1, 10)
        number_of_imagesSpinBox.spin_box.setAccelerated(True)
        number_of_imagesSpinBox.spin_box.setSingleStep(1)
        number_of_imagesSpinBox.spin_box.setValue(
            int(
                Utility.get_settings_value(section=f"{name}_Image_Parameter", prop="number_of_images",
                                           default="1", save=True)))
        number_of_imagesSpinBox.valueChanged.connect(lambda value: self.number_of_images_changed(value, name))
        number_of_imagesSpinBox.check_box.setEnabled(False)
        paramLayout.addRow('No. of images', number_of_imagesSpinBox)

        # size : dall-e-2: 256x256, 512x512, or 1024x1024  dall-e-3: 1024x1024, 1792x1024, or 1024x1792
        sizeComboBox = CheckComboBox()
        sizeComboBox.setObjectName(f"{name}_sizeComboBox")
        sizeComboBox.combo_box.addItems(Constants.DALLE2_SIZE_LIST)
        sizeComboBox.combo_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        sizeComboBox.combo_box.setCurrentText(
            Utility.get_settings_value(section=f"{name}_Image_Parameter", prop="size",
                                       default="1024x1024", save=True)
        )
        sizeComboBox.currentTextChanged.connect(lambda value: self.size_changed(value, name))
        paramLayout.addRow('Size', sizeComboBox)

        groupParam.setLayout(paramLayout)
        layoutMain.addWidget(groupParam)

        tabWidget.setLayout(layoutMain)

        return tabWidget

    def update_open_ai_parameter(self, llm, current_model, qualityComboBox, sizeComboBox, styleComboBox):
        existing_size = self._settings.value(f"{llm}_Image_Parameter/size")
        sizeComboBox.combo_box.clear()
        if current_model == Constants.DALLE2:
            sizeComboBox.combo_box.addItems(Constants.DALLE2_SIZE_LIST)
            styleComboBox.setEnabled(False)
            qualityComboBox.setEnabled(False)
        elif current_model == Constants.DALLE3:
            sizeComboBox.combo_box.addItems(Constants.DALLE3_SIZE_LIST)
            styleComboBox.setEnabled(True)
            qualityComboBox.setEnabled(True)
        sizeComboBox.combo_box.setCurrentText(existing_size)

    def set_model_list(self, modelList, llm, name):
        api_key = self._settings.value(f'AI_Provider/{llm}')
        modelList.addItems(Utility.get_openai_dalle_model_list(api_key))
        current_model = Utility.get_settings_value(section=f"{name}_Image_Parameter", prop="image_model",
                                                   default=Constants.DALLE3, save=True)
        modelList.setCurrentText(current_model)
        modelList.currentTextChanged.connect(lambda current_text: self.model_list_changed(current_text, name))

    def model_list_changed(self, model, name):
        self._settings.setValue(f"{name}_Image_Parameter/image_model", model)

        # OPENAI Only
        if name == Constants.DALLE_CREATE:
            self.update_openai_model(name, model)

    def update_openai_model(self, name, model):
        comboBox = self.findChild(CheckComboBox, f'{name}_sizeComboBox')
        comboBox.combo_box.clear()
        styleComboBox = self.findChild(CheckComboBox,
                                       f'{name}_styleComboBox')
        qualityComboBox = self.findChild(CheckComboBox,
                                         f'{name}_qualityComboBox')
        self.update_open_ai_parameter(name, model, qualityComboBox, comboBox, styleComboBox)

    def select_image_files(self, name):
        fileListWidget = self.findChild(QListWidget, f"{name}_List")
        selected_files = self.show_image_files_dialog(name)
        if name == Constants.DALLE_VARIATION:
            if selected_files:
                fileListWidget.addItem(selected_files)
        else:
            if selected_files:
                for file in selected_files:
                    fileListWidget.addItem(file)
        self.update_submit_status(name)

    def delete_image_list(self, name):
        fileListWidget = self.findChild(QListWidget, f"{name}_List")
        for item in fileListWidget.selectedItems():
            fileListWidget.takeItem(fileListWidget.row(item))
        self.update_submit_status(name)

    def show_image_files_dialog(self, name):
        file_filter = UI.IMAGE_FILTER

        file_dialog = QFileDialog()

        if name == Constants.DALLE_VARIATION:
            file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        else:
            file_dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)

        file_dialog.setNameFilter(file_filter)

        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            valid_files = []
            for file in selected_files:
                # Check if file is a png and its size is less than 4MB
                if file.endswith(UI.IMAGE_PNG_EXTENSION) and os.path.getsize(file) < 4 * 1024 * 1024:
                    valid_files.append(file)
                    if len(valid_files) >= 2:
                        break
                else:
                    QMessageBox.warning(self, UI.WARNING_TITLE,
                                        UI.IMAGE_SIZE_ERROR_MESSAGE)
                    return
            if name == Constants.DALLE_VARIATION:
                return valid_files[0]
            else:
                return valid_files
        else:
            return [] if name != Constants.DALLE_VARIATION else None

    def update_submit_status(self, name):
        fileListWidget = self.findChild(QListWidget,
                                        f"{name}_List")
        submitButton = self.findChild(QPushButton,
                                      f"{name}_SubmitButton")
        if name == Constants.DALLE_VARIATION:
            submitButton.setEnabled(bool(fileListWidget.count()))
        elif name == Constants.DALLE_EDIT:
            submitButton.setEnabled(fileListWidget.count() == Constants.DALLE_EDIT_FILES_COUNT)

    def on_item_selection_changed(self, name):
        fileListWidget = self.findChild(QListWidget,
                                        f"{name}_List")
        deleteButton = self.findChild(QPushButton,
                                      f"{name}_DeleteButton")
        deleteButton.setEnabled(bool(fileListWidget.selectedItems()))

        submitButton = self.findChild(QPushButton,
                                      f"{name}_SubmitButton")

        if name == Constants.DALLE_VARIATION:
            submitButton.setEnabled(bool(fileListWidget.count()))
        elif name == Constants.DALLE_EDIT:
            submitButton.setEnabled(fileListWidget.count() == Constants.DALLE_EDIT_FILES_COUNT)

    def get_selected_files(self, name):
        fileListWidget = self.findChild(QListWidget, f"{name}_List")
        return [fileListWidget.item(i).text() for i in range(fileListWidget.count())]

    def create_args(self, llm, text, filepath):
        method_name = f'create_args_{llm.lower()}'
        method = getattr(self, method_name, None)
        if callable(method):
            return method(llm, text, filepath)
        else:
            raise ValueError(f'{UI.METHOD} {method_name} {UI.NOT_FOUND}')

    def create_args_openai(self, llm, text, file_list):
        api_key = self._settings.value(f'AI_Provider/{llm}')

        creation_type = self.creationTypeList.currentText()

        if creation_type == Constants.DALLE_CREATE:
            model = self.findChild(QComboBox, f'{creation_type}_ModelList').currentText()

            number_of_imagesSpinBox = self.findChild(CheckSpinBox,
                                                     f'{creation_type}_number_of_imagesSpinBox').spin_box
            number_of_images = number_of_imagesSpinBox.value() if number_of_imagesSpinBox.isEnabled() else None

            sizeComboBox = self.findChild(CheckComboBox,
                                          f'{creation_type}_sizeComboBox').combo_box
            size = sizeComboBox.currentText() if sizeComboBox.isEnabled() else None

            styleComboBox = self.findChild(CheckComboBox,
                                           f'{creation_type}_styleComboBox').combo_box
            style = styleComboBox.currentText() if styleComboBox.isEnabled() else None

            qualityComboBox = self.findChild(CheckComboBox,
                                             f'{creation_type}_qualityComboBox').combo_box
            quality = qualityComboBox.currentText() if qualityComboBox.isEnabled() else None

            ai_arg = {
                'prompt': text,
                'model': model,
                'n': number_of_images,
                'size': size,
                'response_format': Constants.RESPONSE_FORMAT_B64_JSON,
            }

            if style:
                ai_arg['style'] = style

            if quality:
                ai_arg['quality'] = quality

            args = {
                'api_key': api_key,
                'ai_arg': ai_arg,
                'stream': False,
                'creation_type': creation_type,
            }
            return args

        elif creation_type == Constants.DALLE_EDIT:
            model = Constants.DALLE2
            number_of_imagesSpinBox = self.findChild(CheckSpinBox,
                                                     f'{creation_type}_edit_number_of_imagesSpinBox').spin_box
            number_of_images = number_of_imagesSpinBox.value() if number_of_imagesSpinBox.isEnabled() else None

            sizeComboBox = self.findChild(CheckComboBox,
                                          f'{creation_type}_edit_sizeComboBox').combo_box
            size = sizeComboBox.currentText() if sizeComboBox.isEnabled() else None

            image_files = self.create_bytes_io_list(file_list)
            if not image_files:
                return

            ai_arg = {
                'prompt': text,
                'image': image_files[0],
                'mask': image_files[1],
                'model': model,
                'n': number_of_images,
                'size': size,
                'response_format': Constants.RESPONSE_FORMAT_B64_JSON,
            }

            args = {
                'api_key': api_key,
                'ai_arg': ai_arg,
                'stream': False,
                'creation_type': creation_type,
            }

            return args

        elif creation_type == Constants.DALLE_VARIATION:
            model = Constants.DALLE2
            number_of_imagesSpinBox = self.findChild(CheckSpinBox,
                                                     f'{creation_type}_variation_number_of_imagesSpinBox').spin_box
            number_of_images = number_of_imagesSpinBox.value() if number_of_imagesSpinBox.isEnabled() else None

            sizeComboBox = self.findChild(CheckComboBox,
                                          f'{creation_type}_variation_sizeComboBox').combo_box
            size = sizeComboBox.currentText() if sizeComboBox.isEnabled() else None

            image_files = self.create_bytes_io_list(file_list)
            if not image_files:
                return
            image_file = image_files[0]

            ai_arg = {
                'image': image_file,
                'model': model,
                'n': number_of_images,
                'size': size,
                'response_format': Constants.RESPONSE_FORMAT_B64_JSON,
            }

            args = {
                'api_key': api_key,
                'ai_arg': ai_arg,
                'stream': False,
                'creation_type': creation_type,
            }

            return args
        else:
            raise ValueError(f"{MODEL_MESSAGE.INVALID_CREATION_TYPE} {creation_type}")

    def create_bytes_io_list(self, file_list):
        bytes_io_list = []
        for filepath in file_list:
            try:
                with open(filepath, UI.FILE_READ_IN_BINARY_MODE) as file:
                    content = file.read()
                    image_file = io.BytesIO(content)
                    image_file.name = filepath
                    bytes_io_list.append(image_file)
            except FileNotFoundError:
                print(f"{UI.FAILED_TO_OPEN_FILE} {filepath}")
        return bytes_io_list

    def create_imagedb_tab(self):
        layoutWidget = QWidget()
        layout = QVBoxLayout()

        self._image_history = ImageHistory(self.model)

        layout.addWidget(self._image_history)

        layoutWidget.setLayout(layout)
        return layoutWidget

    def add_user_question(self, chatType, text, file_list):
        if len(file_list) > 0:
            user_question = ImageListWidget(chatType, text, file_list)
        else:
            user_question = ChatWidget(chatType, text)
        self.result_layout.addWidget(user_question)

    def adjust_scroll_bar(self, min_val, max_val):
        self.ai_answer_scroll_area.verticalScrollBar().setSliderPosition(max_val)

    def update_ui_submit(self, chatType, text, file_list):
        if len(file_list) > 0:
            self.add_user_question(chatType, text, file_list)
        else:
            self.add_user_question(chatType, text, [])
        self.stop_widget.setVisible(True)

    def update_ui(self, image_data, revised_prompt):
        ai_answer = ImageWidget(ChatType.AI, image_data, revised_prompt)
        self.result_layout.addWidget(ai_answer)

    def update_ui_finish(self, model, finish_reason, elapsed_time, stream):
        chatWidget = self.get_last_ai_widget()
        self.stop_widget.setVisible(False)

        if chatWidget and chatWidget.get_chat_type() == ChatType.AI:
            chatWidget.set_model_name(
                Constants.MODEL_PREFIX + model + " | Response Time : " + format(elapsed_time, ".2f"))

    def get_last_ai_widget(self) -> ImageWidget | None:
        layout_item = self.result_widget.layout().itemAt(self.result_widget.layout().count() - 1)
        if layout_item:
            last_ai_widget = layout_item.widget()
            if last_ai_widget.get_chat_type() == ChatType.AI:
                return last_ai_widget
        else:
            return None

    def number_of_images_changed(self, value, name):
        self._settings.setValue(f"{name}_Image_Parameter/number_of_images", value)

    def size_changed(self, value, name):
        self._settings.setValue(f"{name}_Image_Parameter/size", value)

    def style_changed(self, value, name):
        self._settings.setValue(f"{name}_Image_Parameter/style", value)

    def quality_changed(self, value, name):
        self._settings.setValue(f"{name}_Image_Parameter/quality", value)

    def start_chat(self):
        self.prompt_text.clear()
        self.prompt_text.setEnabled(False)

    def finish_chat(self):
        self.prompt_text.setEnabled(True)
        self.prompt_text.setFocus()

        if self._current_type in [Constants.DALLE_EDIT, Constants.DALLE_VARIATION]:
            fileListWidget = self.findChild(QListWidget, f"{self._current_type}_List")
            fileListWidget.clear()

            submitButton = self.findChild(QPushButton, f"{self._current_type}_SubmitButton")
            submitButton.setEnabled(False)

    def clear_all(self):
        target_layout = self.result_layout
        if target_layout is not None:
            while target_layout.count():
                item = target_layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()

    @property
    def image_history(self):
        return self._image_history

    @property
    def creation_type(self):
        return self._current_type
