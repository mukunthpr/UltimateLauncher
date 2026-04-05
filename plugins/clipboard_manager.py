from PyQt6.QtWidgets import QApplication
from plugins.base_plugin import PluginBase, SearchResult
import threading
import time

class ClipboardPlugin(PluginBase):
    id = "clipboard"
    name = "Clipboard History"
    prefix_alias = "clip"

    def __init__(self):
        super().__init__()
        self.history = []
        
        # Subscribe to clipboard changes
        app = QApplication.instance()
        if app:
            clipboard = app.clipboard()
            clipboard.dataChanged.connect(self._on_clipboard_change)
            self._add_to_history(clipboard.text())

    def _on_clipboard_change(self):
        app = QApplication.instance()
        if app:
            text = app.clipboard().text()
            self._add_to_history(text)

    def _add_to_history(self, text):
        if not text: return
        text = text.strip()
        if not text: return
        
        # Remove if exists to jump to front
        if text in self.history:
            self.history.remove(text)
            
        self.history.insert(0, text)
        
        # Cap limits to 50 items memory to prevent RAM exhaustion
        if len(self.history) > 50:
            self.history.pop()

    def query(self, text: str):
        text = text.strip().lower()
        if not text:
            return []

        results = []
        is_explicit = text in ["clip", "clipboard", "clipboard history", "history"]
        
        from PyQt6.QtWidgets import QApplication, QStyle
        style = QApplication.style()
        icon = style.standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView)
        
        if is_explicit:
            # Show top 15 items immediately
            for idx, item in enumerate(self.history[:15]):
                display_title = item.replace('\n', ' ')
                if len(display_title) > 60:
                    display_title = display_title[:60] + "..."
                    
                ctx_actions = [
                    {"name": "Copy Without Pasting", "action": lambda t=item: self.copy_only(t)}
                ]
                
                results.append(SearchResult(
                    title=display_title,
                    subtitle="Clipboard History",
                    icon=self.icon,
                    score=150 + (100 if is_explicit else 0) - idx, # Adjusted score to include idx
                    action=lambda t=item: self.paste_item(t),
                    context_actions=ctx_actions
                ))
            return results
        
        # Implicit search against clipboard items linearly
        if len(text) > 2:
            for idx, item in enumerate(self.history):
                if text in item.lower():
                    display_title = item.replace('\n', ' ')
                    if len(display_title) > 60:
                        display_title = display_title[:60] + "..."
                        
                    results.append(SearchResult(
                        title=display_title,
                        subtitle="Clipboard Match",
                        icon=self.icon,
                        score=150 - min(idx, 10),  # Score high enough to beat generic web searches
                        action=lambda t=item: self.paste_item(t)
                    ))
        
        return results

    def copy_only(self, text):
        from PyQt6.QtWidgets import QApplication
        try:
            self.last_clipboard = text
            app = QApplication.instance()
            if app:
                clipboard = app.clipboard()
                clipboard.dataChanged.disconnect(self._on_clipboard_change)
                clipboard.setText(text)
                clipboard.dataChanged.connect(self._on_clipboard_change)
            self._add_to_history(text)
        except Exception as e:
            print(f"Clipboard copy_only failed: {e}")

    def paste_item(self, text):
        # 1. Update system clipboard
        from PyQt6.QtWidgets import QApplication
        try:
            self.last_clipboard = text
            app = QApplication.instance()
            if app:
                clipboard = app.clipboard()
                clipboard.dataChanged.disconnect(self._on_clipboard_change)
                clipboard.setText(text)
                clipboard.dataChanged.connect(self._on_clipboard_change)
            self._add_to_history(text)
        except Exception as e:
            print(f"Clipboard paste_item (copy part) failed: {e}")
            return

        # 2. Simulate Ctrl+V to paste immediately into the actively focused window behind the launcher
        def _simulate_paste():
            # Let the LauncherWindow completely hide/steal focus back first
            time.sleep(0.15) 
            try:
                import keyboard
                keyboard.send('ctrl+v')
            except Exception as e:
                print(f"Clipboard paste simulation failed: {e}")
        
        threading.Thread(target=_simulate_paste, daemon=True).start()
