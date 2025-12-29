# Image Comparison Viewer

## Overview
A high-performance, synchronized image comparison viewer built with Python (PyQt6). Supports 8K images, scientific TIFFs, and advanced inspection tools (Zoom/Pan/Interpolation).

## Installation
1.  **Clone the Repository**:
    ```bash
    git clone https://github.com/dai1741/Side-by-Side-Image-Viewer.git
    cd Side-by-Side-Image-Viewer
    ```
2.  **Set up Virtual Environment**:
    ```bash
    python -m venv .venv
    # Windows:
    .\.venv\Scripts\Activate.ps1
    # Mac/Linux:
    source .venv/bin/activate
    ```
3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## How to Run
### Option 1: Run from Source
```bash
python main.py
```

### Option 2: Build Executable
To create a standalone `.exe`:
```bash
python setup.py build
```
Then open the created `build/exe.win-amd64-.../` folder and launch `ImageComparisonViewer.exe`.

## Controls & Features
| Category | Action | Key / Control |
| :--- | :--- | :--- |
| **Navigation** | Sync Next/Prev | `Right Arrow` / `Left Arrow` |
| | Left Only | `D` (Next), `A` (Prev) |
| | Right Only | `L` (Next), `J` (Prev) |
| | Jump to Index | Type number in **L:** or **R:** box (updates immediately) |
| **View** | Zoom | **Mouse Wheel** |
| | Pan | **Drag Mouse** (Left click and scroll/drag) |
| | Context Menu | **Right Click** on image (Copy Path, Open, etc.) |
| | Interpolation | Select "Nearest" (Pixelated) or "Bilinear" (Smooth) from dropdown |
| | Pixel Info | **Hover** mouse over image to see X, Y, and RGB values at bottom |
| **Tools** | **Filter Images** | Type Regex in **Filter...** box (next to Load button) |
| | **Unfocus Inputs**| Press **Escape** while typing in ANY box to return focus to navigation |
| **Files** | Load Folder | Click "Load" button or use History arrow |
| | Close Folder | Click **Arrow** on Load button -> **Close Folder** |
| | History | Click the small **Arrow** on Load button |

## Verification Steps
### 1. Advanced Inspection (Zoom/Pan/Hover)
-   **Zoom**: Hover over an image and scroll the mouse wheel.
-   **Pan**: Click and drag the image.
-   **Pixel Info**: Move your mouse over an image. Numbers are zero-padded (e.g., `X:0100 Y:0050`) to prevent jitter.

### 2. File Management
-   **Close Folder**: Click the arrow on the "Load" button and select "Close Folder". The image should disappear.
-   **Long Filenames**: Load a file with a long name. The UI should display it as truncated (e.g., `very_long...name.jpg`) and not shift the layout.
