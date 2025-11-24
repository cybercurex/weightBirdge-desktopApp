# ui/components/styled_components.py
from PyQt5.QtWidgets import (QPushButton, QTableWidget, QTableWidgetItem, 
                            QHeaderView, QLabel, QTextEdit, QFrame)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QColor, QPainter, QPainterPath

class RoundedButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setMinimumHeight(30)
        self.setCursor(Qt.PointingHandCursor)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw background
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 8, 8)
        
        if self.isEnabled():
            if self.underMouse():
                painter.fillPath(path, QColor(70, 130, 180))  # Hover color
            else:
                painter.fillPath(path, QColor(100, 149, 237))  # Normal color
        else:
            painter.fillPath(path, QColor(200, 200, 200))  # Disabled color

        # Draw text
        painter.setPen(Qt.white)
        painter.drawText(self.rect(), Qt.AlignCenter, self.text())

class StatusIndicator(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(12, 12)
        self.set_status(False)

    def set_status(self, is_running):
        self.is_running = is_running
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        
        if self.is_running:
            painter.setBrush(QColor(40, 180, 99))  # Green
        else:
            painter.setBrush(QColor(220, 53, 69))  # Red
            
        painter.drawEllipse(0, 0, self.width(), self.height())

class LogPanel(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setStyleSheet("""
            QTextEdit {
                background-color: #2b2b2b;
                color: #e0e0e0;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                padding: 8px;
                font-family: 'Consolas', 'Monospace';
            }
        """)