from PyQt6.QtWidgets import QWidget


class MCPPresenter(QWidget):

    def __init__(self):
        super().__init__()
        self._mcp_main_id = None
        self._mcp_main_index = None
