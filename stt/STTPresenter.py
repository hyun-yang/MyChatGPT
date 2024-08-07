from PyQt6.QtCore import pyqtSlot
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QDialog, QMessageBox

from stt.model.STTListModel import STTListModel
from stt.model.STTModel import STTModel
from stt.view.STTView import STTView
from util.ChatType import ChatType
from util.ConfirmationDialog import ConfirmationDialog
from util.Constants import AIProviderName, Constants, UI
from util.DataManager import DataManager
from util.SettingsManager import SettingsManager
from util.Utility import Utility


class STTPresenter(QWidget):

    def __init__(self):
        super().__init__()
        self._stt_main_id = None
        self._stt_main_index = None
        self.initialize_manager()
        self.initialize_ui()

    def initialize_manager(self):
        self._settings = SettingsManager.get_settings()
        self._database = DataManager.get_database()
        self.llm = AIProviderName.OPENAI.value

    def initialize_ui(self):
        # View
        self.sttViewModel = STTListModel(self._database)
        self.sttViewModel.new_stt_main_id_signal.connect(self.set_stt_main_id)
        self.sttViewModel.remove_stt_signal.connect(self.clear_stt)
        self.sttView = STTView(self.sttViewModel)

        # Model
        self.sttModel = STTModel()

        # View signal
        self.sttView.submitted_signal.connect(self.submit)
        self.sttView.stop_signal.connect(self.sttModel.force_stop)
        self.sttView.current_llm_signal.connect(self.set_current_llm_signal)
        self.sttView.stt_history.new_stt_signal.connect(self.create_new_stt)
        self.sttView.stt_history.delete_stt_signal.connect(self.confirm_delete_stt)
        self.sttView.stt_history.stt_list.delete_id_signal.connect(self.delete_stt_table)
        self.sttView.stt_history.filter_signal.connect(self.filter_list)
        self.sttView.set_default_tab(self.llm)

        # Model signal
        self.sttModel.thread_started_signal.connect(self.sttView.start_chat)
        self.sttModel.thread_finished_signal.connect(self.sttView.finish_chat)
        self.sttModel.response_signal.connect(self.handle_response_signal)
        self.sttModel.response_finished_signal.connect(self.handle_response_finished_signal)

        # View
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.sttView)

        self.initialize_stt_history()

        self.setLayout(main_layout)

    def initialize_stt_history(self):
        self.stt_list = self.sttView.stt_history.stt_list
        self.stt_list.stt_id_signal.connect(self.show_stt_detail)

    def set_stt_main_id(self, stt_main_id):
        self.stt_main_id = stt_main_id
        self.view.clear_all()

    @pyqtSlot(str, str)
    def handle_response_signal(self, result, response_format):
        self.stt_text = result
        self.response_format = response_format
        self.sttView.update_ui(self.stt_text)

    @pyqtSlot(str, str, float, bool)
    def handle_response_finished_signal(self, model, finish_reason, elapsed_time, stream):
        self.sttView.update_ui_finish(model, finish_reason, elapsed_time, stream)
        self._database.insert_stt_detail(self.stt_main_id, ChatType.AI.value, model, self.stt_text,
                                         self.response_format, None, elapsed_time, finish_reason)

    @property
    def model(self):
        return self.sttModel

    @property
    def view(self):
        return self.sttView

    @property
    def stt_main_id(self):
        return self._stt_main_id

    @stt_main_id.setter
    def stt_main_id(self, value):
        self._stt_main_id = value

    @pyqtSlot(str)
    def set_current_llm_signal(self, llm_name):
        self.llm = llm_name

    @pyqtSlot(int)
    def clear_stt(self, delete_id):
        if self.stt_main_id == delete_id:
            self.stt_main_id = None
            self.view.clear_all()

    @pyqtSlot()
    def confirm_delete_stt(self):
        if self.stt_main_id:
            title = UI.CONFIRM_DELETION_TITLE
            message = UI.CONFIRM_DELETION_STT_MESSAGE
            dialog = ConfirmationDialog(title, message)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.delete_stt(self.sttViewModel.get_index_by_stt_main_id(self.stt_main_id))
        else:
            QMessageBox.information(self, UI.DELETE, UI.CONFIRM_CHOOSE_STT_MESSAGE)

    @pyqtSlot(int)
    def delete_stt_table(self, id):
        self._database.delete_stt_main(id)

    @pyqtSlot(str)
    def filter_list(self, text):
        self.sttViewModel.filter_by_title(text)

    def show_stt_detail(self, id):
        if id != self.stt_main_id:
            self.stt_main_id = id
            self.view.clear_all()
            self.view.reset_search_bar()
            stt_detail_list = self._database.get_all_stt_details_list(id)
            for stt_detail in stt_detail_list:
                if stt_detail['stt_type'] == ChatType.HUMAN.value:
                    self.view.add_user_question(ChatType.HUMAN, None,
                                                Utility.create_temp_file(stt_detail['stt_data'],
                                                                         self.sttView.stt_response_format, True))
                else:
                    self.view.add_ai_answer(ChatType.AI, stt_detail['stt_text'],
                                            Constants.MODEL_PREFIX + stt_detail['stt_model'])
                    self.view.get_last_ai_widget().set_model_name(
                        Constants.MODEL_PREFIX + stt_detail['stt_model']
                        + " | Response Time : " + format(float(stt_detail['elapsed_time']), ".2f"))

    def delete_stt(self, index):
        self.sttViewModel.remove_stt(index)

    def create_new_stt(self, title=Constants.NEW_STT):
        self.sttViewModel.add_new_stt(title)

    def add_human_stt(self, text, filepath):
        if self.stt_main_id:
            self._database.insert_stt_detail(self.stt_main_id, ChatType.HUMAN.value, self.sttView.stt_model, text,
                                             self.sttView.stt_response_format, Utility.base64_encode_file(filepath),
                                             None, None)
        else:
            self.create_new_stt()
            self._database.insert_stt_detail(self.stt_main_id, ChatType.HUMAN.value, self.sttView.stt_model, text,
                                             self.sttView.stt_response_format, Utility.base64_encode_file(filepath),
                                             None, None)

    @pyqtSlot(str, str)
    def submit(self, text, filepath):
        if filepath:
            self.add_human_stt(text, filepath)
            self.sttView.update_ui_submit(ChatType.HUMAN, text, filepath)
            self.sttModel.send_user_input(self.sttView.create_args(self.llm, text, filepath), self.llm)
