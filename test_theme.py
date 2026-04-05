from core.theme_manager import ThemeManager
from core.config import ConfigManager

cfg = ConfigManager()
tm = ThemeManager()
active = cfg.get("active_theme", "default.json")
print(f"Active Theme: {active}")
qss = tm.compile_theme(active)
print("QSS Output:")
print(qss)
