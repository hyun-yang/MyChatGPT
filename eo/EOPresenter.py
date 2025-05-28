from PyQt6.QtWidgets import QWidget


class EOPresenter(QWidget):

    def __init__(self):
        super().__init__()
        self._eo_main_id = None
        self._eo_main_index = None
