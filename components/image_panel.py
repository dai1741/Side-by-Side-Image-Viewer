import os
import sys
import subprocess
import numpy as np
import tifffile
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QGraphicsView, QGraphicsScene, 
                             QGraphicsPixmapItem, QLabel, QSizePolicy, QMenu, QApplication)
from PyQt6.QtGui import QPixmap, QImage, QPainter, QCursor, QAction
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize, QEvent, QRectF

# Helper to import pywin32 components safely
try:
    from win32com.shell import shell, shellcon
    import win32con
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False

class ImageLoader(QThread):
    image_loaded = pyqtSignal(QImage, str, int) # image, path, load_id
    error_occurred = pyqtSignal(str)

    def __init__(self, path, load_id, parent=None):
        super().__init__(parent)
        self.path = path
        self.load_id = load_id
        self._is_cancelled = False

    def run(self):
        if not self.path:
            return

        try:
            if self.path.lower().endswith(('.tif', '.tiff')):
                qimg = self._load_tiff(self.path)
            else:
                qimg = QImage(self.path)

            if not qimg.isNull():
                self.image_loaded.emit(qimg, self.path, self.load_id)
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
    pixel_info_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Graphics View Setup
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setDragMode(QGraphicsView.DragMode.NoDrag) # Default to NoDrag (Arrow Cursor)
        self.view.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.view.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.view.setFrameShape(QGraphicsView.Shape.NoFrame)
        self.view.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.view.setStyleSheet("background-color: #1e1e1e;")
        self.view.setMouseTracking(True)
        self.view.viewport().installEventFilter(self)
        
        # Context Menu
        self.view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.view.customContextMenuRequested.connect(self.show_context_menu)

        # Image Item
        self.pixmap_item = QGraphicsPixmapItem()
        self.scene.addItem(self.pixmap_item)
        
        self.layout.addWidget(self.view)
        
        self.current_loader = None
        self.current_path = None
        self.current_image = None
        self.current_interpolation = Qt.TransformationMode.FastTransformation
        self.load_id = 0 

    def eventFilter(self, source, event):
        if source == self.view.viewport():
            if event.type() == QEvent.Type.MouseMove:
                self._handle_mouse_move(event)
            elif event.type() == QEvent.Type.MouseButtonPress:
                if event.button() == Qt.MouseButton.LeftButton:
                    self.view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
            elif event.type() == QEvent.Type.MouseButtonRelease:
                if event.button() == Qt.MouseButton.LeftButton:
                    self.view.setDragMode(QGraphicsView.DragMode.NoDrag)
            elif event.type() == QEvent.Type.Leave:
                 self.pixel_info_changed.emit("")
                 
        return super().eventFilter(source, event)

    def _handle_mouse_move(self, event):
        if self.pixmap_item.pixmap().isNull() or self.current_image is None:
            return

        view_pos = event.pos()
        scene_pos = self.view.mapToScene(view_pos)
        item_pos = self.pixmap_item.mapFromScene(scene_pos)
        
        x = int(item_pos.x())
        y = int(item_pos.y())
        
        w = self.current_image.width()
        h = self.current_image.height()

        if 0 <= x < w and 0 <= y < h:
            color = self.current_image.pixelColor(x, y)
            r, g, b = color.red(), color.green(), color.blue()
            info = f"X:{x:04d} Y:{y:04d} | R:{r:03d} G:{g:03d} B:{b:03d}"
            self.pixel_info_changed.emit(info)
        else:
            self.pixel_info_changed.emit("")

    def load_image(self, file_path):
        # Increment load ID to invalidate previous renders
        self.load_id += 1
        
        # We do NOT terminate the old thread forcefully to avoid freezes.
        # We just let it finish and ignore its result.
        
        self.current_path = file_path
        if not file_path:
            self.pixmap_item.setPixmap(QPixmap())
            self.current_image = None
            self.scene.setSceneRect(QRectF()) # Reset scene rect
            return

        # Start new load
        self.current_loader = ImageLoader(file_path, self.load_id)
        self.current_loader.image_loaded.connect(self._on_image_loaded)
        self.current_loader.start()

    def _on_image_loaded(self, qimg, path, loaded_id):
        # Ignore if this result is from an old, superseded load request
        if loaded_id != self.load_id:
            return

        self.current_image = qimg.copy() # Store copy for pixel reading
        pixmap = QPixmap.fromImage(qimg)
        self.pixmap_item.setPixmap(pixmap)
        self.pixmap_item.setTransformationMode(self.current_interpolation)
        self.scene.setSceneRect(QRectF(pixmap.rect())) # Correctly set scene size for scrollbars
        self.fit_to_view()

    def set_interpolation_mode(self, mode_str):
        if mode_str == "Bilinear":
            self.current_interpolation = Qt.TransformationMode.SmoothTransformation
        else:
            self.current_interpolation = Qt.TransformationMode.FastTransformation
        
        self.pixmap_item.setTransformationMode(self.current_interpolation)
        self.view.viewport().update()

    def fit_to_view(self):
        if self.pixmap_item.pixmap().isNull():
            return
        self.view.fitInView(self.pixmap_item, Qt.AspectRatioMode.KeepAspectRatio)

    def resizeEvent(self, event):
        self.fit_to_view()
        super().resizeEvent(event)

    def wheelEvent(self, event):
        if self.pixmap_item.pixmap().isNull():
            return
            
        zoom_in_factor = 1.25
        zoom_out_factor = 1 / zoom_in_factor

        if event.angleDelta().y() > 0:
            zoom_factor = zoom_in_factor
        else:
            zoom_factor = zoom_out_factor

        self.view.scale(zoom_factor, zoom_factor)

    def show_context_menu(self, pos):
        if not self.current_path or not os.path.exists(self.current_path):
            return

        menu = QMenu(self)
        
        action_open = QAction("Open", self)
        action_open.triggered.connect(self.action_open)
        menu.addAction(action_open)

        action_reveal = QAction("Reveal in Explorer", self)
        action_reveal.triggered.connect(self.action_reveal)
        menu.addAction(action_reveal)

        action_copy = QAction("Copy Path", self)
        action_copy.triggered.connect(self.action_copy)
        menu.addAction(action_copy)

        menu.addSeparator()

        action_props = QAction("Properties", self)
        action_props.triggered.connect(self.action_properties)
        menu.addAction(action_props)

        menu.exec(QCursor.pos())

    def action_open(self):
        if self.current_path:
            os.startfile(self.current_path)

    def action_reveal(self):
        if self.current_path:
            path = os.path.normpath(self.current_path)
            subprocess.run(['explorer', '/select,', path])

    def action_copy(self):
        if self.current_path:
            QApplication.clipboard().setText(self.current_path)

    def action_properties(self):
        if not self.current_path or not HAS_WIN32:
            return

        try:
            path = os.path.normpath(self.current_path)
            shell.ShellExecuteEx(
                nShow=win32con.SW_SHOW,
                fMask=shellcon.SEE_MASK_INVOKEIDLIST,
                lpVerb='properties',
                lpFile=path,
                lpParameters='',
                lpDirectory=''
            )
        except Exception as e:
            print(f"Error showing properties: {e}")
