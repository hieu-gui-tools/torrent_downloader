import sys
import os
import ctypes
from pathlib import Path

# Add assets directory to DLL search path for libtorrent / msvcp140.dll
base_dir = Path(__file__).resolve().parent.parent.parent
assets_dir = base_dir / "assets"
if assets_dir.exists():
    try:
        os.add_dll_directory(str(assets_dir))
    except Exception:
        pass

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette, QColor, QIcon
from PySide6.QtCore import Qt
from .ui.main_window import MainWindow

def main() -> None:
    # Set Windows taskbar icon app ID
    try:
        app_id = "mycompany.torrentdownloader.pro.1.0"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
    except Exception:
        pass

    app = QApplication(sys.argv)
    
    # Crucial for System Tray: keep app alive when main window is hidden
    app.setQuitOnLastWindowClosed(False)

    # Set app icon if available
    icon_ico = assets_dir / "app.ico"
    icon_png = assets_dir / "app.png"
    if icon_ico.exists():
        app_icon = QIcon(str(icon_ico))
        app.setWindowIcon(app_icon)
    elif icon_png.exists():
        app_icon = QIcon(str(icon_png))
        app.setWindowIcon(app_icon)

    # Enable Fusion style and dark theme
    app.setStyle("Fusion")
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(45, 45, 48))
    palette.setColor(QPalette.WindowText, Qt.white)
    palette.setColor(QPalette.Base, QColor(30, 30, 30))
    palette.setColor(QPalette.AlternateBase, QColor(40, 40, 40))
    palette.setColor(QPalette.ToolTipBase, Qt.black)
    palette.setColor(QPalette.ToolTipText, Qt.white)
    palette.setColor(QPalette.Text, Qt.white)
    palette.setColor(QPalette.Button, QColor(55, 55, 60))
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(16, 185, 129))
    palette.setColor(QPalette.HighlightedText, Qt.white)
    app.setPalette(palette)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
