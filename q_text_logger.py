#!/usr/bin/env python3

from logging import Handler
from PySide6.QtCore import QObject, Signal

class QTextLogger(Handler):

    class Sender(QObject):
        sendEntry = Signal(str)
        def __init__(self, target):
            super().__init__()
            self.sendEntry.connect(target.appendPlainText)

    def __init__(self, widget):
        super().__init__()

        self.widget = widget
        self.sender = QTextLogger.Sender(widget)
        self.widget.setReadOnly(True)

    def emit(self, record):
        self.sender.sendEntry.emit(self.format(record))
