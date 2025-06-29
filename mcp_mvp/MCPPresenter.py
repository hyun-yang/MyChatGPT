from PyQt6.QtCore import pyqtSlot
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QDialog, QMessageBox

from mcp_mvp.view.MCPListModel import MCPListModel
from mcp_mvp.model.MCPModel import MCPModel
from mcp_mvp.view.MCPView import MCPView
from util.ChatType import ChatType
from util.ConfirmationDialog import ConfirmationDialog
from util.Constants import Constants, UI
from util.DataManager import DataManager
from util.SettingsManager import SettingsManager
from util.Utility import Utility


class MCPPresenter(QWidget):

    def __init__(self):
        super().__init__()
        self._mcp_main_id = None
        self._mcp_main_index = None
        self.initialize_manager()
        self.initialize_ui()

    def initialize_manager(self):
        self._settings = SettingsManager.get_settings()
        self._database = DataManager.get_database()
        self.llm = Utility.get_settings_value(section="MCP", prop="llm", default="Claude", save=True)
        self.llm_mcp = Utility.get_settings_value(section="MCP", prop="llm_mcp", default="Claude_MCP", save=True)

    def initialize_ui(self):
        # View
        self.mcpViewModel = MCPListModel(self._database)
        self.mcpViewModel.new_mcp_main_id_signal.connect(self.set_mcp_main_id)
        self.mcpViewModel.remove_mcp_signal.connect(self.clear_mcp)
        self.mcpView = MCPView(self.mcpViewModel)

        # Model
        self.mcpModel = MCPModel()

        # View signal
        self.mcpView.submitted_signal.connect(self.submit)
        self.mcpView.stop_signal.connect(self.mcpModel.force_stop)
        self.mcpView.current_llm_signal.connect(self.set_current_llm_signal)
        self.mcpView.reload_mcp_detail_signal.connect(self.show_mcp_detail)
        self.mcpView.new_mcp_signal.connect(self.create_new_mcp)

        self.mcpView.prompt_list.sendPromptSignal.connect(self.mcpView.set_prompt)

        self.mcpView.mcp_history.new_mcp_signal.connect(self.create_new_mcp)
        self.mcpView.mcp_history.delete_mcp_signal.connect(self.confirm_delete_mcp)
        self.mcpView.mcp_history.mcp_list.delete_id_signal.connect(self.delete_mcp_table)
        self.mcpView.mcp_history.filter_signal.connect(self.filter_list)
        self.mcpView.set_default_tab(self.llm_mcp)

        # Model signal
        self.mcpModel.thread_started_signal.connect(self.mcpView.start_mcp)
        self.mcpModel.thread_finished_signal.connect(self.mcpView.finish_mcp)
        self.mcpModel.response_signal.connect(self.mcpView.update_ui)
        self.mcpModel.response_finished_signal.connect(self.handle_response_finished_signal)

        # View
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.mcpView)

        self.initialize_mcp_history()

        self.setLayout(main_layout)

    def initialize_mcp_history(self):
        self.mcp_list = self.mcpView.mcp_history.mcp_list
        self.mcp_list.mcp_id_signal.connect(self.show_mcp_detail)

    def set_mcp_main_id(self, mcp_main_id):
        self.mcp_main_id = mcp_main_id
        self.view.clear_all()

    @pyqtSlot(str, str, float, bool)
    def handle_response_finished_signal(self, model, finish_reason, elapsed_time, stream):
        self.view.reset_file_list(self.llm_mcp, True)
        last_ai_widget = self.view.get_last_ai_widget()
        if last_ai_widget:
            self.view.update_ui_finish(model, finish_reason, elapsed_time, stream)
            self._database.insert_mcp_detail(self.mcp_main_id, ChatType.AI.value, model,
                                             self.view.get_last_ai_widget().get_original_text(), elapsed_time,
                                             finish_reason)

    @property
    def model(self):
        return self.mcpModel

    @property
    def view(self):
        return self.mcpView

    @property
    def mcp_main_id(self):
        return self._mcp_main_id

    @mcp_main_id.setter
    def mcp_main_id(self, value):
        self._mcp_main_id = value

    @pyqtSlot(str)
    def set_current_llm_signal(self, llm_name):
        self.llm = llm_name

    @pyqtSlot(int)
    def clear_mcp(self, delete_id):
        if self.mcp_main_id == delete_id:
            self.mcp_main_id = None
            self.view.clear_all()

    @pyqtSlot()
    def confirm_delete_mcp(self):
        if self.mcp_main_id:
            title = UI.CONFIRM_DELETION_TITLE
            message = UI.CONFIRM_DELETION_CHAT_MESSAGE
            dialog = ConfirmationDialog(title, message)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.delete_mcp(self.mcpViewModel.get_index_by_mcp_main_id(self.mcp_main_id))
        else:
            QMessageBox.information(self, UI.DELETE, UI.CONFIRM_CHOOSE_CHAT_MESSAGE)

    @pyqtSlot(int)
    def delete_mcp_table(self, id):
        self._database.delete_mcp_main(id)

    @pyqtSlot(str)
    def filter_list(self, text):
        self.mcpViewModel.filter_by_title(text)

    def show_mcp_detail(self, id):
        if id == -1:
            self.get_mcp_detail(self.mcp_main_id)
        elif id != self.mcp_main_id:
            self.mcp_main_id = id
            self.get_mcp_detail(self.mcp_main_id)

    def get_mcp_detail(self, id):
        self.view.clear_all()
        self.view.reset_search_bar()
        mcp_detail_list = self._database.get_all_mcp_details_list(id)
        for mcp_detail in mcp_detail_list:
            if mcp_detail['mcp_type'] == ChatType.HUMAN.value:
                self.view.add_user_question(ChatType.HUMAN, mcp_detail['mcp'])
            else:
                self.view.add_user_question(ChatType.AI, mcp_detail['mcp'])
                self.view.get_last_ai_widget().set_model_name(
                    Constants.MODEL_PREFIX + mcp_detail['mcp_model']
                    + Constants.RESPONSE_TIME + format(float(mcp_detail['elapsed_time']), ".2f"))

    def delete_mcp(self, index):
        self.mcpViewModel.remove_mcp(index)

    def create_new_mcp(self, title=Constants.NEW_MCP):
        self.mcpViewModel.add_new_mcp(title)

    def add_human_mcp(self, text):
        if self.mcp_main_id:
            self._database.insert_mcp_detail(self.mcp_main_id, ChatType.HUMAN.value, None, text, None, None)
        else:
            self.create_new_mcp()
            self._database.insert_mcp_detail(self.mcp_main_id, ChatType.HUMAN.value, None, text, None, None)

    def update_mcp(self, index, new_title):
        self.mcpViewModel.update_mcp(index, new_title)

    def read_mcp(self, index):
        return self.mcpViewModel.get_mcp(index)

    @pyqtSlot(str, str)
    def submit(self, llm_mcp, text):
        if text and text.strip():
            self.llm_mcp = llm_mcp
            self.add_human_mcp(text)
            self.mcpView.update_ui_submit(ChatType.HUMAN, text)
            self.mcpModel.send_user_input(self.mcpView.create_args(text, llm_mcp, self.llm), self.llm)
