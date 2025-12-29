import os
import numpy as np
import tifffile
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QSizePolicy
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize, QMutex, QWaitCondition

class ImageLoader(QThread):
    image_loaded = pyqtSignal(QImage, str) # image, path
    error_occurred = pyqtSignal(str)

    def __init__(self, path, target_size, parent=None):
        super().__init__(parent)
        self.path = path
        self.target_size = target_size
        self._is_cancelled = False

    def run(self):
        if self._is_cancelled or not self.path:
            return

        try:
            if self.path.lower().endswith(('.tif', '.tiff')):
                qimg = self._load_tiff(self.path)
            else:
                qimg = QImage(self.path)

            if not qimg.isNull():
                self.image_loaded.emit(qimg, self.path)
            else:
                self.error_occurred.emit(f"Failed to load {os.path.basename(self.path)}")
                
        except Exception as e:
            self.error_occurred.emit(str(e))

    def _load_tiff(self, path):
         # Read using tifffile
        data = tifffile.imread(path)
        
        # Handle Floating Point
        if data.dtype.kind == 'f':
            data_min = np.nanmin(data)
            data_max = np.nanmax(data)
            if data_max != data_min:
                data = (data - data_min) / (data_max - data_min)
            else:
                data = np.zeros_like(data)
            data = (data * 255).astype(np.uint8)
        elif data.dtype == np.uint16:
            data = (data / 256).astype(np.uint8)
        
        height, width = data.shape[:2]
        
        if data.ndim == 2:
            return QImage(data.data, width, height, data.strides[0], QImage.Format.Format_Grayscale8).copy()
        elif data.ndim == 3:
            if data.shape[2] == 3:
                return QImage(data.data, width, height, data.strides[0], QImage.Format.Format_RGB888).copy()
            elif data.shape[2] == 4:
                return QImage(data.data, width, height, data.strides[0], QImage.Format.Format_RGBA8888).copy()
        
        return QImage()


class ImagePanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.image_label = QLabel("No Image")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        self.image_label.setStyleSheet("background-color: #1e1e1e; color: #888;")
        
        self.layout.addWidget(self.image_label)
        
        self.current_loader = None
        self.current_pixmap = None
        self.current_path = None

    def load_image(self, file_path):
        # Cancel previous load
        if self.current_loader and self.current_loader.isRunning():
            self.current_loader.terminate() # Force kill for responsiveness in this simple case or use flags
            self.current_loader.wait()

        self.current_path = file_path
        if not file_path:
            self.image_label.setText("No Image")
            self.current_pixmap = None
            return

        # self.image_label.setText("Loading...") # Removed to prevent flash
        
        # Start new load
        self.current_loader = ImageLoader(file_path, self.size())
        self.current_loader.image_loaded.connect(self._on_image_loaded)
        self.current_loader.error_occurred.connect(self._on_error)
        self.current_loader.start()

    def _on_image_loaded(self, qimg, path):
        if path != self.current_path:
            return # Old result
            
        self.current_pixmap = QPixmap.fromImage(qimg)
        self.update_display()

    def _on_error(self, msg):
        self.image_label.setText(f"Error: {msg}")

    def update_display(self):
        if self.current_pixmap and not self.current_pixmap.isNull():
            # Scale to fit window
            scaled = self.current_pixmap.scaled(
                self.size(), 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
            self.image_label.setPixmap(scaled)

    def resizeEvent(self, event):
        if self.current_pixmap:
            self.update_display()
        super().resizeEvent(event)
