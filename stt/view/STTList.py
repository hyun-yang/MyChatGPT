from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtWidgets import QWidget, QDialog, \
    QListView, QVBoxLayout

from stt.view.STTItemDelegate import STTItemDelegate
from util.ConfirmationDialog import ConfirmationDialog
from util.Constants import UI
from util.RenameDialog import RenameDialog


class STTList(QWidget):
    stt_id_signal = pyqtSignal(int)
    delete_id_signal = pyqtSignal(int)
    rename_id_signal = pyqtSignal(int, str)

    def __init__(self, model):
        super().__init__()
        self.model = model
        self.stt_list_view = QListView()
        self.stt_list_view.setModel(model)
        self.delegate = STTItemDelegate(self, self.stt_list_view)
        self.stt_list_view.setItemDelegate(self.delegate)

        layout = QVBoxLayout()
        layout.addWidget(self.stt_list_view)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        self.stt_list_view.clicked.connect(self.on_item_clicked)
        self.stt_list_view.setMouseTracking(True)
        self.stt_list_view.viewport().installEventFilter(self)

        self.delegate.row_id_signal.connect(self.delete_stt)

    def delete_stt(self, row):
        title = UI.CONFIRM_DELETION_TITLE
        message = UI.CONFIRM_DELETION_STT_MESSAGE
        dialog = ConfirmationDialog(title, message)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.model.remove_stt(row)

    def eventFilter(self, source, event):
        if event.type() == QMouseEvent.Type.MouseMove:
            index = self.stt_list_view.indexAt(event.pos())
            self.delegate.set_mouse_over_index(index)
            self.stt_list_view.update(index)
        elif event.type() == QMouseEvent.Type.Leave:
            self.delegate.set_mouse_over_index(None)
            self.stt_list_view.update()
        return super().eventFilter(source, event)

    def rename_chat(self, index, text):
        title = UI.RENAME
        dialog = RenameDialog(title, text)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.model.update_stt(index, dialog.text)

    def on_item_clicked(self, index):
        stt_item = self.model.get_stt(index)
        self.stt_id_signal.emit(stt_item['id'])
