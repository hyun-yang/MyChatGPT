from PyQt6.QtCore import pyqtSlot
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QDialog, QMessageBox

from agent.view.AgentListModel import AgentListModel
from agent.model.AgentModel import AgentModel
from agent.view.AgentView import AgentView
from util.ChatType import ChatType
from util.ConfirmationDialog import ConfirmationDialog
from util.Constants import Constants, UI
from util.DataManager import DataManager
from util.SettingsManager import SettingsManager
from util.Utility import Utility


class AgentPresenter(QWidget):

    def __init__(self):
        super().__init__()
        self._agent_main_id = None
        self._agent_main_index = None
        self.initialize_manager()
        self.initialize_ui()

    def initialize_manager(self):
        self._settings = SettingsManager.get_settings()
        self._database = DataManager.get_database()
        self.llm = Utility.get_settings_value(section="Agent_Pattern", prop="llm", default="OpenAI", save=True)
        self.agent_pattern = Utility.get_settings_value(section="Agent_Pattern", prop="agent_pattern", default="Evaluator", save=True)

    def initialize_ui(self):
        # View
        self.agentViewModel = AgentListModel(self._database)
        self.agentViewModel.new_agent_main_id_signal.connect(self.set_agent_main_id)
        self.agentViewModel.remove_agent_signal.connect(self.clear_agent)
        self.agentView = AgentView(self.agentViewModel)

        # Model
        self.agentModel = AgentModel()

        # View signal
        self.agentView.submitted_signal.connect(self.submit)
        self.agentView.stop_signal.connect(self.agentModel.force_stop)
        self.agentView.current_llm_signal.connect(self.set_current_llm_signal)
        self.agentView.reload_agent_detail_signal.connect(self.show_agent_detail)
        self.agentView.new_agent_signal.connect(self.create_new_agent)

        self.agentView.prompt_list.sendPromptSignal.connect(self.agentView.set_prompt)

        self.agentView.agent_history.new_agent_signal.connect(self.create_new_agent)
        self.agentView.agent_history.delete_agent_signal.connect(self.confirm_delete_agent)
        self.agentView.agent_history.agent_list.delete_id_signal.connect(self.delete_agent_table)
        self.agentView.agent_history.filter_signal.connect(self.filter_list)
        self.agentView.set_default_tab(self.agent_pattern)

        # Model signal
        self.agentModel.thread_started_signal.connect(self.agentView.start_agent)
        self.agentModel.thread_finished_signal.connect(self.agentView.finish_agent)
        self.agentModel.response_signal.connect(self.handle_response_signal)
        self.agentModel.response_finished_signal.connect(self.handle_response_finished_signal)

        # View
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.agentView)

        self.initialize_agent_history()

        self.setLayout(main_layout)

    def initialize_agent_history(self):
        self.agent_list = self.agentView.agent_history.agent_list
        self.agent_list.agent_id_signal.connect(self.show_agent_detail)

    def set_agent_main_id(self, agent_main_id):
        self.agent_main_id = agent_main_id
        self.view.clear_all()

    @pyqtSlot(str, bool)
    def handle_response_signal(self, result, stream):
        self.agent_text = result
        self.agentView.update_ui(self.agent_text, stream)

    @pyqtSlot(str, str, float, bool)
    def handle_response_finished_signal(self, model, finish_reason, elapsed_time, stream):
        # self.view.reset_file_list(self.llm, True)
        last_ai_widget = self.view.get_last_ai_widget()
        if last_ai_widget:
            self.agentView.update_ui_finish(model, finish_reason, elapsed_time, stream)
            self._database.insert_agent_detail(self.agent_main_id, ChatType.AI.value, model,
                                              self.view.get_last_ai_widget().get_original_text(), elapsed_time,
                                              finish_reason)

    @property
    def model(self):
        return self.agentModel

    @property
    def view(self):
        return self.agentView

    @property
    def agent_main_id(self):
        return self._agent_main_id

    @agent_main_id.setter
    def agent_main_id(self, value):
        self._agent_main_id = value

    @pyqtSlot(str)
    def set_current_llm_signal(self, llm_name):
        self.llm = llm_name

    @pyqtSlot(int)
    def clear_agent(self, delete_id):
        if self.agent_main_id == delete_id:
            self.agent_main_id = None
            self.view.clear_all()

    @pyqtSlot()
    def confirm_delete_agent(self):
        if self.agent_main_id:
            title = UI.CONFIRM_DELETION_TITLE
            message = UI.CONFIRM_DELETION_AGENT_MESSAGE
            dialog = ConfirmationDialog(title, message)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.delete_agent(self.agentViewModel.get_index_by_agent_main_id(self.agent_main_id))
        else:
            QMessageBox.information(self, UI.DELETE, UI.CONFIRM_CHOOSE_AGENT_MESSAGE)

    @pyqtSlot(int)
    def delete_agent_table(self, id):
        self._database.delete_agent_main(id)

    @pyqtSlot(str)
    def filter_list(self, text):
        self.agentViewModel.filter_by_title(text)

    def show_agent_detail(self, id):
        if id == -1:
            self.get_agent_detail(self.agent_main_id)
        elif id != self.agent_main_id:
            self.agent_main_id = id
            self.get_agent_detail(self.agent_main_id)

    def get_agent_detail(self, id):
        self.view.clear_all()
        self.view.reset_search_bar()
        agent_detail_list = self._database.get_all_agent_details_list(id)
        for agent_detail in agent_detail_list:
            if agent_detail['agent_type'] == ChatType.HUMAN.value:
                self.view.add_user_question(ChatType.HUMAN, agent_detail['agent'])
            else:
                self.view.add_user_question(ChatType.AI, agent_detail['agent'])
                self.view.get_last_ai_widget().set_model_name(
                    Constants.MODEL_PREFIX + agent_detail['agent_model']
                    + Constants.RESPONSE_TIME + format(float(agent_detail['elapsed_time']), ".2f"))

    def delete_agent(self, index):
        self.agentViewModel.remove_agent(index)

    def create_new_agent(self, title=Constants.NEW_AGENT):
        self.agentViewModel.add_new_agent(title)

    def add_human_agent(self, text):
        if self.agent_main_id:
            self._database.insert_agent_detail(self.agent_main_id, ChatType.HUMAN.value, None, text, None, None)
        else:
            self.create_new_agent()
            self._database.insert_agent_detail(self.agent_main_id, ChatType.HUMAN.value, None, text, None, None)

    def update_agent(self, index, new_title):
        self.agentViewModel.update_agent(index, new_title)

    def read_agent(self, index):
        return self.agentViewModel.get_agent(index)

    @pyqtSlot(str, str)
    def submit(self, text, agent_pattern):
        if text and text.strip():
            self.add_human_agent(text)
            self.agentView.update_ui_submit(ChatType.HUMAN, text)
            self.agentModel.send_user_input(self.agentView.create_args(text, self.llm, agent_pattern), self.llm, agent_pattern)
