from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QFont
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QPushButton, QApplication, QHBoxLayout, QFileDialog

from custom.ImageDisplay import ImageDisplay
from util.ChatType import ChatType
from util.Constants import Constants, UI
from util.Utility import Utility


class ImageWidget(QWidget):
    def __init__(self, chat_type: ChatType, image_data: str = None, revised_prompt: str = None):
        super().__init__()
        self.chat_type = chat_type
        self.scale_ratio = Constants.SCALE_RATIO

        self.revised_prompt = QLabel(revised_prompt)
        self.format_text_label()

        self.image = ImageDisplay(image_data)

        # UI setup
        self.initialize_ui()

    def initialize_ui(self):
        layout = QVBoxLayout(self)
        top_widget = self.create_top_widget()
        layout.addWidget(top_widget)
        layout.addWidget(self.revised_prompt)
        layout.addWidget(self.image)

    def format_text_label(self):
        self.revised_prompt.setTextFormat(Qt.TextFormat.MarkdownText)
        self.revised_prompt.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.revised_prompt.setWordWrap(True)
        self.revised_prompt.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.revised_prompt.setOpenExternalLinks(True)

        padding = Utility.get_settings_value(section="Common_Label_Style", prop="padding",
                                             default="5px",
                                             save=True)
        color = Utility.get_settings_value(section="Common_Label_Style", prop="color",
                                           default="#000000",
                                           save=True)
        font_size = Utility.get_settings_value(section="Common_Label_Style", prop="font-size",
                                               default="14px",
                                               save=True)
        font_family = Utility.get_settings_value(section="Common_Label_Style", prop="font-family",
                                                 default="sans-serif",
                                                 save=True)
        user_text_style = f"""
            QLabel {{
                padding: {padding};
                color: {color};
                font-size: {font_size};
                font-family: {font_family};
            }}
            """
        self.revised_prompt.setStyleSheet(user_text_style)

    def create_top_widget(self):

        boldFont = QFont()
        boldFont.setBold(True)

        top_widget = QWidget()
        top_layout = QHBoxLayout(top_widget)

        human_titlebar_background_color = Utility.get_settings_value(section="Chat_TitleBar_Style", prop="human_color",
                                                                     default="#dfccff",
                                                                     save=True)
        ai_titlebar_background_color = Utility.get_settings_value(section="Chat_TitleBar_Style", prop="ai_color",
                                                                  default="#d8fabe",
                                                                  save=True)

        if self.chat_type != ChatType.HUMAN:
            top_widget.setStyleSheet(f"background-color: {ai_titlebar_background_color}")
        else:
            top_widget.setStyleSheet(f"background-color: {human_titlebar_background_color}")

        padding = Utility.get_settings_value(section="Common_Label_Style", prop="padding",
                                             default="5px",
                                             save=True)

        model_color = Utility.get_settings_value(section="Info_Label_Style", prop="model-color",
                                                 default="green",
                                                 save=True)

        self.model_label = QLabel("")
        self.model_label.setFont(boldFont)

        model_label_style = f"""
                    QLabel {{
                        padding: {padding};
                        color: {model_color};
                    }}
                    """

        self.model_label.setStyleSheet(model_label_style)
        self.model_label.setAlignment(Qt.AlignmentFlag.AlignLeft)

        copy_button = QPushButton(QIcon(Utility.get_icon_path('ico', 'disks.png')), "Copy")
        copy_button.clicked.connect(lambda: QApplication.clipboard().setPixmap(self.image.pixmap))

        save_button = QPushButton(QIcon(Utility.get_icon_path('ico', 'disk--plus.png')), "Save")
        save_button.clicked.connect(self.save_image)

        zoomin_button = QPushButton(QIcon(Utility.get_icon_path('ico', 'magnifier-zoom-in.png')), "+Zoom")
        zoomin_button.clicked.connect(self.zoom_in)

        zoomout_button = QPushButton(QIcon(Utility.get_icon_path('ico', 'magnifier-zoom-out.png')), "-Zoom")
        zoomout_button.clicked.connect(self.zoom_out)

        # Create layouts for label and buttons
        model_label_layout = QHBoxLayout()
        model_label_layout.addWidget(self.model_label)
        model_label_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        # Button layout
        button_layout = QHBoxLayout()
        button_layout.addWidget(copy_button)
        button_layout.addWidget(save_button)
        button_layout.addWidget(zoomout_button)
        button_layout.addWidget(zoomin_button)
        button_layout.setAlignment(Qt.AlignmentFlag.AlignRight)

        # Add both layouts to the top layout
        top_layout.addLayout(model_label_layout)
        top_layout.addLayout(button_layout)

        return top_widget

    def get_chat_type(self):
        return self.chat_type

    def set_model_name(self, name):
        self.model_label.setText(name)

    def save_image(self):
        file_name, _ = QFileDialog.getSaveFileName(self, UI.SAVE_IMAGE_TITLE, "", UI.SAVE_IMAGE_FILTER)
        if file_name:
            self.image.pixmap.save(file_name, UI.IMAGE_PNG)

    def zoom(self, ratio):
        self.image.scale(ratio, ratio)

    def zoom_in(self):
        self.zoom(self.scale_ratio)

    def zoom_out(self):
        self.zoom(1 / self.scale_ratio)
