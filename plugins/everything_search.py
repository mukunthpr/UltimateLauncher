import os
import subprocess
from plugins.base_plugin import PluginBase, SearchResult
from PyQt6.QtWidgets import QFileIconProvider
from PyQt6.QtCore import QFileInfo

class EverythingSearchPlugin(PluginBase):
    id = "everything_search"
    name = "Everything File Search"
    prefix_alias = "f"

    def query(self, text: str):
        text = text.strip()
        if len(text) < 2:
            return []
            
        is_explicit = False
        text_lower = text.lower()
        if text_lower.startswith("f ") or text_lower.startswith("file ") or text_lower.startswith("find "):
            is_explicit = True
            if text_lower.startswith("file ") or text_lower.startswith("find "):
                search_query = text[5:].strip()
            else:
                search_query = text[2:].strip()
                
            if len(search_query) < 2:
                return []
        else:
            search_query = text
            
        results = []
        provider = QFileIconProvider()
        
        limit = "15" if is_explicit else "4"
        score_base = 95 if is_explicit else 70
        
        try:
            # Dynamic output limits based on explicit vs implicit searching
            CREATE_NO_WINDOW = 0x08000000
            
            # Everything 1.5a fallback logic
            proc = subprocess.run(["es", search_query, "-n", limit], 
                                  capture_output=True, text=True, creationflags=CREATE_NO_WINDOW, timeout=1.0)
            if "Error 8" in proc.stderr or not proc.stdout.strip():
                proc = subprocess.run(["es", search_query, "-instance", "1.5a", "-n", limit], 
                                      capture_output=True, text=True, creationflags=CREATE_NO_WINDOW, timeout=1.0)
                                  
            if proc.stdout:
                lines = proc.stdout.strip().split('\n')
                for line in lines:
                    path = line.strip()
                    if not path or not os.path.exists(path):
                        continue
                    
                    # Filter out noisy system/library paths in implicit mode
                    if not is_explicit:
                        path_lower = path.lower()
                        NOISE_PATHS = [
                            '\\python3', '\\python\\python', '\\lib\\', '\\site-packages\\',
                            '\\windows\\winsxs', '\\windows\\system32', '\\windows\\syswow64',
                            '\\appdata\\local\\temp', '\\appdata\\local\\programs\\python'
                        ]
                        if any(p in path_lower for p in NOISE_PATHS):
                            continue
                    
                    filename = os.path.basename(path)
                    icon = provider.icon(QFileInfo(path))
                    
                    basename_lower = os.path.splitext(filename)[0].lower()
                    query_lower = search_query.lower()
                    
                    dynamic_score = score_base
                    if query_lower == basename_lower:
                        dynamic_score = 110 # Absolute perfect match
                    elif query_lower in basename_lower:
                        ratio = len(query_lower) / max(1, len(basename_lower))
                        if ratio > 0.5:
                            dynamic_score = 106 + int(ratio * 3) # High confidence -> Beat Web Search Base (105)
                        else:
                            dynamic_score = 81 + int(ratio * 3) # Medium confidence -> Beat Loose Files, below Web Suggestions (87)
                    elif query_lower.replace(" ", "") in basename_lower.replace(" ", ""):
                        dynamic_score = 80 # Loose confidence -> Sent underneath Web Suggestions
                        
                    # Build contextual secondary actions natively
                    ctx_actions = [
                        {"name": "Open File Location", "action": lambda p=path: self.open_location(p)},
                        {"name": "Copy File Path", "action": lambda p=path: self.copy_path(p)}
                    ]
                        
                    results.append(SearchResult(
                        title=filename,
                        subtitle=path,
                        icon=icon,
                        score=dynamic_score,
                        action=lambda p=path: self.open_file(p),
                        context_actions=ctx_actions
                    ))
        except Exception as e:
            print(f"Everything Search error: {e}")
            
        return results

    def copy_path(self, path):
        import pyperclip
        pyperclip.copy(path)

    def open_location(self, path):
        import subprocess
        subprocess.run(['explorer', '/select,', path])

    def open_file(self, path):
        try:
            os.startfile(path)
        except Exception as e:
            print(f"Failed to open {path}: {e}")
