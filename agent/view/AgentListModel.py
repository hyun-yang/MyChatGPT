from PyQt6.QtCore import QAbstractListModel, QModelIndex, Qt, pyqtSignal


class AgentListModel(QAbstractListModel):
    new_agent_main_id_signal = pyqtSignal(int)
    remove_agent_signal = pyqtSignal(int)

    def __init__(self, database):
        super().__init__()
        self.database = database
        self.agent_items = self.database.get_all_agent_main_list()
        self.filtered_agent_items = self.agent_items.copy()

    def rowCount(self, parent=QModelIndex()):
        return len(self.filtered_agent_items)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            return self.filtered_agent_items[index.row()]['title']

    def add_new_agent(self, title):
        agent_main_id = self.database.add_agent_main(title)
        if agent_main_id:
            self.beginInsertRows(QModelIndex(), 0, 0)
            self.agent_items.insert(0, {'id': agent_main_id, 'title': title})
            self.filtered_agent_items = self.agent_items.copy()
            self.endInsertRows()
            self.new_agent_main_id_signal.emit(agent_main_id)

    def remove_agent(self, index):
        agent_id = self.agent_items[index]['id']
        if self.database.delete_agent_main(agent_id):
            self.beginRemoveRows(QModelIndex(), index, index)
            del self.agent_items[index]
            self.filtered_agent_items = self.agent_items.copy()
            self.endRemoveRows()
            self.remove_agent_signal.emit(agent_id)

    def update_agent(self, index, new_title):
        agent_id = self.agent_items[index.row()]['id']
        if self.database.update_agent_main(agent_id, new_title):
            self.agent_items[index.row()]['title'] = new_title
            self.filtered_agent_items = self.agent_items.copy()
            self.dataChanged.emit(index, index, [Qt.ItemDataRole.DisplayRole])

    def get_agent(self, index):
        return self.filtered_agent_items[index.row()]

    def get_index_by_agent_main_id(self, agent_id):
        for i, agent_item in enumerate(self.filtered_agent_items):
            if agent_item['id'] == agent_id:
                return i
        return None

    def filter_by_title(self, title):
        self.beginResetModel()
        if title and title.strip():
            self.filtered_agent_items = [item for item in self.agent_items if title.lower() in item['title'].lower()]
        else:
            self.filtered_agent_items = self.agent_items.copy()
        self.endResetModel()
