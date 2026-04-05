import os
import json
import urllib.request
import zipfile
import tempfile
import threading

class FlowStoreAPI:
    """
    Direct interface to the official Flow Launcher GitHub Plugin Manifest.
    Responsible for fetching the registry JSON and securely extracting community 
    packages locally into the UltimateLauncher extension directory.
    """
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.plugins_dir = os.path.join(self.base_dir, "plugins")
        self.manifest_url = "https://raw.githubusercontent.com/Flow-Launcher/Flow.Launcher.PluginsManifest/plugin_api_v2/plugins.json"

    def fetch_manifest(self):
        """Pulls the entire live registry payload from GitHub."""
        try:
            req = urllib.request.Request(
                self.manifest_url, 
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            )
            data = urllib.request.urlopen(req, timeout=5).read().decode('utf-8')
            return json.loads(data)
        except Exception as e:
            print(f"Failed to fetch Flow Store manifest: {e}")
            return []

    def install_plugin_async(self, plugin_meta, callback):
        """Asynchronously downloads a ZIP payload and unpacks it natively to /plugins."""
        def _installer():
            try:
                download_url = plugin_meta.get("UrlDownload")
                plugin_id = plugin_meta.get("ID")
                
                if not download_url or not plugin_id:
                    callback(False, "Invalid manifest endpoints detected.")
                    return
                    
                temp_zip = os.path.join(tempfile.gettempdir(), f"{plugin_id}.zip")
                
                # Download
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
                }
                req = urllib.request.Request(download_url, headers=headers)
                with urllib.request.urlopen(req, timeout=15) as response, open(temp_zip, 'wb') as out_file:
                    out_file.write(response.read())
                    
                # Setup Extraction Target bounds
                target_dir = os.path.join(self.plugins_dir, f"Flow.Launcher.Plugin.{plugin_id}")
                if not os.path.exists(target_dir):
                    os.makedirs(target_dir)
                    
                # Unzip payloads
                with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
                    zip_ref.extractall(target_dir)
                    
                # Walk down the root recursively to natively compile requirements!
                import sys
                import subprocess
                for root, dirs, files in os.walk(target_dir):
                    if "requirements.txt" in files:
                        req_path = os.path.join(root, "requirements.txt")
                        try:
                            # Isolate stdout and map execution gracefully to Python's nested venv 
                            subprocess.run(
                                [sys.executable, "-m", "pip", "install", "-r", req_path],
                                cwd=root,
                                capture_output=True,
                                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                            )
                        except Exception:
                            pass
                    
                # Clean up memory leak vectors
                try:
                    os.remove(temp_zip)
                except Exception:
                    pass
                    
                callback(True, f"Successfully unpacked Flow Package: {plugin_id}")
            except Exception as e:
                callback(False, str(e))
                
        threading.Thread(target=_installer, daemon=True).start()
