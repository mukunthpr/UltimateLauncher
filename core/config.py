import os
import json

class ConfigManager:
    def __init__(self):
        self.config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.json")
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
