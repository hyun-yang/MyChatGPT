from PyQt6.QtCore import QAbstractListModel, QModelIndex, Qt, pyqtSignal


class ChatListModel(QAbstractListModel):
    new_chat_main_id_signal = pyqtSignal(int)
    remove_chat_signal = pyqtSignal(int)

    def __init__(self, database):
        super().__init__()
        self.database = database
        self.chat_items = self.database.get_all_chat_main_list()
        self.filtered_chat_items = self.chat_items.copy()

    def rowCount(self, parent=QModelIndex()):
        return len(self.filtered_chat_items)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            return self.filtered_chat_items[index.row()]['title']

    def add_new_chat(self, title):
        chat_main_id = self.database.add_chat_main(title)
        if chat_main_id:
            self.beginInsertRows(QModelIndex(), 0, 0)
            self.chat_items.insert(0, {'id': chat_main_id, 'title': title})
            self.filtered_chat_items = self.chat_items.copy()
            self.endInsertRows()
            self.new_chat_main_id_signal.emit(chat_main_id)

    def remove_chat(self, index):
        chat_id = self.chat_items[index]['id']
        if self.database.delete_chat_main(chat_id):
            self.beginRemoveRows(QModelIndex(), index, index)
            del self.chat_items[index]
            self.filtered_chat_items = self.chat_items.copy()
            self.endRemoveRows()
            self.remove_chat_signal.emit(chat_id)

    def update_chat(self, index, new_title):
        chat_id = self.chat_items[index.row()]['id']
        if self.database.update_chat_main(chat_id, new_title):
            self.chat_items[index.row()]['title'] = new_title
            self.filtered_chat_items = self.chat_items.copy()
            self.dataChanged.emit(index, index, [Qt.ItemDataRole.DisplayRole])

    def get_chat(self, index):
        return self.filtered_chat_items[index.row()]

    def get_index_by_chat_main_id(self, chat_main_id):
        for i, chat_item in enumerate(self.filtered_chat_items):
            if chat_item['id'] == chat_main_id:
                return i
        return None

    def filter_by_title(self, title):
        self.beginResetModel()
        if title and title.strip():
            self.filtered_chat_items = [item for item in self.chat_items if title.lower() in item['title'].lower()]
        else:
            self.filtered_chat_items = self.chat_items.copy()
        self.endResetModel()
