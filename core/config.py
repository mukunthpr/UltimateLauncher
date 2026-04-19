import os
import json

import sys
from pathlib import Path

class ConfigManager:
    def __init__(self):
        home = Path.home()
        if sys.platform == "win32":
            config_dir = home / "AppData" / "Local" / "UltimateLauncher"
        elif sys.platform == "darwin":
            config_dir = home / "Library" / "Application Support" / "UltimateLauncher"
        else:
            config_dir = home / ".config" / "UltimateLauncher"
            
        config_dir.mkdir(parents=True, exist_ok=True)
        self.config_path = str(config_dir / "config.json")
        self.defaults = {
            "hotkey": "alt+space",
            "run_on_startup": False,
            "first_time_launch": True
        }
        self.config = self.load()

    def load(self):
        if not os.path.exists(self.config_path):
            self.save(self.defaults)
            return self.defaults.copy()
        
        try:
            with open(self.config_path, "r") as f:
                data = json.load(f)
                config = self.defaults.copy()
                config.update(data)
                return config
        except Exception as e:
            print(f"Error loading config: {e}")
            return self.defaults.copy()

    def save(self, data=None):
        if data is not None:
            self.config = data
        try:
            with open(self.config_path, "w") as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")

    def get(self, key, default=None):
        return self.config.get(key, self.defaults.get(key, default))

    def set(self, key, value):
        self.config[key] = value
        self.save()
