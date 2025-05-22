import sys
import os
import pyautogui
import win32gui
import win32con
from PyQt5.QtCore import Qt, QPoint, QRect
from PyQt5.QtWidgets import QSlider
import datetime
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtCore import QTimer
from notifypy import Notify
from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton, QVBoxLayout, 
                            QHBoxLayout, QLabel, QSizePolicy, QSizeGrip)
from PyQt5.QtGui import (QCursor, QFont, QPainter, QPen, QColor, QPixmap, 
                         QMouseEvent, QPaintEvent, QIcon)

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
        self.setWindowTitle("actionOverlay - Drawing Window")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.title_bar = QWidget(self)
        self.title_bar.setFixedHeight(30)
        self.title_bar.setStyleSheet("background-color: #333;")

        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(5, 0, 5, 0)

        self.title_label = QLabel("actionOverlay - Drawing Window")
        self.title_label.setStyleSheet("color: white;")
        title_layout.addWidget(self.title_label)

        title_layout.addStretch()

        self.bucket_button = QPushButton("🪣")
        self.bucket_button.setFixedSize(24, 24)
        self.bucket_button.setCheckable(True)
        self.bucket_button.setToolTip("Fill Bucket")
        self.bucket_button.setStyleSheet("""
            QPushButton {
                background-color: #eee;
                color: #222;
                border: 2px solid #222;
                border-radius: 4px;
                font-size: 16px;
            }
            QPushButton:checked {
                background-color: #fff;
                border: 2px solid #FFD600;
                color: #FFD600;
            }
        """)
        self.bucket_button.clicked.connect(self.set_bucket_mode)
        title_layout.addWidget(self.bucket_button)

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
                color: white;
                border: 1px solid #000;
                background-color: #ff0000;
                border-radius: 2px;
            }
            QPushButton:hover {
                background-color: #555;
                border-radius: 2px;
            }
        """)
        self.close_button.clicked.connect(self.close)

        self.clear_button = QPushButton("Clear")
        self.clear_button.setFixedSize(60, 20)
        self.clear_button.setStyleSheet("""
            QPushButton {
                color: white;
                border: 1px solid #000;
                background-color: #f47c36;
                border-radius: 2px;
            }
            QPushButton:hover {
                background-color: #555;
                border-radius: 2px;
            }
        """)
        self.clear_button.clicked.connect(self.clear_drawing)

        self.print_screen_button = QPushButton("⌜⌟ Print screen", self)
        self.print_screen_button.setFixedSize(90, 20)
        self.print_screen_button.setStyleSheet("""
            QPushButton {
                color: white;
                border: 1px solid #000;
                background-color: #2196F3;
                border-radius: 2px;
            }
            QPushButton:hover {
                background-color: #555;
                border-radius: 2px;
            }
        """)
        self.print_screen_button.setToolTip("Print Screen")
        self.print_screen_button.clicked.connect(self.take_screenshot)

        self.download_button = QPushButton("Download", self)
        self.download_button.setFixedSize(90, 20)
        self.download_button.setStyleSheet("""
            QPushButton {
                color: white;
                border: 1px solid #000;
                background-color: #4CAF50;
                border-radius: 2px;
            }
            QPushButton:hover {
                background-color: #555;
                border-radius: 2px;
            }
        """)
        self.download_button.setToolTip("Download the drawing as PNG")
        self.download_button.clicked.connect(self.save_as_png)

        title_layout.addWidget(self.print_screen_button)
        title_layout.addWidget(self.download_button)
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
        self.bucket_mode = False

    def save_as_png(self):
        if self.pixmap.isNull():
            return
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Drawing as PNG", "drawing.png", "PNG Files (*.png)")
        if file_path:
            from PyQt5.QtGui import QImage
            image = self.pixmap.toImage().convertToFormat(QImage.Format_ARGB32)
            image.save(file_path, "PNG")

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

    def set_bucket_mode(self):
        if self.bucket_button.isChecked():
            self.bucket_mode = True
        else:
            self.bucket_mode = False

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
                if self.bucket_mode:
                    self.bucket_fill(event.pos() - self.drawing_label.pos())
                else:
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

    def bucket_fill(self, pos):
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            x, y = int(pos.x()), int(pos.y())
            if x < 0 or y < 0 or x >= self.pixmap.width() or y >= self.pixmap.height():
                return

            image = self.pixmap.toImage()
            target_color = image.pixelColor(x, y)

            if self.eraser_mode:
                fill_color = QColor(0, 0, 0, 0)
            else:
                fill_color = self.pen.color()

            if target_color == fill_color:
                return

            self.perform_fill(image, x, y, target_color, fill_color)
            self.pixmap.convertFromImage(image)
            self.drawing_label.setPixmap(self.pixmap)
        finally:
            QApplication.restoreOverrideCursor()

    def perform_fill(self, image, x, y, target_color, fill_color):
        width = image.width()
        height = image.height()
        stack = [(x, y)]
        visited = set()

        while stack:
            cx, cy = stack.pop()
            if (cx, cy) in visited:
                continue
            if cx < 0 or cy < 0 or cx >= width or cy >= height:
                continue
            if image.pixelColor(cx, cy) != target_color:
                continue
            image.setPixelColor(cx, cy, fill_color)
            visited.add((cx, cy))
            stack.extend([
                (cx + 1, cy),
                (cx - 1, cy),
                (cx, cy + 1),
                (cx, cy - 1)
            ])


class ApplicationManager:
    @staticmethod
    def get_open_windows():
        windows = []

        def is_real_window(hwnd):
            if not win32gui.IsWindowVisible(hwnd):
                return False
            if win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE) & win32con.WS_EX_TOOLWINDOW:
                return False
            if win32gui.GetWindow(hwnd, win32con.GW_OWNER):
                return False
            title = win32gui.GetWindowText(hwnd)
            if not title.strip():
                return False

            if "Windows Input Experience" in title or "actionOverlay" in title:
                return False

            return True

        def callback(hwnd, extra):
            if is_real_window(hwnd):
                windows.append((hwnd, win32gui.GetWindowText(hwnd)))
            return True

        win32gui.EnumWindows(callback, None)
        return windows
    
    @staticmethod
    def bring_to_current_monitor(hwnd):
        window_rect = win32gui.GetWindowRect(hwnd)
        window_width = window_rect[2] - window_rect[0]
        window_height = window_rect[3] - window_rect[1]
        
        cursor_pos = QCursor.pos()
        screen = QApplication.screenAt(cursor_pos)
        
        if screen:
            screen_geometry = screen.geometry()
            x = screen_geometry.x() + (screen_geometry.width() - window_width) // 2
            y = screen_geometry.y() + (screen_geometry.height() - window_height) // 2

            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            win32gui.SetWindowPos(hwnd, win32con.HWND_TOP, x, y, window_width, window_height, win32con.SWP_SHOWWINDOW)
            win32gui.SetForegroundWindow(hwnd)
    
    @staticmethod
    def close_window(hwnd):
        win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)

class OverlayButton(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Window
        )
        self.setAttribute(Qt.WA_TranslucentBackground)

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
        self.shortcuts_layout.setAlignment(Qt.AlignTop)
        
        for key, name in self.shortcuts.items():
            btn = QPushButton(name, self)
            btn.setFixedSize(90, 50)
            btn.setStyleSheet(dark_button_style)
            btn.clicked.connect(lambda _, k=key: self.trigger_shortcut(k))
            btn.hide()
            self.shortcut_buttons.append(btn)
            self.shortcuts_layout.addWidget(btn)

        self.apps_button = QPushButton("apps", self)
        self.apps_button.setFixedSize(90, 50)
        self.apps_button.setStyleSheet(dark_button_style)
        self.apps_button.clicked.connect(self.toggle_apps_list)
        self.apps_button.setStyleSheet("""
            QPushButton {
                background-color: #1a1a1a;
                padding: 5px;
                color: #fff;
                border: 1px solid #0d0d0d;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #333333;
            }
            QPushButton:pressed {
                background-color: #595959;
            }
        """)
        self.apps_button.hide()
        self.shortcuts_layout.addWidget(self.apps_button)

        self.apps_list_layout = QVBoxLayout()
        self.apps_list_layout.setContentsMargins(0, 0, 0, 0)
        self.apps_list_layout.setSpacing(5)
        self.apps_list_layout.setAlignment(Qt.AlignTop)
        self.apps_list_widget = QWidget()
        self.apps_list_widget.setLayout(self.apps_list_layout)
        self.apps_list_widget.setFixedWidth(300)
        self.apps_list_widget.hide()

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
        
        main_button_container = QWidget()
        main_button_layout = QVBoxLayout(main_button_container)
        main_button_layout.setContentsMargins(0, 0, 0, 0)
        main_button_layout.addWidget(self.main_button, 0, Qt.AlignTop)
        main_button_layout.addStretch()

        main_layout.addWidget(main_button_container)
        main_layout.addLayout(self.shortcuts_layout)
        main_layout.addWidget(self.apps_list_widget)

        self._resize_timer = QTimer(self)
        self._resize_timer.timeout.connect(self.adjustSize)
        self._resize_timer.start(50)

    def take_screenshot(self):
        pyautogui.hotkey('win', 'shift', 's')

    def toggle_buttons(self):
        visible = self.shortcut_buttons[0].isVisible()
        for btn in self.shortcut_buttons:
            btn.setVisible(not visible)
        self.print_screen_button.setVisible(not visible)
        self.draw_button.setVisible(not visible)
        self.quit_button.setVisible(not visible)
        self.apps_button.setVisible(not visible)
        self.main_button.setText("○" if visible else "◌")
        
        if visible:
            self.apps_list_widget.hide()
        self.adjustSize()

    def toggle_apps_list(self):
        if self.apps_list_widget.isVisible():
            self.apps_list_widget.hide()
        else:
            self.populate_apps_list()
            self.apps_list_widget.show()
        self.adjustSize()

    def populate_apps_list(self):
        for i in reversed(range(self.apps_list_layout.count())): 
            widget = self.apps_list_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
            else:
                layout = self.apps_list_layout.itemAt(i).layout()
                if layout:
                    for j in reversed(range(layout.count())):
                        layout.itemAt(j).widget().setParent(None)
                    self.apps_list_layout.removeItem(layout)
        
        windows = ApplicationManager.get_open_windows()
        
        for hwnd, title in windows[:15]:
            window_layout = QHBoxLayout()
            window_layout.setSpacing(5)
            
            short_title = title[:30] + "..." if len(title) > 30 else title
            label = QLabel(short_title)
            label.setStyleSheet("""
                background-color: #222;
                border-radius: 8px;
                padding: 2px 6px;
                border: 1px solid #444;
                color: white;
            """)
            label.setFixedSize(180, 50)
            window_layout.addWidget(label)
            
            bring_btn = QPushButton("⇲")
            bring_btn.setFixedSize(50, 50)
            bring_btn.setStyleSheet("""
                QPushButton {
                    background-color: #286;
                    color: white;
                    border: none;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: #3a8;
                }
            """)
            bring_btn.clicked.connect(lambda _, h=hwnd: (ApplicationManager.bring_to_current_monitor(h), self.toggle_apps_list()))
            window_layout.addWidget(bring_btn)
            
            close_btn = QPushButton("✕")
            close_btn.setFixedSize(50, 50)
            close_btn.setStyleSheet("""
                QPushButton {
                    background-color: #922;
                    color: white;
                    border: none;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: #b33;
                }
            """)
            def bring_and_close(h):
                ApplicationManager.bring_to_current_monitor(h)
                QTimer.singleShot(300, lambda: ApplicationManager.close_window(h))
                self.toggle_apps_list()
            close_btn.clicked.connect(lambda _, h=hwnd: bring_and_close(h))
            window_layout.addWidget(close_btn)
            
            self.apps_list_layout.addLayout(window_layout)
        self.adjustSize()

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