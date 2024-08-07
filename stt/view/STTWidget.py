import html
import re

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout

from tts.view.AudioPlayerWidget import AudioPlayerWidget
from util.ChatType import ChatType
from util.Utility import Utility


class STTWidget(QWidget):
    def __init__(self, chat_type: ChatType, text: str, filepath: str):
        super().__init__()
        self.chat_type = chat_type
        self.text_result = text

        self.user_text = QLabel(self.text_result)
        self.format_text_label()

        self.filepath = filepath

        self.audio_player = AudioPlayerWidget()
        self.audio_player.set_audio_file(filepath)

        self.initialize_ui()

    def format_text_label(self):
        if self.chat_type == ChatType.AI:
            self.user_text.setTextFormat(Qt.TextFormat.MarkdownText)
        self.user_text.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.user_text.setWordWrap(True)
        self.user_text.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.user_text.setOpenExternalLinks(True)

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
        self.user_text.setStyleSheet(user_text_style)

    def initialize_ui(self):
        layout = QVBoxLayout(self)
        top_widget = self.create_top_widget()
        layout.addWidget(top_widget)
        layout.addWidget(self.user_text)
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

        # Create layouts for label and buttons
        model_label_layout = QHBoxLayout()
        model_label_layout.addWidget(self.model_label)
        model_label_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        # Button layout
        button_layout = QHBoxLayout()
        button_layout.setAlignment(Qt.AlignmentFlag.AlignRight)

        # Add both layouts to the top layout
        top_layout.addLayout(model_label_layout)
        top_layout.addLayout(button_layout)

        return top_widget

    def format_code_snippet(self, text):
        color = Utility.get_settings_value(section="AI_Code_Style", prop="color",
                                           default="#ccc",
                                           save=True)
        background_color = Utility.get_settings_value(section="AI_Code_Style", prop="background-color",
                                                      default="#333333",
                                                      save=True)
        font_size = Utility.get_settings_value(section="AI_Code_Style", prop="font-size",
                                               default="14px",
                                               save=True)
        font_family = Utility.get_settings_value(section="AI_Code_Style", prop="font-family",
                                                 default="monospace",
                                                 save=True)

        code_pattern = re.compile(r'```(\w+)\n(.*?)\n```', re.DOTALL)
        if text:
            matches = code_pattern.findall(text)
            for language, code in matches:
                escaped_code = html.escape('\n' + code)
                formatted_code = (
                    f'<pre style="font-size: {font_size}; font-family: {font_family}; background-color: {background_color}; color: {color};"><code>{escaped_code}</code></pre>')
                text = text.replace(f'```{language}\n{code}\n```', formatted_code)
        return text
    def apply_style(self):
        formatted_text = self.format_code_snippet(self.text_result)
        self.user_text.setText(formatted_text)

    def get_chat_type(self):
        return self.chat_type

    def set_model_name(self, name):
        self.model_label.setText(name)