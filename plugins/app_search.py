import os
from plugins.base_plugin import PluginBase, SearchResult
from PyQt6.QtWidgets import QFileIconProvider
from PyQt6.QtCore import QFileInfo

class AppSearchPlugin(PluginBase):
    id = "app_search"
    name = "Application Search"
    
    def __init__(self):
        self.apps = []
        self.scan_apps()
        
    def scan_apps(self):
        paths = [
            os.environ.get("PROGRAMDATA", "C:\\ProgramData") + "\\Microsoft\\Windows\\Start Menu\\Programs",
            os.environ.get("APPDATA", "") + "\\Microsoft\\Windows\\Start Menu\\Programs"
        ]
        
        for path in paths:
            if not os.path.exists(path):
                continue
                
            for root, dirs, files in os.walk(path):
                for file in files:
                    if file.endswith(".lnk"):
                        name = file[:-4]
                        full_path = os.path.join(root, file)
                        self.apps.append({"name": name, "path": full_path})

    def query(self, text: str):
        if not text.strip():
            return []
            
        text_lower = text.lower()
        is_app_prefix = text_lower.startswith("app ")
        if is_app_prefix:
            text_lower = text_lower[4:].strip()
            if not text_lower:
                return []
                
        results = []
        provider = QFileIconProvider()
        
        for app in self.apps:
            if text_lower in app["name"].lower():
                icon = provider.icon(QFileInfo(app["path"]))
                if text_lower == app["name"].lower():
                    score = 250 + (50 if is_app_prefix else 0)
                elif app["name"].lower().startswith(text_lower):
                    score = 120 + (100 if is_app_prefix else 0)
                else:
                    score = 88 + (100 if is_app_prefix else 0)
                
                results.append(SearchResult(
                    title=app["name"],
                    subtitle="Application",
                    icon=icon,
                    score=score,
                    action=lambda path=app["path"]: self.launch_app(path)
                ))
                
        # Sort and limit
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:10]

    def launch_app(self, path):
        # On Windows, os.startfile opens the shortcut target
        try:
            os.startfile(path)
        except Exception as e:
            print(f"Failed to launch app: {e}")
