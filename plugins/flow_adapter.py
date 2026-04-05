import os
import json
import sys
import subprocess
from plugins.base_plugin import PluginBase, SearchResult

class FlowAdapterPlugin(PluginBase):
    id = "flow_adapter"
    name = "FlowLauncher Adapter"

    def __init__(self):
        self.flow_plugins = []
        self.load_flow_plugins()

    def load_flow_plugins(self):
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # Find the flow_plugins directory
        flow_path = os.path.join(base_path, "flow_plugins")
        if not os.path.exists(flow_path):
            os.makedirs(flow_path)
            
        for folder in os.listdir(flow_path):
            plugin_dir = os.path.join(flow_path, folder)
            if os.path.isdir(plugin_dir):
                json_path = os.path.join(plugin_dir, "plugin.json")
                if os.path.exists(json_path):
                    with open(json_path, 'r', encoding='utf-8') as f:
                        try:
                            meta = json.load(f)
                            # Only execute Python FlowLauncher plugins for now
                            if meta.get("Language", "").lower() in ["python", "python3"]:
                                self.flow_plugins.append({
                                    "meta": meta,
                                    "dir": plugin_dir
                                })
                                print(f"Registered FlowLauncher Plugin: {meta.get('Name')}")
                        except Exception as e:
                            print(f"Failed parsing {json_path}: {e}")

    def query(self, text: str):
        if not text:
            return []

        all_results = []
        for p in self.flow_plugins:
            # Check ActionKeyword
            keyword = p["meta"].get("ActionKeyword", "")
            
            # Flow plugins trigger if keyword is '*' or text starts with keyword
            if keyword and keyword != "*":
                if not text.startswith(keyword):
                    continue
                # Slice off keyword mapping
                plugin_query = text[len(keyword):].strip()
            else:
                plugin_query = text
                
            req = {
                "method": "query",
                "parameters": [plugin_query]
            }
            
            res = self.execute_flow_plugin(p, req)
            if res and isinstance(res, dict) and "result" in res:
                for r in res["result"]:
                    # Create a closure for the JSON-RPC action on enter
                    action_def = r.get("JsonRPCAction")
                    def make_action(plugin_info, act_def):
                        if act_def:
                            return lambda: self.execute_flow_plugin(plugin_info, act_def)
                        return None
                        
                    ico_path = r.get("IcoPath", "")
                    full_ico_path = os.path.join(p["dir"], ico_path) if ico_path else None
                    if full_ico_path and not os.path.exists(full_ico_path):
                        full_ico_path = None
                        
                    all_results.append(SearchResult(
                        title=r.get("Title", ""),
                        subtitle=r.get("SubTitle", ""),
                        icon=full_ico_path,
                        score=80,  # Generic score for external plugins
                        action=make_action(p, action_def)
                    ))
        return all_results

    def execute_flow_plugin(self, plugin_info, req_obj):
        exec_file = plugin_info["meta"].get("ExecuteFileName")
        full_exec = os.path.join(plugin_info["dir"], exec_file)
        
        req_str = json.dumps(req_obj)
        
        lang = plugin_info["meta"].get("Language", "").lower()
        if lang in ["python", "python3"]:
            # Use UltimateLauncher's current python executable
            cmd = [sys.executable, full_exec, req_str]
        else:
            return {}
            
        try:
            CREATE_NO_WINDOW = 0x08000000
            # Set timeout low so slow Flow plugins don't freeze the main UI loop too long
            proc = subprocess.run(cmd, capture_output=True, text=True, cwd=plugin_info["dir"], 
                                  creationflags=CREATE_NO_WINDOW, timeout=2.0)
            if proc.stdout:
                return json.loads(proc.stdout)
        except Exception as e:
            print(f"Flow plugin error {plugin_info['meta'].get('Name')}: {e}")
        return {}
