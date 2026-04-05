import sys
import os
import traceback

def handle_exception(exc_type, exc_value, exc_traceback):
    with open(os.path.join(os.path.dirname(__file__), "crash.log"), "w") as f:
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=f)
    sys.__excepthook__(exc_type, exc_value, exc_traceback)

sys.excepthook = handle_exception
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QStyle
from ui.main_window import LauncherWindow
from core.hotkey import HotkeyManager
from core.plugin_manager import PluginManager
from core.config import ConfigManager
from ui.settings_window import SettingsWindow

def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    # Load stylesheet
    style_path = os.path.join(os.path.dirname(__file__), "ui", "styles.qss")
    try:
        with open(style_path, "r") as f:
            app.setStyleSheet(f.read())
    except FileNotFoundError:
        print(f"Warning: Stylesheet not found at {style_path}")

    # Setup Configurations
    config_mgr = ConfigManager()

    plugin_mgr = PluginManager(config_mgr=config_mgr)
    window = LauncherWindow(plugin_mgr)
    window.center_window()
    
    # Warm up the OS window buffers invisibly to prevent first-launch focus lag
    window.setWindowOpacity(0.0)
    window.show()
    window.hide()
    window.setWindowOpacity(1.0)
    
    # Setup hotkey manager
    hotkey_mgr = HotkeyManager(window, config_manager=config_mgr)
    
    # Initialize Settings Window
    settings_win = SettingsWindow(config_mgr, hotkey_mgr, plugin_mgr)
    window.settings_window = settings_win
    
    # Setup User Icon
    from PyQt6.QtGui import QIcon
    icon_path = os.path.join(os.path.dirname(__file__), "assets", "icon.png")
    app_icon = QIcon(icon_path) if os.path.exists(icon_path) else app.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
    app.setWindowIcon(app_icon)
    
    # Setup System Tray
    tray_icon = QSystemTrayIcon(app_icon, app)
    tray_menu = QMenu()
    
    show_action = tray_menu.addAction("Show Launcher")
    show_action.triggered.connect(window.toggle_visibility)
    
    settings_action = tray_menu.addAction("Settings...")
    settings_action.triggered.connect(settings_win.show)
    
    tray_menu.addSeparator()
    
    quit_action = tray_menu.addAction("Quit UltimateLauncher")
    quit_action.triggered.connect(app.quit)
    
    tray_icon.setContextMenu(tray_menu)
    tray_icon.show()
    window.show()
    window.search_box.setFocus()

    hotkey_mgr.start()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
