from PyQt6.QtCore import QAbstractListModel, QModelIndex, Qt, pyqtSignal


class ImageListModel(QAbstractListModel):
    new_image_main_id_signal = pyqtSignal(int)
    remove_image_signal = pyqtSignal(int)

    def __init__(self, database):
        super().__init__()
        self.database = database
        self.image_items = self.database.get_all_image_main_list()
        self.filtered_image_items = self.image_items.copy()

    def rowCount(self, parent=QModelIndex()):
        return len(self.filtered_image_items)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            return self.filtered_image_items[index.row()]['title']

    def add_new_image(self, title):
        image_main_id = self.database.add_image_main(title)
        if image_main_id:
            self.beginInsertRows(QModelIndex(), 0, 0)
            self.image_items.insert(0, {'id': image_main_id, 'title': title})
            self.filtered_image_items = self.image_items.copy()
            self.endInsertRows()
            self.new_image_main_id_signal.emit(image_main_id)

    def remove_image(self, index):
        image_id = self.image_items[index]['id']
        if self.database.delete_image_main(image_id):
            self.beginRemoveRows(QModelIndex(), index, index)
            del self.image_items[index]
            self.filtered_image_items = self.image_items.copy()
            self.endRemoveRows()
            self.remove_image_signal.emit(image_id)

    def update_image(self, index, new_title):
        image_id = self.image_items[index.row()]['id']
        if self.database.update_image_main(image_id, new_title):
            self.image_items[index.row()]['title'] = new_title
            self.filtered_image_items = self.image_items.copy()
            self.dataChanged.emit(index, index, [Qt.ItemDataRole.DisplayRole])

    def get_image(self, index):
        return self.filtered_image_items[index.row()]

    def get_index_by_image_main_id(self, image_id):
        for i, image_item in enumerate(self.filtered_image_items):
            if image_item['id'] == image_id:
                return i
        return None

    def filter_by_title(self, title):
        self.beginResetModel()
        if title and title.strip():
            self.filtered_image_items = [item for item in self.image_items if title.lower() in item['title'].lower()]
        else:
            self.filtered_image_items = self.image_items.copy()
        self.endResetModel()
