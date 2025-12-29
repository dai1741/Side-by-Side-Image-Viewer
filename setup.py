import sys
from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options = {
    "packages": ["os", "sys", "numpy", "tifffile", "PyQt6", "PIL", "imagecodecs"],
    "excludes": ["tkinter", "unittest", "email", "http", "xml", "pydoc"],
    "include_files": [], # Add any data files here if needed
}

# GUI applications require a different base on Windows (the default is for a
# console application).
base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(
    name="ImageComparisonViewer",
    version="1.0",
    description="High-performance Side-by-Side Image Viewer",
    options={"build_exe": build_exe_options},
    executables=[Executable("main.py", base=base, target_name="ImageComparisonViewer.exe", icon=None)],
)
