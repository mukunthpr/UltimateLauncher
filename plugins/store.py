import os
import json
import urllib.request
import zipfile
import io
import threading
import sys
import subprocess
import shutil
from plugins.base_plugin import PluginBase, SearchResult

class PluginStore(PluginBase):
    id = "plugin_store"
    name = "Plugin Store"

    def __init__(self):
        self.manifest_url = "https://raw.githubusercontent.com/Flow-Launcher/Flow.Launcher.PluginsManifest/plugin_api_v2/plugins.json"
        self.plugins_data = []
        self.fetch_manifest()

    def fetch_manifest(self):
        def _fetch():
            try:
                req = urllib.request.Request(self.manifest_url, headers={'User-Agent': 'Mozilla/5.0 Plugin-Store'})
                with urllib.request.urlopen(req, timeout=5) as response:
                    data = response.read()
                    self.plugins_data = json.loads(data)
            except Exception as e:
                print(f"Failed to fetch plugin manifest: {e}")
        t = threading.Thread(target=_fetch, daemon=True)
        t.start()
        
    def query(self, text: str):
        if not text.startswith("pm "):
            return []
            
        search_query = text[3:].strip().lower()
        results = []
        
        for p in self.plugins_data:
            lang = p.get("Language", "").lower()
            if lang not in ["python", "python3"]:
                continue
                
            name = p.get("Name", "")
            desc = p.get("Description", "")
            
            if search_query in name.lower() or search_query in desc.lower():
                dl_url = p.get("UrlDownload")
                author = p.get("Author", "Unknown")
                version = p.get("Version", "")
                
                results.append(SearchResult(
                    title=f"Install: {name} v{version}",
                    subtitle=f"{author} - {desc}",
                    score=100 if search_query in name.lower() else 50,
                    action=lambda url=dl_url, n=name: self.install_plugin(url, n)
                ))
                
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:15]

    def install_plugin(self, url, name):
        if not url:
            print(f"No download URL for {name}")
            return
            
        def _download():
            try:
                print(f"Downloading {name} from {url}...")
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 Plugin-Store'})
                with urllib.request.urlopen(req, timeout=10) as response:
                    zip_data = response.read()
                    
                base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                flow_path = os.path.join(base_path, "flow_plugins")
                safe_name = "".join(x for x in name if x.isalnum() or x in " -_")
                plugin_dir = os.path.join(flow_path, safe_name)
                
                if not os.path.exists(plugin_dir):
                    os.makedirs(plugin_dir)
                    
                with zipfile.ZipFile(io.BytesIO(zip_data)) as z:
                    z.extractall(plugin_dir)
                    
                contents = os.listdir(plugin_dir)
                if len(contents) == 1 and os.path.isdir(os.path.join(plugin_dir, contents[0])):
                    sub_dir = os.path.join(plugin_dir, contents[0])
                    for item in os.listdir(sub_dir):
                        shutil.move(os.path.join(sub_dir, item), plugin_dir)
                    os.rmdir(sub_dir)
                    
                print(f"Successfully installed {name}!")
                
                req_file = os.path.join(plugin_dir, "requirements.txt")
                if os.path.exists(req_file):
                    CREATE_NO_WINDOW = 0x08000000
                    subprocess.run([sys.executable, "-m", "pip", "install", "-r", req_file], 
                                   capture_output=True, creationflags=CREATE_NO_WINDOW)
            except Exception as e:
                print(f"Failed to install {name}: {e}")
                
        threading.Thread(target=_download, daemon=True).start()
