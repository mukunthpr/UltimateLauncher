import os
import json
import webbrowser
from plugins.base_plugin import PluginBase, SearchResult

class QuicklinksPlugin(PluginBase):
    id = "quicklinks"
    name = "Quicklinks"
    prefix_alias = "ql"

    def __init__(self):
        super().__init__()
        self.config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "quicklinks.json")
        self.links = self._load()

    def _load(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        
        # Default seeding bundle
        defaults = {
            "github": "https://github.com",
            "youtube": "https://youtube.com",
            "gmail": "https://mail.google.com",
            "maps": "https://maps.google.com"
        }
        self.links = defaults
        self._save()
        return defaults

    def _save(self):
        try:
            with open(self.config_path, "w") as f:
                json.dump(self.links, f, indent=4)
        except Exception:
            pass

    def query(self, text: str):
        text = text.strip()
        if not text:
            return []

        results = []
        
        from PyQt6.QtWidgets import QApplication, QStyle
        style = QApplication.style()
        icon = style.standardIcon(QStyle.StandardPixmap.SP_CommandLink)

        # Interactive UI logic: "add link <keyword> <url>"
        if text.lower().startswith("add link "):
            parts = text[9:].split(" ", 1)
            if len(parts) == 2:
                keyword, url = parts[0].lower(), parts[1]
                if not url.startswith("http"):
                    url = "https://" + url
                
                results.append(SearchResult(
                    title=f"Create Link: {keyword}",
                    subtitle=f"Map keyword '{keyword}' to {url}",
                    icon=style.standardIcon(QStyle.StandardPixmap.SP_FileIcon),
                    score=300, # Highest score to beat web search fallbacks
                    action=lambda k=keyword, u=url: self.add_link(k, u)
                ))
            else:
                results.append(SearchResult(
                    title="Add a custom Quicklink",
                    subtitle="Format: add link <keyword> <url>",
                    icon=style.standardIcon(QStyle.StandardPixmap.SP_FileIcon),
                    score=150,
                    action=None
                ))
            return results

        # Scan for existing mapped links
        text_lower = text.lower()
        for kw, url in self.links.items():
            if kw == text_lower:
                results.append(SearchResult(
                    title=f"Open {kw.capitalize()}",
                    subtitle=url,
                    icon=icon,
                    score=280,
                    action=lambda u=url: webbrowser.open(u)
                ))
            elif kw.startswith(text_lower):
                results.append(SearchResult(
                    title=f"Open {kw.capitalize()}",
                    subtitle=url,
                    icon=icon,
                    score=130,
                    action=lambda u=url: webbrowser.open(u)
                ))

        return results

    def add_link(self, keyword, url):
        self.links[keyword] = url
        self._save()
        
        from PyQt6.QtWidgets import QMessageBox
        msg = QMessageBox()
        msg.setWindowTitle("Quicklink Created")
        msg.setText(f"Success! Typing '{keyword}' will now instantly launch {url}.")
        msg.exec()
