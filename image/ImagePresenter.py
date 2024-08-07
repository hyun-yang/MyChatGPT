from PyQt6.QtCore import pyqtSlot
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QDialog, QMessageBox

from image.model.ImageListModel import ImageListModel
from image.model.ImageModel import ImageModel
from image.view.ImageView import ImageView
from util.ChatType import ChatType
from util.ConfirmationDialog import ConfirmationDialog
from util.Constants import Constants, AIProviderName, UI
from util.DataManager import DataManager
from util.SettingsManager import SettingsManager
from util.Utility import Utility


class ImagePresenter(QWidget):

    def __init__(self):
        super().__init__()
        self._image_main_id = None
        self._image_main_index = None
        self.initialize_manager()
        self.initialize_ui()

    def initialize_manager(self):
        self._settings = SettingsManager.get_settings()
        self._database = DataManager.get_database()
        self.llm = AIProviderName.OPENAI.value

    def initialize_ui(self):
        # View
        self.imageViewModel = ImageListModel(self._database)
        self.imageViewModel.new_image_main_id_signal.connect(self.set_image_main_id)
        self.imageViewModel.remove_image_signal.connect(self.clear_image)
        self.imageView = ImageView(self.imageViewModel)

        # Model
        self.imageModel = ImageModel()

        # View signal
        self.imageView.submitted_signal.connect(self.submit)
        self.imageView.stop_signal.connect(self.imageModel.force_stop)
        self.imageView.current_llm_signal.connect(self.set_current_llm_signal)

        self.imageView.image_history.new_image_signal.connect(self.create_new_image)
        self.imageView.image_history.delete_image_signal.connect(self.confirm_delete_image)
        self.imageView.image_history.image_list.delete_id_signal.connect(self.delete_image_table)
        self.imageView.image_history.filter_signal.connect(self.filter_list)
        self.imageView.set_default_tab(self.llm)

        # Model signal
        self.imageModel.thread_started_signal.connect(self.imageView.start_chat)
        self.imageModel.thread_finished_signal.connect(self.imageView.finish_chat)
        self.imageModel.response_signal.connect(self.handle_response_signal)
        self.imageModel.response_finished_signal.connect(self.handle_response_finished_signal)

        # View
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.imageView)

        self.initialize_image_history()

        self.setLayout(main_layout)

    def initialize_image_history(self):
        self.image_list = self.imageView.image_history.image_list
        self.image_list.image_id_signal.connect(self.show_image_detail)

    def set_image_main_id(self, image_main_id):
        self.image_main_id = image_main_id
        self.view.clear_all()

    @pyqtSlot(str, str)
    def handle_response_signal(self, image_data, revised_prompt):
        self.image_data = image_data
        self.revised_prompt = revised_prompt
        self.imageView.update_ui(self.image_data, revised_prompt)

    @pyqtSlot(str, str, float, bool)
    def handle_response_finished_signal(self, model, finish_reason, elapsed_time, stream):
        self.imageView.update_ui_finish(model, finish_reason, elapsed_time, stream)
        image_detail_id = self._database.insert_image_detail(self.image_main_id, ChatType.AI.value, model,
                                                             self.image_text, self.view.creation_type,
                                                             self.revised_prompt, elapsed_time, finish_reason)
        self._database.insert_image_file(image_detail_id, self.image_data)

    @property
    def model(self):
        return self.imageModel

    @property
    def view(self):
        return self.imageView

    @property
    def image_main_id(self):
        return self._image_main_id

    @image_main_id.setter
    def image_main_id(self, value):
        self._image_main_id = value

    @pyqtSlot(str)
    def set_current_llm_signal(self, llm_name):
        self.llm = llm_name

    @pyqtSlot(int)
    def clear_image(self, delete_id):
        if self.image_main_id == delete_id:
            self.image_main_id = None
            self.view.clear_all()

    @pyqtSlot()
    def confirm_delete_image(self):
        if self.image_main_id:
            title = UI.CONFIRM_DELETION_TITLE
            message = UI.CONFIRM_DELETION_IMAGE_MESSAGE
            dialog = ConfirmationDialog(title, message)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.delete_image(self.imageViewModel.get_index_by_image_main_id(self.image_main_id))
        else:
            QMessageBox.information(self, UI.DELETE, UI.CONFIRM_CHOOSE_IMAGE_MESSAGE)

    @pyqtSlot(int)
    def delete_image_table(self, id):
        self._database.delete_image_main(id)

    @pyqtSlot(str)
    def filter_list(self, text):
        self.imageViewModel.filter_by_title(text)

    def show_image_detail(self, id):
        if id != self.image_main_id:
            self.image_main_id = id
            self.view.clear_all()
            self.view.reset_search_bar()
            image_detail_list = self._database.get_all_image_details_list(id)
            for image_detail in image_detail_list:
                if image_detail['image_type'] == ChatType.HUMAN.value:
                    image_detail_id = f"{Constants.IMAGE_DETAIL_TABLE_ID_NAME}{id}_{image_detail['id']}"
                    image_detail_file_list = self._database.get_all_image_details_file_list(image_detail_id)
                    file_list = []
                    for image_detail_file in image_detail_file_list:
                        file_list.append(Utility.create_temp_file(image_detail_file['image_detail_file_data'],
                                                                  Constants.VISION_IMAGE_EXTENSION, True))

                    self.view.add_user_question(ChatType.HUMAN, image_detail['image_text'], file_list)
                else:
                    image_detail_id = f"{Constants.IMAGE_DETAIL_TABLE_ID_NAME}{id}_{image_detail['id']}"
                    image_detail_file = self._database.get_image_detail_file(image_detail_id)
                    self.view.update_ui(image_detail_file['image_detail_file_data'], image_detail['image_revised_prompt'])
                    self.view.get_last_ai_widget().set_model_name(
                        Constants.MODEL_PREFIX + image_detail['image_model']
                        + " | Response Time : " + format(float(image_detail['elapsed_time']), ".2f"))

    def delete_image(self, index):
        self.imageViewModel.remove_image(index)

    def create_new_image(self, title=Constants.NEW_IMAGE):
        self.imageViewModel.add_new_image(title)

    def add_human_image(self, text, file_list):
        if self.image_main_id:
            image_detail_id = self._database.insert_image_detail(self.image_main_id, ChatType.HUMAN.value,
                                                                 None, text, self.view.creation_type,
                                                                 None, None, None)
        else:
            self.create_new_image()
            image_detail_id = self._database.insert_image_detail(self.image_main_id, ChatType.HUMAN.value,
                                                                 None, text, self.view.creation_type,
                                                                 None, None, None)

        if self.view.creation_type in [Constants.DALLE_EDIT, Constants.DALLE_VARIATION] and image_detail_id:
            for file in file_list:
                self._database.insert_image_file(image_detail_id, Utility.base64_encode_file(file))

    @pyqtSlot(str, list)
    def submit(self, text, file_list):
        self.image_text = text
        if file_list is not None:
            self.add_human_image(text, file_list)
            self.imageView.update_ui_submit(ChatType.HUMAN, text, file_list)
            self.imageModel.send_user_input(self.imageView.create_args(self.llm, text, file_list), self.llm)
