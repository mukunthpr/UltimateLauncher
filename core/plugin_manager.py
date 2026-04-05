import os
import importlib.util
import inspect
from plugins.base_plugin import PluginBase

class PluginManager:
    def __init__(self, plugins_dir="plugins", config_mgr=None):
        self.plugins = []
        self.plugins_dir = plugins_dir
        self.config = config_mgr
        self.load_plugins()

    def load_plugins(self):
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        plugins_path = os.path.join(base_path, self.plugins_dir)
        
        if not os.path.exists(plugins_path):
            os.makedirs(plugins_path)
            # Create an empty __init__.py so it's a package
            with open(os.path.join(plugins_path, "__init__.py"), "w") as f:
                pass
            
        for filename in os.listdir(plugins_path):
            if filename.endswith(".py") and filename != "base_plugin.py" and filename != "__init__.py":
                filepath = os.path.join(plugins_path, filename)
                module_name = f"plugins.{filename[:-3]}"
                
                spec = importlib.util.spec_from_file_location(module_name, filepath)
                if spec and spec.loader:
                    try:
                        module = importlib.util.module_from_spec(spec)
                        # We must add it to sys.modules
                        import sys
                        sys.modules[module_name] = module
                        spec.loader.exec_module(module)
                        
                        for name, obj in inspect.getmembers(module):
                            if inspect.isclass(obj) and issubclass(obj, PluginBase) and obj is not PluginBase:
                                instance = obj()
                                # Preload prefix metadata natively from Config payload overrides
                                if self.config:
                                    overrides = self.config.get("plugins", {}).get(instance.id, {})
                                    if "prefix_alias" in overrides:
                                        instance.prefix_alias = overrides["prefix_alias"]
                                self.plugins.append(instance)
                                print(f"Loaded Native Plugin: {instance.name}")
                    except Exception as e:
                        print(f"Failed to load native plugin {filename}: {e}")
                        
            # Flow Launcher Ecosystem Support
            elif os.path.isdir(filepath):
                plugin_json_path = os.path.join(filepath, "plugin.json")
                if os.path.exists(plugin_json_path):
                    import json
                    from core.flow_json_rpc_bridge import FlowPluginBridge
                    try:
                        with open(plugin_json_path, "r", encoding="utf-8") as f:
                            flow_manifest = json.load(f)
                            
                        # Wrap the raw JSON into our highly advanced Proxy Class
                        bridge_instance = FlowPluginBridge(filepath, flow_manifest)
                        
                        # Apply local alias overrides
                        if self.config:
                            overrides = self.config.get("plugins", {}).get(bridge_instance.id, {})
                            if "prefix_alias" in overrides:
                                bridge_instance.prefix_alias = overrides["prefix_alias"]
                                
                        self.plugins.append(bridge_instance)
                        print(f"Loaded Flow Bridge Plugin: {bridge_instance.name}")
                    except Exception as e:
                        print(f"Failed to load Flow Plugin {filename}: {e}")

    def query(self, text: str):
        results = []
        if not text.strip():
            return results

        for plugin in self.plugins:
            # Respect user-defined GUI settings layout
            if self.config:
                is_enabled = self.config.get("plugins", {}).get(plugin.id, {}).get("enabled", True)
                if not is_enabled:
                    continue

            try:
                res = plugin.query(text)
                if res:
                    results.extend(res)
            except Exception as e:
                print(f"Plugin {plugin.name} error on query: {e}")
                
        # Sort by score descending
        results.sort(key=lambda x: x.score, reverse=True)
        return results
