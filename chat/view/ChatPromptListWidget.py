from PyQt6.QtCore import pyqtSignal, QSortFilterProxyModel, Qt, QAbstractTableModel, QRegularExpression
from PyQt6.QtGui import QIcon, QGuiApplication
from PyQt6.QtSql import QSqlDatabase, QSqlQuery
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QTableView, \
    QAbstractItemView, QPushButton, QMessageBox, QPlainTextEdit, QLineEdit, QDialog, QHeaderView

from util.ConfirmationDialog import ConfirmationDialog
from util.Constants import Constants, UI, DATABASE_MESSAGE
from util.Utility import Utility


class ChatPromptListWidget(QWidget):
    sendPromptSignal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.initialize_ui()

    def initialize_ui(self):
        self._chatPromptDB = QSqlDatabase.addDatabase('QSQLITE', 'ChatPromptDBConnection')
        self._chatPromptDB.setDatabaseName(Constants.DATABASE_NAME)
        self._chatPromptDB.open()

        self.model = PromptLazyLoadTableModel(self._chatPromptDB)
        self.filter_model = FilterProxyModel()
        self.filter_model.setSourceModel(self.model)

        self.deleteButton = QPushButton(QIcon(Utility.get_icon_path('ico', 'database--minus.png')), "")
        self.deleteButton.clicked.connect(self.delete)
        self.deleteButton.setToolTip(UI.DELETE)

        self.addButton = QPushButton(QIcon(Utility.get_icon_path('ico', 'database--plus.png')), "")
        self.addButton.clicked.connect(self.add_new)
        self.addButton.setToolTip(UI.ADD)

        self.searchTerm = QLineEdit()
        self.searchTerm.setPlaceholderText(UI.SEARCH_PROMPT_DB_PLACEHOLDER)
        self.searchTerm.textChanged.connect(self.update_filter)

        search_layout = QHBoxLayout()
        search_layout.addWidget(self.searchTerm)
        search_layout.addWidget(self.deleteButton)
        search_layout.addWidget(self.addButton)
        search_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        search_layout.setContentsMargins(0, 0, 0, 0)

        searchWidget = QWidget()
        searchWidget.setLayout(search_layout)

        self.promptListView = QTableView()
        self.promptListView.setModel(self.filter_model)
        self.promptListView.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)
        self.promptListView.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.promptListView.resizeColumnsToContents()
        self.promptListView.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.promptListView.clicked.connect(self.show_contents)
        self.promptListView.setColumnHidden(0, True)  # Hide the ID column

        header = self.promptListView.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)

        self.titleWidget = QLineEdit()
        titleLabel = QLabel(UI.TITLE)
        self.detailWidget = QPlainTextEdit()
        promptLabel = QLabel(UI.PROMPT)

        detail_layout = QVBoxLayout()
        detail_layout.addWidget(titleLabel)
        detail_layout.addWidget(self.titleWidget)
        detail_layout.addWidget(promptLabel)
        detail_layout.addWidget(self.detailWidget)

        self.saveButton = QPushButton(QIcon(Utility.get_icon_path('ico', 'disk--plus.png')), "Save")
        self.saveButton.clicked.connect(self.save)

        self.copyButton = QPushButton(QIcon(Utility.get_icon_path('ico', 'clipboard--arrow.png')), "Send")
        self.copyButton.clicked.connect(self.send_prompt_signal)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.saveButton)
        button_layout.addWidget(self.copyButton)

        main_layout = QVBoxLayout()
        main_layout.addWidget(searchWidget)
        main_layout.addWidget(self.promptListView)
        main_layout.addLayout(detail_layout)
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)

    def update_filter(self):
        # index -1 will be read from all columns
        self.filter_model.setFilterKeyColumn(-1)
        self.filter_model.setFilterRegularExpression(
            QRegularExpression(self.searchTerm.text(), QRegularExpression.PatternOption.CaseInsensitiveOption))

    def refresh(self):
        self.model.reload_data()

    def show_contents(self, idx):
        source_index = self.filter_model.mapToSource(idx)
        #  you need to use 'source_index = self.filter_model.mapToSource(idx)'
        #  where clicking on a filtered row shows the wrong 'title' and 'prompt', we need to map the
        #  filtered index back to the source model index.
        #  This ensures that we are referencing the correct row in the original data model.

        # title = self.model.data(idx.siblingAtColumn(1), Qt.ItemDataRole.DisplayRole)
        # prompt = self.model.data(idx.siblingAtColumn(2), Qt.ItemDataRole.DisplayRole)

        title = self.model.data(source_index.siblingAtColumn(1), Qt.ItemDataRole.DisplayRole)
        prompt = self.model.data(source_index.siblingAtColumn(2), Qt.ItemDataRole.DisplayRole)

        self.titleWidget.setText(title)
        self.detailWidget.setPlainText(prompt)

    def send_prompt_signal(self):
        prompt = self.detailWidget.toPlainText()
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(prompt)
        self.sendPromptSignal.emit(prompt)

    def add_new(self):
        self.model.add_row()
        self.refresh()

    def save(self):
        selected_indexes = self.promptListView.selectionModel().selectedRows()
        if not selected_indexes:
            QMessageBox.warning(self, UI.WARNING_TITLE, UI.WARNING_TITLE_NO_ROW_SELECT_MESSAGE)
            return

        row = self.filter_model.mapToSource(selected_indexes[0]).row()
        title = self.titleWidget.text()
        prompt = self.detailWidget.toPlainText()
        self.model.update_row(row, title, prompt)
        self.refresh()

    def delete(self):
        title = UI.CONFIRM_DELETION_TITLE
        message = UI.CONFIRM_DELETION_ROW_MESSAGE
        selected_indexes = self.promptListView.selectionModel().selectedRows()
        if not selected_indexes:
            QMessageBox.warning(self, UI.WARNING_TITLE, UI.WARNING_TITLE_NO_ROW_DELETE_MESSAGE)
            return

        dialog = ConfirmationDialog(title, message)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            for index in selected_indexes:
                row = index.row()
                self.model.delete_row(row)
            self.refresh()


class FilterProxyModel(QSortFilterProxyModel):
    def __init__(self):
        super().__init__()
        self.searchTerm = None

    @property
    def search_text(self):
        return self.searchTerm

    @search_text.setter
    def search_text(self, value):
        self.searchTerm = value
        self.invalidateFilter()


class PromptLazyLoadTableModel(QAbstractTableModel):

    def __init__(self, db_connection):
        super().__init__()
        self.db_connection = db_connection
        self.data_cache = []
        self.load_initial_data()

    def load_initial_data(self):
        query = QSqlQuery(self.db_connection)
        query.exec("SELECT id, title, prompt FROM prompt")
        while query.next():
            id = query.value(0)
            title = query.value(1)
            prompt = query.value(2)
            self.data_cache.append((id, title, prompt))
        self.layoutChanged.emit()

    def rowCount(self, index):
        return len(self.data_cache)

    def columnCount(self, index):
        return 3

    def data(self, index, role):
        if role == Qt.ItemDataRole.DisplayRole:
            return self.data_cache[index.row()][index.column()]

    def headerData(self, section, orientation, role):
        if role == Qt.ItemDataRole.DisplayRole:
            headers = ["ID", "Title", "Prompt"]
            if orientation == Qt.Orientation.Horizontal:
                return headers[section]

    def reload_data(self):
        self.beginResetModel()
        self.data_cache.clear()
        query = QSqlQuery(self.db_connection)
        query.exec("SELECT id, title, prompt FROM prompt")
        while query.next():
            id = query.value(0)
            title = query.value(1)
            prompt = query.value(2)
            self.data_cache.append((id, title, prompt))
        self.endResetModel()

    def fetch_prompt(self, row):
        query = QSqlQuery(self.db_connection)
        id = self.data_cache[row][0]
        queryData = {}
        query.prepare("SELECT title, prompt FROM vision_tb WHERE Id = ?")
        query.addBindValue(id)
        if query.exec():
            if query.next():
                queryData['title'] = query.value(0)
                queryData['prompt'] = query.value(1)
                return queryData
        else:
            error = query.lastError()
            error_message = f"Error: {error.text()}"
            QMessageBox.critical(None, DATABASE_MESSAGE.DATABASE_TITLE_ERROR,
                                 f"{DATABASE_MESSAGE.DATABASE_FETCH_ERROR}\n{error_message}")
        return None

    def delete_row(self, row):
        id = self.data_cache[row][0]
        query = QSqlQuery(self.db_connection)
        query.prepare("DELETE FROM prompt WHERE id = ?")
        query.addBindValue(id)
        if query.exec():
            del self.data_cache[row]
            self.layoutChanged.emit()
        else:
            error = query.lastError()
            error_message = f"Error: {error.text()}"
            QMessageBox.critical(None, DATABASE_MESSAGE.DATABASE_TITLE_ERROR,
                                 f"{DATABASE_MESSAGE.DATABASE_DELETE_ERROR}\n{error_message}")

    def add_row(self):
        query = QSqlQuery(self.db_connection)
        query.prepare("INSERT INTO prompt (title, prompt) VALUES (?, ?)")
        query.addBindValue(DATABASE_MESSAGE.NEW_TITLE)
        query.addBindValue(DATABASE_MESSAGE.NEW_PROMPT)
        if query.exec():
            self.reload_data()
        else:
            error = query.lastError()
            error_message = f"Error: {error.text()}"
            QMessageBox.critical(None, DATABASE_MESSAGE.DATABASE_TITLE_ERROR,
                                 f"{DATABASE_MESSAGE.DATABASE_ADD_ERROR}\n{error_message}")

    def update_row(self, row, title, prompt):
        id = self.data_cache[row][0]
        query = QSqlQuery(self.db_connection)
        query.prepare("UPDATE prompt SET title = ?, prompt = ? WHERE id = ?")
        query.addBindValue(title)
        query.addBindValue(prompt)
        query.addBindValue(id)

        if query.exec():
            self.data_cache[row] = (id, title, prompt)
            self.layoutChanged.emit()
        else:
            error = query.lastError()
            error_message = f"Error: {error.text()}"
            QMessageBox.critical(None, DATABASE_MESSAGE.DATABASE_TITLE_ERROR,
                                 f"{DATABASE_MESSAGE.DATABASE_UPDATE_ERROR}\n{error_message}")

