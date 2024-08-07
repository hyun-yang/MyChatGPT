from PyQt6.QtCore import QAbstractListModel, QModelIndex, Qt, pyqtSignal


class TTSListModel(QAbstractListModel):
    new_tts_main_id_signal = pyqtSignal(int)
    remove_tts_signal = pyqtSignal(int)

    def __init__(self, database):
        super().__init__()
        self.database = database
        self.tts_items = self.database.get_all_tts_main_list()
        self.filtered_tts_items = self.tts_items.copy()

    def rowCount(self, parent=QModelIndex()):
        return len(self.filtered_tts_items)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            return self.filtered_tts_items[index.row()]['title']

    def add_new_tts(self, title):
        tts_main_id = self.database.add_tts_main(title)
        if tts_main_id:
            self.beginInsertRows(QModelIndex(), 0, 0)
            self.tts_items.insert(0, {'id': tts_main_id, 'title': title})
            self.filtered_tts_items = self.tts_items.copy()
            self.endInsertRows()
            self.new_tts_main_id_signal.emit(tts_main_id)

    def remove_tts(self, index):
        tts_id = self.tts_items[index]['id']
        if self.database.delete_tts_main(tts_id):
            self.beginRemoveRows(QModelIndex(), index, index)
            del self.tts_items[index]
            self.filtered_tts_items = self.tts_items.copy()
            self.endRemoveRows()
            self.remove_tts_signal.emit(tts_id)

    def update_tts(self, index, new_title):
        tts_id = self.tts_items[index.row()]['id']
        if self.database.update_tts_main(tts_id, new_title):
            self.tts_items[index.row()]['title'] = new_title
            self.filtered_tts_items = self.tts_items.copy()
            self.dataChanged.emit(index, index, [Qt.ItemDataRole.DisplayRole])

    def get_tts(self, index):
        return self.filtered_tts_items[index.row()]

    def get_index_by_tts_main_id(self, tts_id):
        for i, tts_item in enumerate(self.filtered_tts_items):
            if tts_item['id'] == tts_id:
                return i
        return None

    def filter_by_title(self, title):
        self.beginResetModel()
        if title and title.strip():
            self.filtered_tts_items = [item for item in self.tts_items if title.lower() in item['title'].lower()]
        else:
            self.filtered_tts_items = self.tts_items.copy()
        self.endResetModel()
