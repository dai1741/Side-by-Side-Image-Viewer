import sys
import os
import glob
import re
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QFileDialog, QSplitter,
                             QToolButton, QMenu, QSizePolicy, QComboBox, QSpinBox, QLineEdit)
from PyQt6.QtGui import QAction, QActionGroup, QFontMetrics
from PyQt6.QtCore import Qt, QSettings
from components.image_panel import ImagePanel

# Supported extensions
IMG_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.webp', '.tif', '.tiff'}

class FocusClearLineEdit(QLineEdit):
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.clearFocus()
        else:
            super().keyPressEvent(event)

class FocusClearSpinBox(QSpinBox):
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.clearFocus()
        else:
            super().keyPressEvent(event)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Side-by-Side Image Comparison Viewer")
        self.resize(1600, 900)
        self.setStyleSheet("background-color: #121212; color: #ffffff;")

        # Settings
        self.settings = QSettings("Antigravity", "ImageComparisonViewer")
        self.recent_folders = self.settings.value("recent_folders", [])
        if not isinstance(self.recent_folders, list):
            self.recent_folders = []

        # State
        self.folder_a = None
        self.folder_b = None
        self.all_files_a = [] # Complete list
        self.all_files_b = [] # Complete list
        self.files_a = [] # Filtered list
        self.files_b = [] # Filtered list
        self.current_index_a = 0
        self.current_index_b = 0

        # UI Components
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Top Control Bar
        control_bar = QHBoxLayout()
        
        # Left Controls
        left_layout = QVBoxLayout()
        left_layout.setSpacing(2)
        
        # Row 1: Load + Filter
        left_row1 = QHBoxLayout()
        self.btn_load_a = QToolButton()
        self.btn_load_a.setText("Load Left")
        self.btn_load_a.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)
        self.update_recent_menu(self.btn_load_a, 'A')
        self.btn_load_a.clicked.connect(lambda: self.select_folder('A'))
        self.btn_load_a.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btn_load_a.setStyleSheet("background-color: #333; padding: 5px; border-radius: 4px; color: white;")
        
        self.txt_filter_a = FocusClearLineEdit()
        self.txt_filter_a.setPlaceholderText("Filter (Regex)...")
        self.txt_filter_a.setStyleSheet("background-color: #222; color: #ddd; border: 1px solid #444; border-radius: 3px; padding: 2px;")
        self.txt_filter_a.setFixedWidth(150) 
        self.txt_filter_a.textChanged.connect(lambda: self.apply_filter('A'))

        left_row1.addWidget(self.btn_load_a)
        left_row1.addWidget(self.txt_filter_a)

        self.lbl_filename_a = QLabel("")
        self.lbl_filename_a.setStyleSheet("color: #aaa; font-size: 11px;")
        self.lbl_filename_a.setFixedWidth(250) 
        self.lbl_filename_a.setAlignment(Qt.AlignmentFlag.AlignCenter)

        left_layout.addLayout(left_row1)
        left_layout.addWidget(self.lbl_filename_a)
        
        # Middle Controls
        middle_layout = QHBoxLayout()
        
        # Interpolation
        self.combo_interp = QComboBox()
        self.combo_interp.addItems(["Nearest", "Bilinear"])
        self.combo_interp.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.combo_interp.setStyleSheet("background-color: #333; color: white; padding: 5px;")
        self.combo_interp.currentTextChanged.connect(self.change_interpolation)
        
        # L Index
        lbl_l = QLabel("L:")
        lbl_l.setStyleSheet("font-weight: bold; color: #bbb;")
        self.spin_index_a = FocusClearSpinBox()
        self.spin_index_a.setRange(1, 1)
        self.spin_index_a.setFixedWidth(70)
        self.spin_index_a.setStyleSheet("background-color: #333; color: white; padding: 5px;")
        self.spin_index_a.valueChanged.connect(lambda: self.jump_to_index('A'))
        self.lbl_total_a = QLabel("/ 0")
        self.lbl_total_a.setFixedWidth(50)

        # R Index
        lbl_r = QLabel("R:")
        lbl_r.setStyleSheet("font-weight: bold; color: #bbb; margin-left: 10px;")
        self.spin_index_b = FocusClearSpinBox()
        self.spin_index_b.setRange(1, 1)
        self.spin_index_b.setFixedWidth(70)
        self.spin_index_b.setStyleSheet("background-color: #333; color: white; padding: 5px;")
        self.spin_index_b.valueChanged.connect(lambda: self.jump_to_index('B'))
        self.lbl_total_b = QLabel("/ 0")
        self.lbl_total_b.setFixedWidth(50)

        middle_layout.addWidget(self.combo_interp)
        middle_layout.addSpacing(20)
        middle_layout.addWidget(lbl_l)
        middle_layout.addWidget(self.spin_index_a)
        middle_layout.addWidget(self.lbl_total_a)
        middle_layout.addWidget(lbl_r)
        middle_layout.addWidget(self.spin_index_b)
        middle_layout.addWidget(self.lbl_total_b)

        # Right Controls
        right_layout = QVBoxLayout()
        right_layout.setSpacing(2)
        
        # Row 1: Load + Filter
        right_row1 = QHBoxLayout()
        self.btn_load_b = QToolButton()
        self.btn_load_b.setText("Load Right")
        self.btn_load_b.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)
        self.update_recent_menu(self.btn_load_b, 'B')
        self.btn_load_b.clicked.connect(lambda: self.select_folder('B'))
        self.btn_load_b.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btn_load_b.setStyleSheet("background-color: #333; padding: 5px; border-radius: 4px; color: white;")

        self.txt_filter_b = FocusClearLineEdit()
        self.txt_filter_b.setPlaceholderText("Filter (Regex)...")
        self.txt_filter_b.setStyleSheet("background-color: #222; color: #ddd; border: 1px solid #444; border-radius: 3px; padding: 2px;")
        self.txt_filter_b.setFixedWidth(150)
        self.txt_filter_b.textChanged.connect(lambda: self.apply_filter('B'))

        right_row1.addWidget(self.btn_load_b)
        right_row1.addWidget(self.txt_filter_b)

        self.lbl_filename_b = QLabel("")
        self.lbl_filename_b.setStyleSheet("color: #aaa; font-size: 11px;")
        self.lbl_filename_b.setFixedWidth(250)
        self.lbl_filename_b.setAlignment(Qt.AlignmentFlag.AlignCenter)

        right_layout.addLayout(right_row1)
        right_layout.addWidget(self.lbl_filename_b)

        # Add to Main Control Bar
        control_bar.addLayout(left_layout)
        control_bar.addStretch()
        control_bar.addLayout(middle_layout)
        control_bar.addStretch()
        control_bar.addLayout(right_layout)

        main_layout.addLayout(control_bar)

        # Image Area
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.panel_a = ImagePanel()
        self.panel_b = ImagePanel()
        self.panel_a.pixel_info_changed.connect(lambda info: self.lbl_info_a.setText(info))
        self.panel_b.pixel_info_changed.connect(lambda info: self.lbl_info_b.setText(info))

        self.splitter.addWidget(self.panel_a)
        self.splitter.addWidget(self.panel_b)
        self.splitter.setSizes([800, 800])
        
        main_layout.addWidget(self.splitter, stretch=1)

        # Info Bar (Pixel Info)
        info_layout = QHBoxLayout()
        self.lbl_info_a = QLabel("")
        self.lbl_info_a.setStyleSheet("color: #0bd; font-family: monospace; font-size: 14px;")
        self.lbl_info_a.setFixedWidth(400) 
        
        self.lbl_info_b = QLabel("")
        self.lbl_info_b.setStyleSheet("color: #0bd; font-family: monospace; font-size: 14px;")
        self.lbl_info_b.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.lbl_info_b.setFixedWidth(400) 
        
        info_layout.addWidget(self.lbl_info_a)
        info_layout.addStretch()
        info_layout.addWidget(self.lbl_info_b)
        main_layout.addLayout(info_layout)

        # Instructions
        instruction_label = QLabel("Sync: Arrows | Left: A/D | Right: J/L | Zoom: Wheel | Pan: Drag | Right Click: Menu")
        instruction_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instruction_label.setStyleSheet("color: #666; font-size: 12px; margin-top: 5px;")
        main_layout.addWidget(instruction_label)
        
        # Ensure main window has focus at startup, preventing filters from stealing it
        self.setFocus()

    def elide_text(self, text, max_len=40):
        if len(text) <= max_len:
            return text
        return text[:max_len//2 - 2] + "..." + text[-(max_len//2 - 1):]

    def update_recent_menu(self, button, side):
        menu = QMenu(self)
        menu.setStyleSheet("QMenu { background-color: #2b2b2b; color: white; } QMenu::item:selected { background-color: #444; }")
        
        # Close Folder Option
        action_close = QAction("Close Folder", self)
        action_close.triggered.connect(lambda: self.close_folder(side))
        menu.addAction(action_close)
        
        menu.addSeparator()

        if not self.recent_folders:
            action = QAction("No Recent Folders", self)
            action.setEnabled(False)
            menu.addAction(action)
        else:
            label_action = QAction("Recent Folders:", self)
            label_action.setEnabled(False)
            menu.addAction(label_action)
            menu.addSeparator()
            
            for folder in self.recent_folders:
                if os.path.exists(folder):
                    action = QAction(folder, self)
                    action.triggered.connect(lambda checked, f=folder: self.load_folder_path(side, f))
                    menu.addAction(action)
        
        button.setMenu(menu)

    def close_folder(self, side):
        if side == 'A':
            self.folder_a = None
            self.all_files_a = []
            self.files_a = []
            self.current_index_a = 0
            self.btn_load_a.setText("Load Left")
            self.txt_filter_a.clear()
            self.panel_a.load_image(None)
            self.lbl_filename_a.setText("")
        else:
            self.folder_b = None
            self.all_files_b = []
            self.files_b = []
            self.current_index_b = 0
            self.btn_load_b.setText("Load Right")
            self.txt_filter_b.clear()
            self.panel_b.load_image(None)
            self.lbl_filename_b.setText("")
        self.update_images()

    def add_to_recent(self, folder):
        if folder in self.recent_folders:
            self.recent_folders.remove(folder)
        self.recent_folders.insert(0, folder)
        self.recent_folders = self.recent_folders[:5]
        self.settings.setValue("recent_folders", self.recent_folders)
        self.update_recent_menu(self.btn_load_a, 'A')
        self.update_recent_menu(self.btn_load_b, 'B')

    def select_folder(self, side):
        folder = QFileDialog.getExistingDirectory(self, f"Select Folder {side}")
        if folder:
            self.load_folder_path(side, folder)

    def load_folder_path(self, side, folder):
        self.add_to_recent(folder)
        if side == 'A':
            self.folder_a = folder
            self.all_files_a = self.get_image_files(folder)
            self.apply_filter('A') # This will set self.files_a
            self.btn_load_a.setText(os.path.basename(folder))
        else:
            self.folder_b = folder
            self.all_files_b = self.get_image_files(folder)
            self.apply_filter('B') # This will set self.files_b
            self.btn_load_b.setText(os.path.basename(folder))
        
    def get_image_files(self, folder):
        files = []
        try:
            for f in os.listdir(folder):
                _, ext = os.path.splitext(f)
                if ext.lower() in IMG_EXTENSIONS:
                    files.append(os.path.join(folder, f))
            files.sort()
        except Exception as e:
            print(f"Error reading folder {folder}: {e}")
        return files

    def apply_filter(self, side):
        if side == 'A':
            pattern = self.txt_filter_a.text()
            source_files = self.all_files_a
        else:
            pattern = self.txt_filter_b.text()
            source_files = self.all_files_b
            
        filtered = []
        try:
            for f in source_files:
                filename = os.path.basename(f)
                if not pattern or re.search(pattern, filename):
                    filtered.append(f)
        except re.error:
            print(f"Invalid regex: {pattern}")
            filtered = source_files 

        if side == 'A':
            self.files_a = filtered
            self.current_index_a = 0
        else:
            self.files_b = filtered
            self.current_index_b = 0
            
        self.update_images()

    def update_images(self):
        len_a = len(self.files_a)
        len_b = len(self.files_b)
        
        # Update Status A
        self.lbl_total_a.setText(f"/ {len_a}")
        if len_a > 0:
            self.spin_index_a.setMaximum(len_a)
            self.spin_index_a.blockSignals(True)
            self.spin_index_a.setValue(self.current_index_a + 1)
            self.spin_index_a.blockSignals(False)
        else:
            self.spin_index_a.setMaximum(1)
            self.spin_index_a.setValue(0) # 0 to indicate empty
        
        # Update Status B
        self.lbl_total_b.setText(f"/ {len_b}")
        if len_b > 0:
            self.spin_index_b.setMaximum(len_b)
            self.spin_index_b.blockSignals(True)
            self.spin_index_b.setValue(self.current_index_b + 1)
            self.spin_index_b.blockSignals(False)
        else:
            self.spin_index_b.setMaximum(1)
            self.spin_index_b.setValue(0)

        # Update Image A
        if self.current_index_a < len_a:
            path_a = self.files_a[self.current_index_a]
            self.panel_a.load_image(path_a)
            self.lbl_filename_a.setText(self.elide_text(os.path.basename(path_a)))
        else:
            self.panel_a.load_image(None)
            self.lbl_filename_a.setText("")

        # Update Image B
        if self.current_index_b < len_b:
            path_b = self.files_b[self.current_index_b]
            self.panel_b.load_image(path_b)
            self.lbl_filename_b.setText(self.elide_text(os.path.basename(path_b)))
        else:
            self.panel_b.load_image(None)
            self.lbl_filename_b.setText("")

    def jump_to_index(self, side):
        changed = False
        if side == 'A':
            val = self.spin_index_a.value() - 1
            if val >= 0 and val < len(self.files_a):
                self.current_index_a = val
                changed = True
        else:
            val = self.spin_index_b.value() - 1
            if val >= 0 and val < len(self.files_b):
                self.current_index_b = val
                changed = True
        
        if changed:
            self.update_images()
        
        # We don't need to clear focus here anymore since valueChanged works while typing
        # and we want to keep typing. If we clear focus, it disrupts typing.
        # self.setFocus() # Removed to keep focus in spinbox

    def change_interpolation(self, text):
        self.panel_a.set_interpolation_mode(text)
        self.panel_b.set_interpolation_mode(text)

    def keyPressEvent(self, event):
        key = event.key()
        len_a = len(self.files_a)
        len_b = len(self.files_b)
        
        # Sync Navigation
        if key == Qt.Key.Key_Right:
            changed = False
            if self.current_index_a < len_a - 1:
                self.current_index_a += 1
                changed = True
            if self.current_index_b < len_b - 1:
                self.current_index_b += 1
                changed = True
            if changed: self.update_images()
                
        elif key == Qt.Key.Key_Left:
            changed = False
            if self.current_index_a > 0:
                self.current_index_a -= 1
                changed = True
            if self.current_index_b > 0:
                self.current_index_b -= 1
                changed = True
            if changed: self.update_images()

        # Independent Left (A/D)
        elif key == Qt.Key.Key_D:
            if self.current_index_a < len_a - 1:
                self.current_index_a += 1
                self.update_images()
        elif key == Qt.Key.Key_A:
            if self.current_index_a > 0:
                self.current_index_a -= 1
                self.update_images()

        # Independent Right (J/L)
        elif key == Qt.Key.Key_L:
            if self.current_index_b < len_b - 1:
                self.current_index_b += 1
                self.update_images()
        elif key == Qt.Key.Key_J:
            if self.current_index_b > 0:
                self.current_index_b -= 1
                self.update_images()
                
        else:
            super().keyPressEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
