from PyQt5.QtWidgets import (
    QApplication, QWidget, QTextEdit, QColorDialog,
    QSystemTrayIcon, QMenu, QAction, QStyle
)
from PyQt5.QtCore import Qt, QRectF, QPoint
from PyQt5.QtGui import QPainter, QColor, QPen, QFont, QIcon
import sys

class FloatingReminder(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.bg_color = QColor(144, 238, 144, 200)
        self.border_color = QColor(0, 128, 0, 220)

        self.resize(180, 60)
        self.setMinimumSize(150, 40)

        self.text = QTextEdit(self)
        self.text.setText("小仓看着你哦！")
        self.text.setStyleSheet("""
            QTextEdit {
                background-color: transparent;
                border: none;
                color: black;
            }
        """)
        self.text.setFont(QFont("Arial", 16))
        self.text.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.text.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.text.setFrameStyle(0)
        self.text.setReadOnly(True)
        self.text.setGeometry(10, 10, self.width() - 20, self.height() - 20)

        self.resizing = False
        self.dragging = False
        self.drag_pos = None
        self.resize_margin = 15

        self.text.viewport().installEventFilter(self)
        self.init_tray()

    def init_tray(self):
        # 使用系统默认图标，避免打包后找不到图标文件
        default_icon = self.style().standardIcon(QStyle.SP_ComputerIcon)
        self.tray = QSystemTrayIcon(default_icon, self)
        self.tray.setToolTip("专注提醒")

        menu = QMenu()

        show_action = QAction("显示", self)
        show_action.triggered.connect(self.show)
        menu.addAction(show_action)

        hide_action = QAction("隐藏", self)
        hide_action.triggered.connect(self.hide)
        menu.addAction(hide_action)

        exit_action = QAction("退出", self)
        exit_action.triggered.connect(QApplication.instance().quit)
        menu.addAction(exit_action)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self.toggle_visibility)
        self.tray.show()

    def toggle_visibility(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self.setVisible(not self.isVisible())

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()
        painter.setBrush(self.bg_color)
        painter.setPen(QPen(self.border_color, 2))
        painter.drawRoundedRect(QRectF(rect), self.height() / 2, self.height() / 2)

    def resizeEvent(self, event):
        self.text.setGeometry(10, 10, self.width() - 20, self.height() - 20)

    def mousePressEvent(self, event):
        if event.button() in [Qt.LeftButton, Qt.MiddleButton]:
            if self.is_on_corner(event.pos()):
                self.resizing = True
            else:
                self.dragging = True
                self.drag_pos = event.globalPos() - self.frameGeometry().topLeft()
        elif event.button() == Qt.RightButton:
            color = QColorDialog.getColor(self.bg_color, self)
            if color.isValid():
                self.bg_color = QColor(color.red(), color.green(), color.blue(), 200)
                self.update()

    def mouseMoveEvent(self, event):
        if self.resizing:
            new_width = max(event.pos().x(), self.minimumWidth())
            new_height = max(event.pos().y(), self.minimumHeight())
            self.resize(new_width, new_height)
        elif self.dragging and self.drag_pos:
            self.move(event.globalPos() - self.drag_pos)
        else:
            if self.is_on_corner(event.pos()):
                self.setCursor(Qt.SizeFDiagCursor)
            else:
                self.setCursor(Qt.ArrowCursor)

    def mouseReleaseEvent(self, event):
        self.resizing = False
        self.dragging = False
        self.drag_pos = None

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MiddleButton:
            QApplication.instance().quit()

    def wheelEvent(self, event):
        delta = event.angleDelta().y() / 120
        font = self.text.font()
        size = max(8, min(48, font.pointSize() + delta))
        font.setPointSize(int(size))
        self.text.setFont(font)

    def is_on_corner(self, pos):
        return pos.x() >= self.width() - self.resize_margin and pos.y() >= self.height() - self.resize_margin

    def eventFilter(self, source, event):
        if source == self.text.viewport():
            if event.type() == event.MouseButtonPress:
                if event.button() == Qt.LeftButton:
                    self.text.setReadOnly(False)
                    self.text.setFocus()
        return super().eventFilter(source, event)

    def focusOutEvent(self, event):
        self.text.setReadOnly(True)
        super().focusOutEvent(event)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    reminder = FloatingReminder()
    reminder.show()
    sys.exit(app.exec_())
