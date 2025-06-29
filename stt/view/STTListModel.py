from PyQt6.QtCore import QAbstractListModel, QModelIndex, Qt, pyqtSignal


class STTListModel(QAbstractListModel):
    new_stt_main_id_signal = pyqtSignal(int)
    remove_stt_signal = pyqtSignal(int)

    def __init__(self, database):
        super().__init__()
        self.database = database
        self.stt_items = self.database.get_all_stt_main_list()
        self.filtered_stt_items = self.stt_items.copy()

    def rowCount(self, parent=QModelIndex()):
        return len(self.filtered_stt_items)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            return self.filtered_stt_items[index.row()]['title']

    def add_new_stt(self, title):
        stt_main_id = self.database.add_stt_main(title)
        if stt_main_id:
            self.beginInsertRows(QModelIndex(), 0, 0)
            self.stt_items.insert(0, {'id': stt_main_id, 'title': title})
            self.filtered_stt_items = self.stt_items.copy()
            self.endInsertRows()
            self.new_stt_main_id_signal.emit(stt_main_id)

    def remove_stt(self, index):
        stt_id = self.stt_items[index]['id']
        if self.database.delete_stt_main(stt_id):
            self.beginRemoveRows(QModelIndex(), index, index)
            del self.stt_items[index]
            self.filtered_stt_items = self.stt_items.copy()
            self.endRemoveRows()
            self.remove_stt_signal.emit(stt_id)

    def update_stt(self, index, new_title):
        stt_id = self.stt_items[index.row()]['id']
        if self.database.update_stt_main(stt_id, new_title):
            self.stt_items[index.row()]['title'] = new_title
            self.filtered_stt_items = self.stt_items.copy()
            self.dataChanged.emit(index, index, [Qt.ItemDataRole.DisplayRole])

    def get_stt(self, index):
        return self.filtered_stt_items[index.row()]

    def get_index_by_stt_main_id(self, stt_id):
        for i, stt_item in enumerate(self.filtered_stt_items):
            if stt_item['id'] == stt_id:
                return i
        return None

    def filter_by_title(self, title):
        self.beginResetModel()
        if title and title.strip():
            self.filtered_stt_items = [item for item in self.stt_items if title.lower() in item['title'].lower()]
        else:
            self.filtered_stt_items = self.stt_items.copy()
        self.endResetModel()
