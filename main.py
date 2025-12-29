import sys
import os
import glob
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QFileDialog, QSplitter,
                             QToolButton, QMenu, QSizePolicy)
from PyQt6.QtGui import QAction, QActionGroup
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
        
        # Left Load Button (ToolButton for Menu)
        self.btn_load_a = QToolButton()
        self.btn_load_a.setText("Load Left Folder")
        self.btn_load_a.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)
        self.update_recent_menu(self.btn_load_a, 'A')
        self.btn_load_a.clicked.connect(lambda: self.select_folder('A'))
        self.btn_load_a.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btn_load_a.setStyleSheet("background-color: #333; padding: 5px 10px; border-radius: 4px; color: white;")
        
        # Left Filename Label
        self.lbl_filename_a = QLabel("")
        self.lbl_filename_a.setStyleSheet("color: #aaa; font-size: 11px;")
        self.lbl_filename_a.setAlignment(Qt.AlignmentFlag.AlignLeft)

        # Right Load Button
        self.btn_load_b = QToolButton()
        self.btn_load_b.setText("Load Right Folder")
        self.btn_load_b.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)
        self.update_recent_menu(self.btn_load_b, 'B')
        self.btn_load_b.clicked.connect(lambda: self.select_folder('B'))
        self.btn_load_b.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btn_load_b.setStyleSheet("background-color: #333; padding: 5px 10px; border-radius: 4px; color: white;")

        # Right Filename Label
        self.lbl_filename_b = QLabel("")
        self.lbl_filename_b.setStyleSheet("color: #aaa; font-size: 11px;")
        self.lbl_filename_b.setAlignment(Qt.AlignmentFlag.AlignRight)

        # Status Label (Center)
        self.lbl_files_status = QLabel("0 / 0")
        self.lbl_files_status.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.lbl_files_status.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Bar Layout
        control_bar.addWidget(self.btn_load_a)
        control_bar.addWidget(self.lbl_filename_a)
        control_bar.addStretch()
        control_bar.addWidget(self.lbl_files_status)
        control_bar.addStretch()
        control_bar.addWidget(self.lbl_filename_b)
        control_bar.addWidget(self.btn_load_b)

        main_layout.addLayout(control_bar)

        # Image Area (Splitter)
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.panel_a = ImagePanel()
        self.panel_b = ImagePanel()
        self.splitter.addWidget(self.panel_a)
        self.splitter.addWidget(self.panel_b)
        self.splitter.setSizes([800, 800])
        
        main_layout.addWidget(self.splitter, stretch=1)

        # Instructions
        instruction_label = QLabel("Sync: Right/Left Arrows | Left Only: A/D | Right Only: J/L")
        instruction_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instruction_label.setStyleSheet("color: #666; font-size: 12px; margin-top: 5px;")
        main_layout.addWidget(instruction_label)

    def update_recent_menu(self, button, side):
        menu = QMenu(self)
        menu.setStyleSheet("QMenu { background-color: #2b2b2b; color: white; } QMenu::item:selected { background-color: #444; }")
        
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

    def add_to_recent(self, folder):
        if folder in self.recent_folders:
            self.recent_folders.remove(folder)
        self.recent_folders.insert(0, folder)
        self.recent_folders = self.recent_folders[:5] # Keep last 5
        self.settings.setValue("recent_folders", self.recent_folders)
        
        # Update both menus
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
        # Update Status (Using max length context, though indices are separate now)
        len_a = len(self.files_a)
        len_b = len(self.files_b)
        
        status_text = f"L: {self.current_index_a + 1}/{len_a} | R: {self.current_index_b + 1}/{len_b}"
        if len_a == 0 and len_b == 0:
            status_text = "0 / 0"
        self.lbl_files_status.setText(status_text)

        # Update Image A
        if self.current_index_a < len_a:
            path_a = self.files_a[self.current_index_a]
            self.panel_a.load_image(path_a)
            self.lbl_filename_a.setText(os.path.basename(path_a))
        else:
            self.panel_a.load_image(None)
            self.lbl_filename_a.setText("")

        # Update Image B
        if self.current_index_b < len_b:
            path_b = self.files_b[self.current_index_b]
            self.panel_b.load_image(path_b)
            self.lbl_filename_b.setText(os.path.basename(path_b))
        else:
            self.panel_b.load_image(None)
            self.lbl_filename_b.setText("")

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
