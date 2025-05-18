import sys
import pyautogui
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QLabel
from PyQt5.QtGui import QCursor, QFont

# change to this 🤜
class DragLabel(QLabel):
    def __init__(self, parent):
        super().__init__("💠", parent)
        self.setFont(QFont("Arial", 25))
        self.setFixedSize(30, 30)
        self.setStyleSheet("""
            QLabel {
                color: white;
                background-color: transparent;
            }
        """)
        self.setAlignment(Qt.AlignCenter)
        self.setCursor(Qt.OpenHandCursor)
        self.parent_widget = parent
        self.dragging = False
        self.offset = QPoint()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.setCursor(Qt.ClosedHandCursor)
            self.setText("🔹")  # Change to closed fist
            self.dragging = True
            self.offset = event.globalPos() - self.parent_widget.pos()

    def mouseMoveEvent(self, event):
        if self.dragging:
            self.parent_widget.move(QCursor.pos() - self.offset)

    def mouseReleaseEvent(self, event):
        self.setCursor(Qt.OpenHandCursor)
        self.setText("💠")  # Back to open hand
        self.dragging = False


class OverlayButton(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setGeometry(100, 100, 60, 60)

        # Drag handle
        self.drag_label = DragLabel(self)

        # Main button (always above drag label)
        self.main_button = QPushButton("🔺", self)
        self.main_button.setFixedSize(60, 60)
        self.main_button.setFont(QFont("Arial", 32))  # <-- add this line to increase font size
        self.main_button.clicked.connect(self.toggle_buttons)
        self.main_button.raise_()  # Ensure it’s always above drag_label


        # Horizontal layout
        self.header_layout = QHBoxLayout()
        self.header_layout.setContentsMargins(0, 0, 0, 0)
        self.header_layout.addWidget(self.drag_label)
        self.header_layout.addWidget(self.main_button)

        # Vertical layout (with shortcuts)
        self.button_layout = QVBoxLayout(self)
        self.button_layout.setContentsMargins(0, 0, 0, 0)
        self.button_layout.addLayout(self.header_layout)

        # Shortcut buttons
        self.shortcut_buttons = []
        self.shortcuts = {
            "C": "copy",
            "V": "paste",
            "X": "cut",
            "D": "duplicate",
            "A": "select_all",
            "Z": "undo",
            "Y": "redo"
        }

        # Dark mode style
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

        # Apply to main button
        self.main_button.setStyleSheet(dark_button_style)

        # Apply to all shortcut buttons
        for key in self.shortcuts:
            btn = QPushButton(f"Ctrl+{key}")
            btn.setFixedSize(90, 50)
            btn.setStyleSheet(dark_button_style)  # <=== Apply style here
            btn.clicked.connect(lambda _, k=key: self.trigger_shortcut(k))
            btn.hide()
            self.shortcut_buttons.append(btn)
            self.button_layout.addWidget(btn)

    def toggle_buttons(self):
        is_visible = self.shortcut_buttons[0].isVisible()
        for btn in self.shortcut_buttons:
            btn.setVisible(not is_visible)

        if is_visible:
            self.main_button.setText("🔺")  # folded (closed)
        else:
            self.main_button.setText("🔻")  # unfolded (open)

    def trigger_shortcut(self, key):
        pyautogui.keyDown('alt')
        pyautogui.press('tab')
        pyautogui.keyUp('alt')
        pyautogui.sleep(0.1)
        pyautogui.hotkey('ctrl', key.lower())


if __name__ == "__main__":
    app = QApplication(sys.argv)
    overlay = OverlayButton()
    overlay.show()
    sys.exit(app.exec_())
