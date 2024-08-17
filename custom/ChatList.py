from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtWidgets import QWidget, QDialog, \
    QListView, QVBoxLayout

from custom.ChatItemDelegate import ChatItemDelegate
from util.ConfirmationDialog import ConfirmationDialog
from util.Constants import UI
from util.RenameDialog import RenameDialog


class ChatList(QWidget):
    chat_id_signal = pyqtSignal(int)
    delete_id_signal = pyqtSignal(int)
    rename_id_signal = pyqtSignal(int, str)

    def __init__(self, model):
        super().__init__()
        self.model = model
        self.chat_list_view = QListView()
        self.chat_list_view.setModel(model)
        self.delegate = ChatItemDelegate(self, self.chat_list_view)
        self.chat_list_view.setItemDelegate(self.delegate)

        layout = QVBoxLayout()
        layout.addWidget(self.chat_list_view)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        self.chat_list_view.clicked.connect(self.on_item_clicked)
        self.chat_list_view.setMouseTracking(True)
        self.chat_list_view.viewport().installEventFilter(self)

        self.delegate.row_id_signal.connect(self.delete_chat)

    def delete_chat(self, row):
        title = UI.CONFIRM_DELETION_TITLE
        message = UI.CONFIRM_DELETION_CHAT_MESSAGE
        dialog = ConfirmationDialog(title, message)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.model.remove_chat(row)

    def eventFilter(self, source, event):
        if event.type() == QMouseEvent.Type.MouseMove:
            index = self.chat_list_view.indexAt(event.pos())
            self.delegate.setMouseOverIndex(index)
            self.chat_list_view.update(index)
        elif event.type() == QMouseEvent.Type.Leave:
            self.delegate.setMouseOverIndex(None)
            self.chat_list_view.update()
        return super().eventFilter(source, event)

    def rename_chat(self, index, text):
        title = UI.RENAME
        dialog = RenameDialog(title, text)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.model.update_chat(index, dialog.text)

    def on_item_clicked(self, index):
        chat_item = self.model.get_chat(index)
        self.chat_id_signal.emit(chat_item['id'])
