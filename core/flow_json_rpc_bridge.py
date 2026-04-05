import os
import sys
import json
import subprocess
import threading
from plugins.base_plugin import PluginBase, SearchResult

class FlowPluginBridge(PluginBase):
    """
    A dynamically generated wrapper that acts precisely as a native PluginBase object,
    but proxies queries over JSON-RPC via STDIN/STDOUT to a sandboxed Flow Launcher plugin.
    """
    def __init__(self, plugin_dir, flow_json):
        super().__init__()
        self.plugin_dir = plugin_dir
        
        self.id = flow_json.get("ID", os.path.basename(plugin_dir))
        self.name = flow_json.get("Name", "Flow Plugin")
        self.prefix_alias = flow_json.get("ActionKeyword", "")
        self.description = flow_json.get("Description", "")
        self.executable = flow_json.get("ExecuteFileName", "")
        self.language = flow_json.get("Language", "python")
        
        # Resolve absolute graphical icon paths relative to the plugin sandbox
        icon_path = flow_json.get("IcoPath", "")
        self.resolved_icon = os.path.join(self.plugin_dir, icon_path) if icon_path else None

    def _execute_rpc(self, method, parameters):
        if not self.executable:
            return []
            
        exe_path = os.path.join(self.plugin_dir, self.executable)
        if not os.path.exists(exe_path):
            print(f"[{self.name}] Proxy Failure: Cannot locate {exe_path}")
            return []
            
        cmd = []
        if self.language.lower() in ["python", "python3"]:
            # Use wrapped virtualenv Python scope if targeting a python plugin
            cmd.append(sys.executable)
        
        cmd.append(exe_path)
        
        # JSON-RPC 2.0 strictly requires ID correlation
        payload = {
            "method": method,
            "parameters": parameters,
            "jsonrpc": "2.0",
            "id": 1
        }
        
        try:
            # Spawn the isolated executable shell synchronously mapping our stringified JSON payloads
            proc = subprocess.Popen(
                cmd,
                cwd=self.plugin_dir,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            stdout, stderr = proc.communicate(input=json.dumps(payload), timeout=3.0)
            
            if proc.returncode != 0:
                print(f"[{self.name}] Bridge Error: {stderr}")
                return []
                
            response = json.loads(stdout)
            return response.get("result", [])
            
        except subprocess.TimeoutExpired:
            print(f"[{self.name}] Timeout: Plugin execution froze.")
        except Exception as e:
            print(f"[{self.name}] JSON-RPC Error: {e}")
            
        return []

    def query(self, text: str) -> list[SearchResult]:
        if not text:
            return []
            
        prefix = getattr(self, "prefix_alias", "").strip()
        query_text = text
        
        # In the Flow Launcher specification, plugins are only queried if their explicit ActionKeyword strictly matches (unless wildcarded)
        # Additionally, the API specification strictly mandates the prefix be stripped locally prior to forwarding the execution args
        if prefix and prefix != "*":
            if not text.lower().startswith(prefix.lower()):
                return []
            query_text = text[len(prefix):].strip()
            
        # Fire proxy
        raw_results = self._execute_rpc("query", [query_text])
        parsed = []
        
        for idx, item in enumerate(raw_results):
            # Translate Flow's JSON schema back into UltimateLauncher's PyQt native format
            title = item.get("Title", "")
            sub = item.get("SubTitle", "")
            icon = item.get("IcoPath", self.resolved_icon)
            if icon and not os.path.isabs(icon):
                icon = os.path.join(self.plugin_dir, icon)
                
            rpc_action = item.get("JsonRPCAction")
            
            # Map the primary executable callback to fire the secondary RPC method requested by the plugin
            action_lambda = None
            if rpc_action:
                act_method = rpc_action.get("method", "")
                act_params = rpc_action.get("parameters", [])
                
                # Capture variable state natively 
                def _invoke(m=act_method, p=act_params):
                    threading.Thread(target=self._execute_rpc, args=(m, p), daemon=True).start()
                action_lambda = _invoke
            
            parsed.append(SearchResult(
                title=title,
                subtitle=sub,
                icon=icon,
                score=200 - idx,  # Elevated score logic
                action=action_lambda
            ))
            
        return parsed
