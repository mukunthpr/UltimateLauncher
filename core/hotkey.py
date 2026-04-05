from PyQt6.QtCore import QObject, pyqtSignal
import keyboard

class HotkeySignalManager(QObject):
    toggle_signal = pyqtSignal()

class HotkeyManager:
    def __init__(self, window, config_manager=None):
        self.window = window
        self.config_manager = config_manager
        self.signal_manager = HotkeySignalManager()
        self.signal_manager.toggle_signal.connect(self.window.toggle_visibility)
        self.current_hotkey = "alt+space"

    def _on_activate(self):
        self.signal_manager.toggle_signal.emit()

    def _resolve_key(self, key_str):
        return key_str.lower().replace("hyper", "ctrl+alt+shift+windows")

    def start(self):
        if self.config_manager:
            self.current_hotkey = self.config_manager.get("hotkey")
        
        try:
            keyboard.add_hotkey(self._resolve_key(self.current_hotkey), self._on_activate, suppress=True)
        except Exception as e:
            print(f"Failed to start global hotkey listener ({self.current_hotkey}): {e}")

    def update_hotkey(self, new_hotkey):
        if self.current_hotkey == new_hotkey:
            return
            
        try:
            keyboard.remove_hotkey(self.current_hotkey)
        except Exception as e:
            print(f"Failed to remove old hotkey: {e}")
            
        self.current_hotkey = new_hotkey
        
        try:
            keyboard.add_hotkey(self._resolve_key(self.current_hotkey), self._on_activate, suppress=True)
            if self.config_manager:
                self.config_manager.set("hotkey", new_hotkey)
        except Exception as e:
            print(f"Failed to bind new hotkey {new_hotkey}: {e}")
