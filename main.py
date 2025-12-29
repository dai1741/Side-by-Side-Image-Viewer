import sys
import os
import glob
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QFileDialog, QSplitter,
                             QToolButton, QMenu, QSizePolicy, QComboBox, QSpinBox)
from PyQt6.QtGui import QAction, QActionGroup, QFontMetrics
from PyQt6.QtCore import Qt, QSettings
from components.image_panel import ImagePanel

# Supported extensions
IMG_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.webp', '.tif', '.tiff'}

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
        self.files_a = []
        self.files_b = []
        self.current_index_a = 0
        self.current_index_b = 0

        # UI Components
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Top Control Bar
        control_bar = QHBoxLayout()
        
        # Left Load Button
        self.btn_load_a = QToolButton()
        self.btn_load_a.setText("Load Left")
        self.btn_load_a.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)
        self.update_recent_menu(self.btn_load_a, 'A')
        self.btn_load_a.clicked.connect(lambda: self.select_folder('A'))
        self.btn_load_a.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btn_load_a.setStyleSheet("background-color: #333; padding: 5px; border-radius: 4px; color: white;")
        
        self.lbl_filename_a = QLabel("")
        self.lbl_filename_a.setStyleSheet("color: #aaa; font-size: 11px;")
        self.lbl_filename_a.setFixedWidth(250)
        self.lbl_filename_a.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Middle Controls
        self.btn_copy_path = QPushButton("Copy Paths")
        self.btn_copy_path.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btn_copy_path.setStyleSheet("background-color: #444; padding: 5px; border-radius: 4px;")
        self.btn_copy_path.clicked.connect(self.copy_current_paths)

        self.spin_index = QSpinBox()
        self.spin_index.setPrefix("Index: ")
        self.spin_index.setRange(1, 99999)
        self.spin_index.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.spin_index.setStyleSheet("background-color: #333; color: white; padding: 5px;")
        self.spin_index.editingFinished.connect(self.jump_to_index)

        self.combo_interp = QComboBox()
        self.combo_interp.addItems(["Nearest", "Bilinear"])
        self.combo_interp.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.combo_interp.setStyleSheet("background-color: #333; color: white; padding: 5px;")
        self.combo_interp.currentTextChanged.connect(self.change_interpolation)

        self.lbl_files_status = QLabel("0 / 0")
        self.lbl_files_status.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.lbl_files_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_files_status.setFixedWidth(100) # Fixed width prevents jitter

        # Right Load Button
        self.btn_load_b = QToolButton()
        self.btn_load_b.setText("Load Right")
        self.btn_load_b.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)
        self.update_recent_menu(self.btn_load_b, 'B')
        self.btn_load_b.clicked.connect(lambda: self.select_folder('B'))
        self.btn_load_b.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btn_load_b.setStyleSheet("background-color: #333; padding: 5px; border-radius: 4px; color: white;")

        self.lbl_filename_b = QLabel("")
        self.lbl_filename_b.setStyleSheet("color: #aaa; font-size: 11px;")
        self.lbl_filename_b.setFixedWidth(250) # Fixed width
        self.lbl_filename_b.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Add to Layout
        control_bar.addWidget(self.btn_load_a)
        control_bar.addWidget(self.lbl_filename_a)
        control_bar.addStretch()
        
        control_bar.addWidget(self.btn_copy_path)
        control_bar.addWidget(self.spin_index)
        control_bar.addWidget(self.combo_interp)
        control_bar.addWidget(self.lbl_files_status)
        
        control_bar.addStretch()
        control_bar.addWidget(self.lbl_filename_b)
        control_bar.addWidget(self.btn_load_b)

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
        self.lbl_info_a.setFixedWidth(400) # Fixed width for info
        
        self.lbl_info_b = QLabel("")
        self.lbl_info_b.setStyleSheet("color: #0bd; font-family: monospace; font-size: 14px;")
        self.lbl_info_b.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.lbl_info_b.setFixedWidth(400) # Fixed width for info
        
        info_layout.addWidget(self.lbl_info_a)
        info_layout.addStretch()
        info_layout.addWidget(self.lbl_info_b)
        main_layout.addLayout(info_layout)

        # Instructions
        instruction_label = QLabel("Sync: Arrows | Left: A/D | Right: J/L | Zoom: Wheel | Pan: Drag | Right Click: Menu")
        instruction_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instruction_label.setStyleSheet("color: #666; font-size: 12px; margin-top: 5px;")
        main_layout.addWidget(instruction_label)

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
            self.files_a = []
            self.current_index_a = 0
            self.btn_load_a.setText("Load Left")
            self.panel_a.load_image(None)
            self.lbl_filename_a.setText("")
        else:
            self.folder_b = None
            self.files_b = []
            self.current_index_b = 0
            self.btn_load_b.setText("Load Right")
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
            self.files_a = self.get_image_files(folder)
            self.current_index_a = 0
            self.btn_load_a.setText(os.path.basename(folder))
        else:
            self.folder_b = folder
            self.files_b = self.get_image_files(folder)
            self.current_index_b = 0
            self.btn_load_b.setText(os.path.basename(folder))
        
        self.update_images()

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

    def update_images(self):
        len_a = len(self.files_a)
        len_b = len(self.files_b)
        
        status_text = f"L: {self.current_index_a + 1}/{len_a} | R: {self.current_index_b + 1}/{len_b}"
        if len_a == 0 and len_b == 0:
            status_text = "0 / 0"
        self.lbl_files_status.setText(status_text)
        
        max_len = max(len_a, len_b)
        if max_len > 0:
            self.spin_index.setMaximum(max_len)
            idx = self.current_index_a if len_a > 0 else self.current_index_b
            self.spin_index.blockSignals(True)
            self.spin_index.setValue(idx + 1)
            self.spin_index.blockSignals(False)
        else:
            self.spin_index.setMaximum(1)
            self.spin_index.setValue(1)

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

    def copy_current_paths(self):
        paths = []
        if self.current_index_a < len(self.files_a):
            paths.append(self.files_a[self.current_index_a])
        if self.current_index_b < len(self.files_b):
            paths.append(self.files_b[self.current_index_b])
        
        if paths:
            text = "\n".join(paths)
            QApplication.clipboard().setText(text)
            self.btn_copy_path.setText("Copied!")

    def jump_to_index(self):
        val = self.spin_index.value() - 1 
        changed = False
        if val >= 0 and val < len(self.files_a):
            self.current_index_a = val
            changed = True
        if val >= 0 and val < len(self.files_b):
            self.current_index_b = val
            changed = True
        
        if changed:
            self.update_images()
        self.spin_index.clearFocus()
        self.setFocus()

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
