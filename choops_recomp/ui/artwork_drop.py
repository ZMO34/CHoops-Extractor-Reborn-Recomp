"""Single local artwork file picker and drop target."""
from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QLabel


class ArtworkDrop(QLabel):
    dropped = Signal(str)
    suffixes = {'.dds', '.png', '.jpg', '.jpeg', '.tga', '.bmp'}

    def __init__(self, text, parent=None, suffixes=None):
        super().__init__(text, parent)
        self.setAcceptDrops(True)
        self.allowed = self.suffixes if suffixes is None else suffixes

    def file(self, event):
        urls = event.mimeData().urls()
        if len(urls) == 1 and urls[0].isLocalFile():
            path = Path(urls[0].toLocalFile())
            if path.suffix.casefold() in self.allowed and path.is_file():
                return str(path)
        return None

    def dragEnterEvent(self, event):
        if self.file(event):
            event.acceptProposedAction()

    def dropEvent(self, event):
        path = self.file(event)
        if path:
            event.acceptProposedAction()
            self.dropped.emit(path)
