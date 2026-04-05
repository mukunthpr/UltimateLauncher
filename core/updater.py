import os
import json
import urllib.request
import zipfile
import tempfile
import shutil
import threading
from PyQt6.QtCore import QObject, pyqtSignal

class AutoUpdater(QObject):
    """
    Asynchronous GitHub API bridge that automatically polls repository Release tags.
    Selectively hot-swaps Python system execution scripts natively from `.zip` payloads
    without destroying the local memory configs or third party extensions.
    """
    update_available = pyqtSignal(str, str) # version, description
    update_finished = pyqtSignal(bool, str)

    def __init__(self, repo_identifier="Mukunth/UltimateLauncher"):
        super().__init__()
        self.repo = repo_identifier
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.version_file = os.path.join(self.base_dir, "version.json")

    def get_local_version(self):
        try:
            with open(self.version_file, "r") as f:
                return json.load(f).get("version", "0.0.0")
        except:
            return "0.0.0"

    def check_for_updates(self):
        def _check():
            try:
                url = f"https://api.github.com/repos/{self.repo}/releases/latest"
                req = urllib.request.Request(url, headers={'User-Agent': 'UltimateLauncher'})
                res = urllib.request.urlopen(req, timeout=5).read().decode('utf-8')
                data = json.loads(res)
                
                remote_version = data.get("tag_name", "0.0.0").replace("v", "")
                local_version = self.get_local_version().replace("v", "")
                
                if remote_version != local_version and remote_version != "0.0.0":
                    self.update_available.emit(remote_version, data.get("body", "Bug fixes and performance improvements."))
            except Exception:
                pass
        threading.Thread(target=_check, daemon=True).start()

    def install_update(self):
        def _install():
            try:
                url = f"https://api.github.com/repos/{self.repo}/releases/latest"
                req = urllib.request.Request(url, headers={'User-Agent': 'UltimateLauncher'})
                res = urllib.request.urlopen(req, timeout=5).read().decode('utf-8')
                data = json.loads(res)
                
                zip_url = data.get("zipball_url")
                if not zip_url:
                    self.update_finished.emit(False, "No binary `.zip` distribution payload found globally.")
                    return
                
                tmp_zip = os.path.join(tempfile.gettempdir(), "ultimatelauncher_payload.zip")
                req = urllib.request.Request(zip_url, headers={'User-Agent': 'UltimateLauncher'})
                with urllib.request.urlopen(req, timeout=20) as response, open(tmp_zip, 'wb') as f:
                    f.write(response.read())
                    
                tmp_extract = os.path.join(tempfile.gettempdir(), "ul_extract_phase")
                if os.path.exists(tmp_extract):
                    shutil.rmtree(tmp_extract)
                
                with zipfile.ZipFile(tmp_zip, 'r') as zf:
                    zf.extractall(tmp_extract)
                    
                # GitHub automatically mounts zipballs inside a wrapper child folder (e.g., Mukunth-UltimateLauncher-xyz)
                extracted_root = os.path.join(tmp_extract, os.listdir(tmp_extract)[0])
                
                # Recursively and selectively execute hot-file swaps overriding core system bounds
                for root, _, files in os.walk(extracted_root):
                    rel_dir = os.path.relpath(root, extracted_root)
                    target_dir = os.path.join(self.base_dir, rel_dir)
                    
                    if not os.path.exists(target_dir) and rel_dir != ".":
                        os.makedirs(target_dir)
                        
                    for file in files:
                        # Skip extremely volatile user-generated data environments natively
                        if file in ["config.json", "crash.log", ".gitignore", "version.json"]:
                            continue
                            
                        # Edge case: Avoid hot-swapping standard Community Extensions maliciously
                        if "plugins" in rel_dir.lower() and "Flow.Launcher.Plugin" in root:
                            continue
                            
                        src_file = os.path.join(root, file)
                        dst_file = os.path.join(target_dir, file)
                        shutil.copy2(src_file, dst_file)
                        
                # Update native OS version registry manually to prevent loops
                new_version = data.get("tag_name", "0.0.0").replace("v", "")
                with open(self.version_file, "w") as f:
                    json.dump({"version": new_version}, f, indent=4)
                    
                # Erase installation tracks preventing memory leakages
                shutil.rmtree(tmp_extract)
                os.remove(tmp_zip)
                
                self.update_finished.emit(True, "Update automatically deployed over live files successfully.")
            except Exception as e:
                self.update_finished.emit(False, str(e))
                
        threading.Thread(target=_install, daemon=True).start()
