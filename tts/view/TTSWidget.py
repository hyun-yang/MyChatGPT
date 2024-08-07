from shutil import copy2

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QFont
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QPushButton, QHBoxLayout, QFileDialog

from tts.view.AudioPlayerWidget import AudioPlayerWidget
from util.ChatType import ChatType
from util.Constants import UI
from util.Utility import Utility


class TTSWidget(QWidget):
    def __init__(self, chat_type: ChatType, filepath: str):
        super().__init__()
        self.chat_type = chat_type
        self.filepath = filepath

        self.audio_player = AudioPlayerWidget()
        self.audio_player.set_audio_file(filepath)

        self.initialize_ui()

    def initialize_ui(self):
        layout = QVBoxLayout(self)
        top_widget = self.create_top_widget()
        layout.addWidget(top_widget)
        layout.addWidget(self.audio_player, alignment=Qt.AlignmentFlag.AlignCenter)

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

        # Create Buttons
        copy_button = QPushButton(QIcon(Utility.get_icon_path('ico', 'disks.png')), UI.COPY)
        copy_button.clicked.connect(self.copy_audio)

        save_button = QPushButton(QIcon(Utility.get_icon_path('ico', 'disk--plus.png')), UI.SAVE)
        save_button.clicked.connect(self.save_audio)

        # Create layouts for label and buttons
        model_label_layout = QHBoxLayout()
        model_label_layout.addWidget(self.model_label)
        model_label_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        # Button layout
        button_layout = QHBoxLayout()
        button_layout.addWidget(copy_button)
        button_layout.addWidget(save_button)
        button_layout.setAlignment(Qt.AlignmentFlag.AlignRight)

        # Add both layouts to the top layout
        top_layout.addLayout(model_label_layout)
        top_layout.addLayout(button_layout)

        return top_widget

    def get_chat_type(self):
        return self.chat_type

    def set_model_name(self, name):
        self.model_label.setText(name)

    def copy_audio(self):
        dest_dir = QFileDialog.getExistingDirectory(self, UI.AUDIO_SELECT_FOLDER)
        if dest_dir:
            copy2(self.filepath, dest_dir)

    def save_audio(self):
        dest_file, _ = QFileDialog.getSaveFileName(self, UI.AUDIO_SAVE)
        if dest_file:
            copy2(self.filepath, dest_file)
