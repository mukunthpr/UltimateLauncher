import os
import json
import xml.etree.ElementTree as ET
from urllib import request

class ThemeManager:
    def __init__(self, config_manager=None):
        self.config = config_manager
        
        # Core directories
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.themes_dir = os.path.join(self.base_dir, "themes")
        if not os.path.exists(self.themes_dir):
            os.makedirs(self.themes_dir)

    def fetch_flow_themes(self):
        """Fetch popular Flow Launcher themes from GitHub or local directory"""
        # For simplicity, we can load local .xaml themes dumped by users
        themes = []
        for filename in os.listdir(self.themes_dir):
            if filename.endswith(".xaml") or filename.endswith(".json"):
                themes.append(filename)
        return themes

    def compile_theme(self, theme_filename):
        """Converts Flow Launcher XAML/JSON dicts into active PyQt styles"""
        theme_path = os.path.join(self.themes_dir, theme_filename)
        if not os.path.exists(theme_path):
            return ""
            
        colors = {
            "WindowBackground": "#1e1e1e",
            "ItemTitleColor": "#FFFFFF",
            "ItemSubTitleColor": "#8C8C8C",
            "ItemSelectedBackground": "rgba(255, 255, 255, 25)",
            "BorderColor": "rgba(255, 255, 255, 30)",
            "SearchBackground": "transparent"
        }
        
        def _to_solid(c):
            # WPF Themes utilize #AARRGGBB for acrylic masking. Since we use Qt Window masking,
            # we must mathematically strip the alpha layer to cast solid arrays.
            if c.startswith("#") and len(c) == 9:
                return "#" + c[3:]
            return c
        
        try:
            if theme_filename.endswith(".xaml"):
                tree = ET.parse(theme_path)
                root = tree.getroot()
                
                ns = {'xaml': 'http://schemas.microsoft.com/winfx/2006/xaml/presentation', 
                      'x': 'http://schemas.microsoft.com/winfx/2006/xaml'}
                
                # Extract SolidColorBrush (e.g. ItemSelectedBackgroundColor)
                for brush in root.findall('.//xaml:SolidColorBrush', ns):
                    key = brush.get('{http://schemas.microsoft.com/winfx/2006/xaml}Key')
                    if key == "ItemSelectedBackgroundColor" and brush.text:
                        colors["ItemSelectedBackground"] = _to_solid(brush.text.strip())
                        
                # Extract complex Style block matrices
                for style in root.findall('.//xaml:Style', ns):
                    key = style.get('{http://schemas.microsoft.com/winfx/2006/xaml}Key')
                    if key == "WindowBorderStyle":
                        for setter in style.findall('.//xaml:Setter', ns):
                            if setter.get('Property') == 'Background':
                                colors["WindowBackground"] = _to_solid(setter.get('Value', colors["WindowBackground"]))
                            elif setter.get('Property') == 'BorderBrush':
                                colors["BorderColor"] = _to_solid(setter.get('Value', colors["BorderColor"]))
                    elif key == "ItemTitleStyle":
                        for setter in style.findall('.//xaml:Setter', ns):
                            if setter.get('Property') == 'Foreground':
                                colors["ItemTitleColor"] = _to_solid(setter.get('Value', colors["ItemTitleColor"]))
                    elif key == "ItemSubTitleStyle":
                        for setter in style.findall('.//xaml:Setter', ns):
                            if setter.get('Property') == 'Foreground':
                                colors["ItemSubTitleColor"] = _to_solid(setter.get('Value', colors["ItemSubTitleColor"]))
                    elif key == "ItemTitleSelectedStyle":
                        for setter in style.findall('.//xaml:Setter', ns):
                            if setter.get('Property') == 'Foreground':
                                colors["ItemTitleSelectedStyle"] = _to_solid(setter.get('Value', colors.get("ItemTitleColor", "#FFF")))
                    elif key == "ItemSubTitleSelectedStyle":
                        for setter in style.findall('.//xaml:Setter', ns):
                            if setter.get('Property') == 'Foreground':
                                colors["ItemSubTitleSelectedStyle"] = _to_solid(setter.get('Value', colors.get("ItemSubTitleColor", "#8C8C8C")))
                    elif key == "QueryBoxStyle":
                        for setter in style.findall('.//xaml:Setter', ns):
                            if setter.get('Property') == 'Foreground':
                                colors["ItemTitleColor"] = _to_solid(setter.get('Value', colors["ItemTitleColor"]))
                        
            elif theme_filename.endswith(".json"):
                with open(theme_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for k, v in data.items():
                        if k in colors:
                            colors[k] = _to_solid(v)
        except Exception as e:
            print(f"Failed parsing XAML Theme: {e}")
            
        qss = f"""
            * {{
                font-family: 'Inter', 'Segoe UI', sans-serif;
            }}
            LauncherWindow {{
                background: transparent;
            }}
            QWidget#MainContainer {{
                background-color: {colors.get('WindowBackground', '#1e1e1e')};
                border-radius: 12px;
                border: 1px solid {colors.get('BorderColor', 'rgba(255, 255, 255, 30)')};
            }}
            QLineEdit#SearchBox {{
                background: {colors.get('SearchBoxBackground', 'transparent')};
                border: none;
                outline: none;
                color: {colors.get('ItemTitleColor', '#FFFFFF')};
            }}
            QListWidget {{
                background: transparent;
                border: none;
                outline: none;
            }}
            QListWidget::item {{
                background: transparent;
                border-radius: 8px;
            }}
            QListWidget::item:selected {{
                background-color: {colors.get('ItemSelectedBackground', 'rgba(255, 255, 255, 25)')};
            }}
            QLabel[item_type="title"] {{
                color: {colors.get('ItemTitleColor', '#FFFFFF')};
            }}
            QLabel[item_type="subtitle"], QLabel[item_type="trait"] {{
                color: {colors.get('ItemSubTitleColor', '#8C8C8C')};
            }}
            QListWidget::item:selected QLabel[item_type="title"] {{
                color: {colors.get('ItemTitleSelectedStyle', colors.get('ItemTitleColor', '#FFFFFF'))};
            }}
            QListWidget::item:selected QLabel[item_type="subtitle"], QListWidget::item:selected QLabel[item_type="trait"] {{
                color: {colors.get('ItemSubTitleSelectedStyle', colors.get('ItemSubTitleColor', '#8C8C8C'))};
            }}
        """
        
        return qss
