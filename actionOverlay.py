import sys
import pyautogui
from PyQt5.QtCore import Qt, QPoint, QRect
from PyQt5.QtWidgets import QSlider
import datetime
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton, QVBoxLayout, 
                            QHBoxLayout, QLabel, QSizePolicy)
from PyQt5.QtGui import (QCursor, QFont, QPainter, QPen, QColor, QPixmap, 
                         QMouseEvent, QPaintEvent)

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
            self.was_dragging = True
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.dragging = False
        super().mouseReleaseEvent(event)

class DrawingWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Drawing Window")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.title_bar = QWidget(self)
        self.title_bar.setFixedHeight(30)
        self.title_bar.setStyleSheet("background-color: #333;")

        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(5, 0, 5, 0)

        self.title_label = QLabel("Drawing Window")
        self.title_label.setStyleSheet("color: white;")
        title_layout.addWidget(self.title_label)

        title_layout.addStretch()

        self.eraser_button = QPushButton("⎚")
        self.eraser_button.setFixedSize(24, 24)
        self.eraser_button.setCheckable(True)
        self.eraser_button.setToolTip("Eraser")
        self.eraser_button.setStyleSheet("""
            QPushButton {
                background-color: #eee;
                color: #222;
                border: 2px solid #222;
                border-radius: 4px;
                font-size: 16px;
            }
            QPushButton:checked {
                background-color: #fff;
                border: 2px solid #2196F3;
                color: #2196F3;
            }
        """)
        self.eraser_button.clicked.connect(self.set_eraser_mode)
        title_layout.addWidget(self.eraser_button)

        self.color_buttons = []
        color_defs = [
            ("#FFD600", "yellow"),
            ("#000000", "black"),
            ("#FFFFFF", "white"),
            ("#888888", "gray"),
            ("#2196F3", "blue"),
            ("#F44336", "red"),
            ("#E91E63", "pink"),
            ("#9C27B0", "purple"),
            ("#4CAF50", "green"),
            ("#00BCD4", "cyan"),
        ]
        self.pen = QPen(QColor(255, 255, 255), 3, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)

        def make_color_btn(color, tooltip):
            btn = QPushButton()
            btn.setFixedSize(22, 22)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    border: 2px solid #222;
                    border-radius: 4px;
                }}
                QPushButton:checked {{
                    border: 2px solid #fff;
                }}
            """)
            btn.setToolTip(tooltip)
            btn.setCheckable(True)
            btn.clicked.connect(lambda _, c=color: self.set_pen_color(c))
            return btn

        self.color_btn_group = []
        for color, name in color_defs:
            btn = make_color_btn(color, name)
            self.color_buttons.append(btn)
            title_layout.addWidget(btn)
            self.color_btn_group.append(btn)
        self.color_btn_group[2].setChecked(True)

        self.thickness_slider = QSlider(Qt.Horizontal)
        self.thickness_slider.setMinimum(1)
        self.thickness_slider.setMaximum(20)
        self.thickness_slider.setValue(3)
        self.thickness_slider.setFixedWidth(80)
        self.thickness_slider.setToolTip("Pen thickness")
        self.thickness_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #444;
                height: 6px;
                background: #222;
                margin: 0px;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #fff;
                border: 1px solid #2196F3;
                width: 14px;
                margin: -4px 0;
                border-radius: 7px;
            }
        """)
        self.thickness_slider.valueChanged.connect(self.set_pen_thickness)
        title_layout.addWidget(self.thickness_slider)

        title_layout.addStretch()

        self.close_button = QPushButton("✕")
        self.close_button.setFixedSize(20, 20)
        self.close_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: white;
                border: none;
            }
            QPushButton:hover {
                background-color: #555;
                border-radius: 2px;
            }
        """)
        self.close_button.clicked.connect(self.close)

        self.clear_button = QPushButton("clear")
        self.clear_button.setFixedSize(30, 20)
        self.clear_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: white;
                border: none;
            }
            QPushButton:hover {
                background-color: #555;
                border-radius: 2px;
            }
        """)
        self.clear_button.clicked.connect(self.clear_drawing)
        self.print_screen_button = QPushButton("⎙", self)
        self.print_screen_button.setFixedSize(30, 20)
        self.print_screen_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: white;
                border: none;
            }
            QPushButton:hover {
                background-color: #555;
                border-radius: 2px;
            }
        """)
        self.print_screen_button.setToolTip("Print Screen")
        self.print_screen_button.clicked.connect(self.take_screenshot)
        title_layout.addWidget(self.print_screen_button)
        title_layout.addWidget(self.clear_button)
        title_layout.addWidget(self.close_button)
        layout.addWidget(self.title_bar)

        self.drawing_label = QLabel(self)
        self.drawing_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.drawing_label.setStyleSheet("background-color: rgba(30, 30, 30, 20);")
        layout.addWidget(self.drawing_label)

        self.pixmap = QPixmap(1, 1)
        self.pixmap.fill(Qt.transparent)
        self.last_point = None

        self.dragging = False
        self.offset = QPoint()

        self.drawing_label.showEvent = self.update_drawing_surface

        self.showEvent = self.set_available_geometry_on_show

        self.eraser_mode = False

    def take_screenshot(self):
        pyautogui.hotkey('win', 'shift', 's')

    def set_eraser_mode(self):
        if self.eraser_button.isChecked():
            self.eraser_mode = True
            for btn in self.color_btn_group:
                btn.setChecked(False)
            self.pen.setColor(Qt.transparent)
            self.pen.setWidth(self.thickness_slider.value())
        else:
            self.eraser_mode = False
            checked = [btn for btn in self.color_btn_group if btn.isChecked()]
            if checked:
                idx = self.color_btn_group.index(checked[0])
                color = self.color_buttons[idx].palette().button().color()
                self.pen.setColor(color)
            else:
                self.pen.setColor(QColor("#FFFFFF"))
            self.pen.setWidth(self.thickness_slider.value())

    def set_pen_color(self, color):
        self.eraser_button.setChecked(False)
        self.eraser_mode = False
        for btn in self.color_btn_group:
            btn.setChecked(False)
        sender = self.sender()
        if sender:
            sender.setChecked(True)
        self.pen.setColor(QColor(color))
        self.pen.setWidth(self.thickness_slider.value())

    def set_pen_thickness(self, value):
        self.pen.setWidth(value)

    def set_pen_color(self, color):
        for btn in self.color_btn_group:
            btn.setChecked(False)
        sender = self.sender()
        if sender:
            sender.setChecked(True)
        self.pen.setColor(QColor(color))

    def set_available_geometry_on_show(self, event):
        cursor_pos = QCursor.pos()
        screen = QApplication.screenAt(cursor_pos)
        if screen:
            geometry = screen.availableGeometry()
            self.setGeometry(geometry)
        event.accept()

    def set_fullscreen_on_show(self, event):
        cursor_pos = QCursor.pos()
        screen = QApplication.screenAt(cursor_pos)
        if screen:
            geometry = screen.geometry()
            self.setGeometry(geometry)
        event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.dragging:
            self.dragging = False
            center = self.geometry().center()
            screen = QApplication.screenAt(center)
            if screen:
                geometry = screen.geometry()
                self.setGeometry(geometry)
            self.last_point = None
        else:
            self.last_point = None
        super().mouseReleaseEvent(event)
    
    def update_drawing_surface(self, event):
        if self.pixmap.size() != self.drawing_label.size():
            new_pixmap = QPixmap(self.drawing_label.size())
            new_pixmap.fill(Qt.transparent)
            
            if not self.pixmap.isNull():
                painter = QPainter(new_pixmap)
                painter.drawPixmap(0, 0, self.pixmap)
                painter.end()
            
            self.pixmap = new_pixmap
            self.drawing_label.setPixmap(self.pixmap)
        
        event.accept()
        
    def resizeEvent(self, event):
        self.update_drawing_surface(event)
        super().resizeEvent(event)
    
    def draw_line(self, from_point, to_point):
        if self.pixmap.isNull():
            return
            
        painter = QPainter(self.pixmap)
        if painter.isActive():
            if self.eraser_mode:
                painter.setCompositionMode(QPainter.CompositionMode_Clear)
                eraser_pen = QPen(Qt.transparent, self.thickness_slider.value(), Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
                painter.setPen(eraser_pen)
            else:
                painter.setPen(self.pen)
            painter.drawLine(from_point, to_point)
            painter.end()
            self.drawing_label.setPixmap(self.pixmap)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.title_bar.underMouse():
                self.dragging = True
                self.offset = event.pos()
            elif self.drawing_label.underMouse():
                self.last_point = event.pos() - self.drawing_label.pos()
    
    def mouseMoveEvent(self, event):
        if self.dragging:
            self.move(event.globalPos() - self.offset)
        elif self.last_point is not None and event.buttons() & Qt.LeftButton:
            current_point = event.pos() - self.drawing_label.pos()
            self.draw_line(self.last_point, current_point)
            self.last_point = current_point
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False
            self.last_point = None
    
    def clear_drawing(self):
        if not self.pixmap.isNull():
            self.pixmap.fill(Qt.transparent)
            self.drawing_label.setPixmap(self.pixmap)

class OverlayButton(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Window
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setGeometry(100, 100, 200, 300)

        self.drawing_window = None

        self.main_button = DraggableButton("○", self)
        self.main_button.clicked.connect(self.on_main_button_clicked)

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

        self.shortcuts = {
            "C": "copy",
            "V": "paste",
            "X": "cut",
            "D": "duplicate",
            "A": "select all",
            "Z": "undo",
            "Y": "redo"
        }

        self.shortcut_buttons = []
        self.shortcuts_layout = QVBoxLayout()
        self.shortcuts_layout.setContentsMargins(0, 0, 0, 0)
        self.shortcuts_layout.setSpacing(5)

        for key, name in self.shortcuts.items():
            btn = QPushButton(name, self)
            btn.setFixedSize(90, 50)
            btn.setStyleSheet(dark_button_style)
            btn.clicked.connect(lambda _, k=key: self.trigger_shortcut(k))
            btn.hide()
            self.shortcut_buttons.append(btn)
            self.shortcuts_layout.addWidget(btn)

        self.print_screen_button = QPushButton("⎙ print screen", self)
        self.print_screen_button.setFixedSize(90, 50)
        self.print_screen_button.setStyleSheet("""
            QPushButton {
                background-color: #286;
                padding: 5px;
                color: #fff;
                border: 1px solid #063;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #3a8;
            }
            QPushButton:pressed {
                background-color: #174;
            }
        """)
        self.print_screen_button.clicked.connect(self.take_screenshot)
        self.print_screen_button.hide()
        self.shortcuts_layout.addWidget(self.print_screen_button)

        self.draw_button = QPushButton("✎ draw", self)
        self.draw_button.setFixedSize(90, 50)
        self.draw_button.setStyleSheet("""
            QPushButton {
                background-color: #228;
                padding: 5px;
                color: #fff;
                border: 1px solid #006;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #33a;
            }
            QPushButton:pressed {
                background-color: #116;
            }
        """)
        self.draw_button.clicked.connect(self.toggle_drawing_window)
        self.draw_button.hide()
        self.shortcuts_layout.addWidget(self.draw_button)

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

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        control_layout = QHBoxLayout()
        control_layout.setSpacing(0)
        control_layout.setContentsMargins(0, 0, 0, 0)
        control_layout.addWidget(self.main_button)
        control_layout.addStretch()

        main_layout.addLayout(control_layout)
        main_layout.addLayout(self.shortcuts_layout)

    def take_screenshot(self):
        pyautogui.hotkey('win', 'shift', 's')

    def toggle_buttons(self):
        visible = self.shortcut_buttons[0].isVisible()
        for btn in self.shortcut_buttons:
            btn.setVisible(not visible)
        self.print_screen_button.setVisible(not visible)
        self.draw_button.setVisible(not visible)
        self.quit_button.setVisible(not visible)
        self.main_button.setText("○" if visible else "◌")

    def trigger_shortcut(self, key):
        pyautogui.keyDown('alt')
        pyautogui.press('tab')
        pyautogui.keyUp('alt')
        pyautogui.sleep(0.1)
        pyautogui.hotkey('ctrl', key.lower())

    def on_main_button_clicked(self):
        if not self.main_button.was_dragging:
            self.toggle_buttons()

    def toggle_drawing_window(self):
        if self.drawing_window is None or not self.drawing_window.isVisible():
            self.drawing_window = DrawingWindow()
            
            cursor_pos = QCursor.pos()
            screen = QApplication.screenAt(cursor_pos)
            if screen:
                screen_geometry = screen.availableGeometry()
                window_width = min(800, screen_geometry.width() - 100)
                window_height = min(600, screen_geometry.height() - 100)
                x = screen_geometry.x() + (screen_geometry.width() - window_width) // 2
                y = screen_geometry.y() + (screen_geometry.height() - window_height) // 2
                self.drawing_window.setGeometry(x, y, window_width, window_height)
            
            self.drawing_window.show()
            self.draw_button.setStyleSheet("""
                QPushButton {
                    background-color: #44a;
                    padding: 5px;
                    color: #fff;
                    border: 1px solid #006;
                    border-radius: 10px;
                }
                QPushButton:hover {
                    background-color: #55b;
                }
                QPushButton:pressed {
                    background-color: #338;
                }
            """)
        else:
            self.drawing_window.close()
            self.draw_button.setStyleSheet("""
                QPushButton {
                    background-color: #228;
                    padding: 5px;
                    color: #fff;
                    border: 1px solid #006;
                    border-radius: 10px;
                }
                QPushButton:hover {
                    background-color: #33a;
                }
                QPushButton:pressed {
                    background-color: #116;
                }
            """)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    overlay = OverlayButton()
    overlay.show()
    sys.exit(app.exec_())