import sys
import pyautogui
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QLabel
from PyQt5.QtGui import QCursor, QFont

class DraggableButton(QPushButton):
    def __init__(self, text, parent):
        super().__init__(text, parent)
        self.setFixedSize(60, 60)
        font = QFont("Arial", 32)
        font.setStyleStrategy(QFont.PreferAntialias)
        self.setFont(font)
        self.setStyleSheet("""
            QPushButton {
                background-color: #2c2c2c;
                padding: 0px;
                color: #ffffff;
                border: 1px solid #444;
                border-radius: 10px;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #3a3a3a;
            }
            QPushButton:pressed {
                background-color: #1e1e1e;
            }
        """)
        self.dragging = False
        self.offset = QPoint()
        self.was_dragging = False

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.was_dragging = False
            self.offset = event.globalPos() - self.window().pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.dragging:
            self.window().move(QCursor.pos() - self.offset)
            self.was_dragging = True  # mark it as a drag
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.dragging = False
        super().mouseReleaseEvent(event)



class OverlayButton(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setGeometry(100, 100, 200, 300)  # Height for vertical buttons

        self.main_button = DraggableButton("○", self)
        self.main_button.setFixedSize(60, 60)
        font = QFont("Arial", 32)
        font.setStyleStrategy(QFont.PreferAntialias)
        self.main_button.setFont(font)
        self.main_button.setStyleSheet("""
            QPushButton {
                background-color: #2c2c2c;
                padding: 0px;
                color: #ffffff;
                border: 1px solid #444;
                border-radius: 10px;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #3a3a3a;
            }
            QPushButton:pressed {
                background-color: #1e1e1e;
            }
        """)
        self.main_button.clicked.connect(self.on_main_button_clicked)
        self.main_button.raise_()

        self.shortcut_buttons = []
        self.shortcuts = {
            "C": "copy",
            "V": "paste",
            "X": "cut",
            "D": "duplicate",
            "A": "select all",
            "Z": "↶ undo",
            "Y": "redo ↷"
        }

        dark_button_style = """
        QPushButton {
            background-color: #2c2c2c;
            padding: 5px;
            color: #ffffff;
            border: 1px solid #444;
            border-radius: 10px;
        }

        QPushButton:hover {
            background-color: #3a3a3a;
        }

        QPushButton:pressed {
            background-color: #1e1e1e;
        }
        """

        self.main_button.setStyleSheet(dark_button_style)

        # Main horizontal layout: drag/main on the left, shortcuts on the right
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        # Vertical layout for drag + main button
        control_layout = QHBoxLayout()
        control_layout.setSpacing(0)
        control_layout.setContentsMargins(0, 0, 0, 0)
        control_layout.addWidget(self.main_button)
        control_layout.addStretch()
        main_layout.addLayout(control_layout)

        # Vertical layout for shortcut buttons (right of main button)
        self.shortcuts_layout = QVBoxLayout()
        self.shortcuts_layout.setContentsMargins(0, 0, 0, 0)
        self.shortcuts_layout.setSpacing(5)

        # Center the shortcut buttons vertically relative to the main button
        self.shortcuts_layout.addStretch()
        for key, action_name in self.shortcuts.items():
            btn = QPushButton(action_name, self)
            btn.setFixedSize(90, 50)
            btn.setStyleSheet(dark_button_style)
            btn.clicked.connect(lambda _, k=key: self.trigger_shortcut(k))
            btn.hide()
            self.shortcut_buttons.append(btn)
            self.shortcuts_layout.addWidget(btn)
        self.shortcuts_layout.addStretch()

        self.quit_button = QPushButton("✖ quit", self)
        self.quit_button.setFixedSize(90, 50)
        self.quit_button.setStyleSheet("""
            QPushButton {
                background-color: #922;
                padding: 5px;
                color: #fff;
                border: 1px solid #600;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #b33;
            }
            QPushButton:pressed {
                background-color: #811;
            }
        """)
        self.quit_button.clicked.connect(QApplication.quit)
        self.quit_button.hide()
        self.shortcuts_layout.addWidget(self.quit_button)

        main_layout.addLayout(self.shortcuts_layout)

    def toggle_buttons(self):
        is_visible = self.shortcut_buttons[0].isVisible()
        for btn in self.shortcut_buttons:
            btn.setVisible(not is_visible)

        self.quit_button.setVisible(not is_visible)
        self.main_button.setText("○" if is_visible else "◌")

    def trigger_shortcut(self, key):
        pyautogui.keyDown('alt')
        pyautogui.press('tab')
        pyautogui.keyUp('alt')
        pyautogui.sleep(0.1)
        pyautogui.hotkey('ctrl', key.lower())

    def on_main_button_clicked(self):
        if not self.main_button.was_dragging:
            self.toggle_buttons()




if __name__ == "__main__":
    app = QApplication(sys.argv)
    overlay = OverlayButton()
    overlay.show()
    sys.exit(app.exec_())
