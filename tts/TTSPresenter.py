from PyQt6.QtCore import QByteArray
from PyQt6.QtCore import pyqtSlot
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QDialog, QMessageBox

from tts.model.TTSListModel import TTSListModel
from tts.model.TTSModel import TTSModel
from tts.view.TTSView import TTSView
from util.ChatType import ChatType
from util.ConfirmationDialog import ConfirmationDialog
from util.Constants import Constants, AIProviderName, UI
from util.DataManager import DataManager
from util.SettingsManager import SettingsManager


class TTSPresenter(QWidget):

    def __init__(self):
        super().__init__()
        self._tts_main_id = None
        self._tts_main_index = None
        self.initialize_manager()
        self.initialize_ui()

    def initialize_manager(self):
        self._settings = SettingsManager.get_settings()
        self._database = DataManager.get_database()
        self.llm = AIProviderName.OPENAI.value

    def initialize_ui(self):
        # View
        self.ttsViewModel = TTSListModel(self._database)
        self.ttsViewModel.new_tts_main_id_signal.connect(self.set_tts_main_id)
        self.ttsViewModel.remove_tts_signal.connect(self.clear_tts)
        self.ttsView = TTSView(self.ttsViewModel)

        # Model
        self.ttsModel = TTSModel()

        # View signal
        self.ttsView.submitted_signal.connect(self.submit)
        self.ttsView.stop_signal.connect(self.ttsModel.force_stop)
        self.ttsView.current_llm_signal.connect(self.set_current_llm_signal)

        self.ttsView.tts_history.new_tts_signal.connect(self.create_new_tts)
        self.ttsView.tts_history.delete_tts_signal.connect(self.confirm_delete_tts)
        self.ttsView.tts_history.tts_list.delete_id_signal.connect(self.delete_tts_table)
        self.ttsView.tts_history.filter_signal.connect(self.filter_list)
        self.ttsView.set_default_tab(self.llm)

        # Model signal
        self.ttsModel.thread_started_signal.connect(self.ttsView.start_chat)
        self.ttsModel.thread_finished_signal.connect(self.ttsView.finish_chat)
        self.ttsModel.response_signal.connect(self.handle_response_signal)
        self.ttsModel.response_finished_signal.connect(self.handle_response_finished_signal)

        # View
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.ttsView)

        self.initialize_tts_history()

        self.setLayout(main_layout)

    def initialize_tts_history(self):
        self.tts_list = self.ttsView.tts_history.tts_list
        self.tts_list.tts_id_signal.connect(self.show_tts_detail)

    def set_tts_main_id(self, tts_main_id):
        self.tts_main_id = tts_main_id
        self.view.clear_all()

    @pyqtSlot(bytes, str)
    def handle_response_signal(self, result, response_format):
        self.tts_data = QByteArray(result)
        self.response_format = response_format
        self.ttsView.update_ui(self.tts_data)

    @pyqtSlot(str, str, float, bool)
    def handle_response_finished_signal(self, model, finish_reason, elapsed_time, stream):
        self.ttsView.update_ui_finish(model, finish_reason, elapsed_time, stream)
        self._database.insert_tts_detail(self.tts_main_id, ChatType.AI.value, model, None,
                                         self.response_format, self.tts_data, elapsed_time, finish_reason)

    @property
    def model(self):
        return self.ttsModel

    @property
    def view(self):
        return self.ttsView

    @property
    def tts_main_id(self):
        return self._tts_main_id

    @tts_main_id.setter
    def tts_main_id(self, value):
        self._tts_main_id = value

    @pyqtSlot(str)
    def set_current_llm_signal(self, llm_name):
        self.llm = llm_name

    @pyqtSlot(int)
    def clear_tts(self, delete_id):
        if self.tts_main_id == delete_id:
            self.tts_main_id = None
            self.view.clear_all()

    @pyqtSlot()
    def confirm_delete_tts(self):
        if self.tts_main_id:
            title = UI.CONFIRM_DELETION_TITLE
            message = UI.CONFIRM_DELETION_TTS_MESSAGE
            dialog = ConfirmationDialog(title, message)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.delete_tts(self.ttsViewModel.get_index_by_tts_main_id(self.tts_main_id))
        else:
            QMessageBox.information(self, UI.DELETE, UI.CONFIRM_CHOOSE_TTS_MESSAGE)

    @pyqtSlot(int)
    def delete_tts_table(self, id):
        self._database.delete_tts_main(id)

    @pyqtSlot(str)
    def filter_list(self, text):
        self.ttsViewModel.filter_by_title(text)

    def show_tts_detail(self, id):
        if id != self.tts_main_id:
            self.tts_main_id = id
            self.view.clear_all()
            self.view.reset_search_bar()
            tts_detail_list = self._database.get_all_tts_details_list(id)
            for tts_detail in tts_detail_list:
                if tts_detail['tts_type'] == ChatType.HUMAN.value:
                    self.view.add_user_question(ChatType.HUMAN, tts_detail['tts_text'])
                else:
                    self.view.add_ai_answer(ChatType.AI, tts_detail['tts_data'], tts_detail['tts_response_format'])
                    self.view.get_last_ai_widget().set_model_name(
                        Constants.MODEL_PREFIX + tts_detail['tts_model']
                        + Constants.RESPONSE_TIME + format(float(tts_detail['elapsed_time']), ".2f"))

    def delete_tts(self, index):
        self.ttsViewModel.remove_tts(index)

    def create_new_tts(self, title=Constants.NEW_TTS):
        self.ttsViewModel.add_new_tts(title)

    def add_human_tts(self, text):
        if self.tts_main_id:
            self._database.insert_tts_detail(self.tts_main_id, ChatType.HUMAN.value, None, text,
                                             None, None, None, None)
        else:
            self.create_new_tts()
            self._database.insert_tts_detail(self.tts_main_id, ChatType.HUMAN.value, None, text,
                                             None, None, None, None)

    @pyqtSlot(str)
    def submit(self, text):
        if text and text.strip():
            self.add_human_tts(text)
            self.ttsView.update_ui_submit(ChatType.HUMAN, text)
            self.ttsModel.send_user_input(self.ttsView.create_args(text, self.llm), self.llm)
