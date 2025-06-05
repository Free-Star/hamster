from PyQt5.QtWidgets import (
    QApplication, QWidget, QTextEdit,
    QSystemTrayIcon, QMenu, QAction, QStyle, QDialog,
    QComboBox, QDialogButtonBox, QFormLayout, QKeySequenceEdit, QShortcut
)
from PyQt5.QtCore import Qt, QRectF, QKeySequence
from PyQt5.QtGui import QPainter, QColor, QPen, QFont, QIcon

PRESETS = {
    "简约风": {
        "bg": QColor(245, 245, 245, 200),
        "border": QColor(200, 200, 200, 220),
        "text": QColor(0, 0, 0),
        "font": ("Arial", 16),
    },
    "科技风": {
        "bg": QColor(30, 30, 30, 220),
        "border": QColor(0, 255, 255, 180),
        "text": QColor(0, 255, 255),
        "font": ("Consolas", 16),
    },
    "暖色风": {
        "bg": QColor(255, 228, 196, 200),
        "border": QColor(255, 140, 0, 220),
        "text": QColor(90, 50, 0),
        "font": ("Verdana", 16),
    },
    "海洋风": {
        "bg": QColor(173, 216, 230, 200),
        "border": QColor(70, 130, 180, 220),
        "text": QColor(0, 0, 80),
        "font": ("Tahoma", 16),
    },
    "复古风": {
        "bg": QColor(250, 235, 215, 200),
        "border": QColor(139, 69, 19, 220),
        "text": QColor(84, 47, 0),
        "font": ("Times New Roman", 16),
    },
}

import sys

class SettingsDialog(QDialog):
    def __init__(self, current_hotkey, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")

        layout = QFormLayout()

        self.preset_combo = QComboBox()
        self.preset_combo.addItems(list(PRESETS.keys()))
        layout.addRow("风格预设:", self.preset_combo)

        self.hotkey_edit = QKeySequenceEdit(QKeySequence(current_hotkey))
        layout.addRow("显示/隐藏快捷键:", self.hotkey_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

        self.setLayout(layout)

    def get_settings(self):
        return (
            self.preset_combo.currentText(),
            self.hotkey_edit.keySequence().toString(),
        )

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
        self.text_color = QColor(0, 0, 0)
        self.hotkey = "Ctrl+Shift+H"

        self.resize(180, 60)
        self.setMinimumSize(150, 40)

        self.font_family = "Arial"
        self.font_size = 16

        self.text = QTextEdit(self)
        self.text.setText("小仓看着你哦！")
        self.apply_preset("简约风")
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
        self.init_shortcut()

    def init_tray(self):
        self.tray = QSystemTrayIcon(QIcon("hamster.ico"), self)
        self.tray.setToolTip("专注提醒")

        menu = QMenu()

        show_action = QAction("显示", self)
        show_action.triggered.connect(self.show)
        menu.addAction(show_action)

        hide_action = QAction("隐藏", self)
        hide_action.triggered.connect(self.hide)
        menu.addAction(hide_action)

        settings_action = QAction("设置", self)
        settings_action.triggered.connect(self.open_settings)
        menu.addAction(settings_action)

        exit_action = QAction("退出", self)
        exit_action.triggered.connect(QApplication.instance().quit)
        menu.addAction(exit_action)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self.toggle_visibility)
        self.tray.show()

    def init_shortcut(self):
        self.shortcut = QShortcut(QKeySequence(self.hotkey), self)
        self.shortcut.activated.connect(lambda: self.toggle_visibility(None))

    def open_settings(self):
        dialog = SettingsDialog(self.hotkey, self)
        if dialog.exec_():
            preset, hotkey = dialog.get_settings()
            self.apply_preset(preset)
            if hotkey:
                self.hotkey = hotkey
                self.shortcut.setKey(QKeySequence(self.hotkey))

    def toggle_visibility(self, reason):
        if reason is None or reason == QSystemTrayIcon.Trigger:
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
            self.open_settings()

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
        self.font_size = max(8, min(48, self.font_size + delta))
        self.update_text_style()

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

    def apply_preset(self, name):
        preset = PRESETS.get(name)
        if not preset:
            return
        self.bg_color = preset["bg"]
        self.border_color = preset["border"]
        self.text_color = preset["text"]
        self.font_family, self.font_size = preset["font"]
        self.update_text_style()
        self.update()

    def update_text_style(self):
        self.text.setStyleSheet(
            f"QTextEdit {{background-color: transparent; border: none; color: {self.text_color.name()};}}"
        )
        self.text.setFont(QFont(self.font_family, int(self.font_size)))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    reminder = FloatingReminder()
    reminder.show()
    sys.exit(app.exec_())
