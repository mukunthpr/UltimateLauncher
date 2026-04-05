from dataclasses import dataclass, field
from typing import Callable, Any, List, Dict

@dataclass
class SearchResult:
    title: str
    subtitle: str = ""
    icon: Any = None
    action: Callable = None
    score: int = 0
    context_actions: List[Dict] = field(default_factory=list) # [{"name": "Copy", "icon": QIcon, "action": lambda}]
    is_calculator: bool = False
    query: str = ""

class PluginBase:
    # A unique identifier for the plugin
    id: str = "base"
    # A display name for the plugin
    name: str = "Base Plugin"
    # An optional strict prefix trigger for dedicated search
    prefix_alias: str = ""

    def query(self, text: str) -> list[SearchResult]:
        """Return a list of SearchResult objects matching the text."""
        return []
