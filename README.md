# Image Comparison Viewer

## Overview
A high-performance, synchronized image comparison viewer built with Python (PyQt6). Supports 8K images, scientific TIFFs, and advanced inspection tools (Zoom/Pan/Interpolation).

## How to Run
1.  **Run the Executable**:
    Open the `build` folder and run `ImageComparisonViewer.exe`.

## Controls & Features
| Category | Action | Key / Control |
| :--- | :--- | :--- |
| **Navigation** | Sync Next/Prev | `Right Arrow` / `Left Arrow` |
| | Left Only | `D` (Next), `A` (Prev) |
| | Right Only | `L` (Next), `J` (Prev) |
| | Jump to Index | Type number in "Index:" box + Enter |
| **View** | Zoom | **Mouse Wheel** |
| | Pan | **Drag Mouse** (Left click and scroll/drag) |
| | Context Menu | **Right Click** on image |
| | Interpolation | Select "Nearest" (Pixelated) or "Bilinear" (Smooth) from dropdown |
| | Pixel Info | **Hover** mouse over image to see X, Y, and RGB values at bottom |
| **Tools** | Copy Paths | Click **Copy Paths** button |
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
