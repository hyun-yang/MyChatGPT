from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtWidgets import QWidget, QDialog, \
    QListView, QVBoxLayout

from util.Constants import UI
from agent.view.AgentItemDelegate import AgentItemDelegate
from util.ConfirmationDialog import ConfirmationDialog
from util.RenameDialog import RenameDialog


class AgentList(QWidget):
    agent_id_signal = pyqtSignal(int)
    delete_id_signal = pyqtSignal(int)
    rename_id_signal = pyqtSignal(int, str)

    def __init__(self, model):
        super().__init__()
        self.model = model
        self.agent_list_view = QListView()
        self.agent_list_view.setModel(model)
        self.delegate = AgentItemDelegate(self, self.agent_list_view)
        self.agent_list_view.setItemDelegate(self.delegate)

        layout = QVBoxLayout()
        layout.addWidget(self.agent_list_view)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        self.agent_list_view.clicked.connect(self.on_item_clicked)
        self.agent_list_view.setMouseTracking(True)
        self.agent_list_view.viewport().installEventFilter(self)

        self.delegate.row_id_signal.connect(self.delete_agent)

    def delete_agent(self, row):
        title = UI.CONFIRM_DELETION_TITLE
        message = UI.CONFIRM_DELETION_AGENT_MESSAGE
        dialog = ConfirmationDialog(title, message)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.model.remove_agent(row)

    def eventFilter(self, source, event):
        if event.type() == QMouseEvent.Type.MouseMove:
            index = self.agent_list_view.indexAt(event.pos())
            self.delegate.set_mouse_over_index(index)
            self.agent_list_view.update(index)
        elif event.type() == QMouseEvent.Type.Leave:
            self.delegate.set_mouse_over_index(None)
            self.agent_list_view.update()
        return super().eventFilter(source, event)

    def rename_chat(self, index, text):
        title = UI.RENAME
        dialog = RenameDialog(title, text)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.model.update_agent(index, dialog.text)

    def on_item_clicked(self, index):
        agent_item = self.model.get_agent(index)
        self.agent_id_signal.emit(agent_item['id'])
