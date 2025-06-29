from PyQt6.QtCore import QAbstractListModel, QModelIndex, Qt, pyqtSignal


class MCPListModel(QAbstractListModel):
    new_mcp_main_id_signal = pyqtSignal(int)
    remove_mcp_signal = pyqtSignal(int)

    def __init__(self, database):
        super().__init__()
        self.database = database
        self.mcp_items = self.database.get_all_mcp_main_list()
        self.filtered_mcp_items = self.mcp_items.copy()

    def rowCount(self, parent=QModelIndex()):
        return len(self.filtered_mcp_items)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            return self.filtered_mcp_items[index.row()]['title']

    def add_new_mcp(self, title):
        mcp_main_id = self.database.add_mcp_main(title)
        if mcp_main_id:
            self.beginInsertRows(QModelIndex(), 0, 0)
            self.mcp_items.insert(0, {'id': mcp_main_id, 'title': title})
            self.filtered_mcp_items = self.mcp_items.copy()
            self.endInsertRows()
            self.new_mcp_main_id_signal.emit(mcp_main_id)

    def remove_mcp(self, index):
        mcp_id = self.mcp_items[index]['id']
        if self.database.delete_mcp_main(mcp_id):
            self.beginRemoveRows(QModelIndex(), index, index)
            del self.mcp_items[index]
            self.filtered_mcp_items = self.mcp_items.copy()
            self.endRemoveRows()
            self.remove_mcp_signal.emit(mcp_id)

    def update_mcp(self, index, new_title):
        mcp_id = self.mcp_items[index.row()]['id']
        if self.database.update_mcp_main(mcp_id, new_title):
            self.mcp_items[index.row()]['title'] = new_title
            self.filtered_mcp_items = self.mcp_items.copy()
            self.dataChanged.emit(index, index, [Qt.ItemDataRole.DisplayRole])

    def get_mcp(self, index):
        return self.filtered_mcp_items[index.row()]

    def get_index_by_mcp_main_id(self, mcp_id):
        for i, mcp_item in enumerate(self.filtered_mcp_items):
            if mcp_item['id'] == mcp_id:
                return i
        return None

    def filter_by_title(self, title):
        self.beginResetModel()
        if title and title.strip():
            self.filtered_mcp_items = [item for item in self.mcp_items if title.lower() in item['title'].lower()]
        else:
            self.filtered_mcp_items = self.mcp_items.copy()
        self.endResetModel()
