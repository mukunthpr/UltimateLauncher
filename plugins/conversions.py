import re
from plugins.base_plugin import PluginBase, SearchResult

class ConversionsPlugin(PluginBase):
    id = "conversions"
    name = "Data Conversions"
    prefix_alias = "cv"

    def __init__(self):
        super().__init__()
        
        # Standard multiplication conversions
        self.factors = {
            "km": {"mile": 0.621371, "m": 1000, "cm": 100000},
            "mile": {"km": 1.60934, "m": 1609.34},
            "m": {"km": 0.001, "cm": 100, "foot": 3.28084, "yard": 1.09361},
            "cm": {"m": 0.01, "inch": 0.393701},
            "inch": {"cm": 2.54, "foot": 0.0833333},
            "foot": {"inch": 12, "m": 0.3048, "cm": 30.48},
            "yard": {"m": 0.9144, "foot": 3},
            
            "kg": {"lb": 2.20462, "g": 1000},
            "lb": {"kg": 0.453592},
            "g": {"kg": 0.001, "oz": 0.035274},
            "oz": {"g": 28.3495},
            
            "l": {"ml": 1000, "gallon": 0.264172},
            "ml": {"l": 0.001},
            "gallon": {"l": 3.78541}
        }
        
        # Normalize plurals
        self.aliases = {
            "miles": "mile",
            "meters": "m", "meter": "m",
            "kilometers": "km", "kilometer": "km",
            "centimeters": "cm", "centimeter": "cm",
            "inches": "inch",
            "feet": "foot", "ft": "foot",
            "yards": "yard", "yd": "yard",
            "kilograms": "kg", "kilogram": "kg",
            "pounds": "lb", "lbs": "lb",
            "grams": "g", "gram": "g",
            "ounces": "oz", "ounce": "oz",
            "liters": "l", "liter": "l",
            "milliliters": "ml", "milliliter": "ml",
            "gallons": "gallon", "gal": "gallon"
        }

    def query(self, text: str):
        text = text.strip().lower()
        
        # Patterns: "100 km to miles", "10 kg in lbs"
        match = re.match(r"^([\d\.]+)\s*([a-z]+)\s*(to|in)\s*([a-z]+)$", text)
        if not match:
            return []

        try:
            val = float(match.group(1))
            unit_from = match.group(2)
            unit_to = match.group(4)
            
            # Resolve aliases
            unit_from = self.aliases.get(unit_from, unit_from)
            unit_to = self.aliases.get(unit_to, unit_to)
            
            if unit_from == 'c' and unit_to == 'f':
                ans = (val * 9/5) + 32
                formatted = f"{ans:.2f} °F"
            elif unit_from == 'f' and unit_to == 'c':
                ans = (val - 32) * 5/9
                formatted = f"{ans:.2f} °C"
            elif unit_from in self.factors and unit_to in self.factors[unit_from]:
                ans = val * self.factors[unit_from][unit_to]
                # Format smartly (drop .00 if integer)
                if ans.is_integer():
                    formatted = f"{int(ans)} {unit_to}"
                else:
                    formatted = f"{ans:.4f} {unit_to}".rstrip('0').rstrip('.') + f" {unit_to}"
            else:
                return []
                
            from PyQt6.QtWidgets import QApplication, QStyle
            style = QApplication.style()

            return [SearchResult(
                title=formatted,
                subtitle=f"Conversion: {val} {unit_from} = {formatted}",
                icon=style.standardIcon(QStyle.StandardPixmap.SP_MessageBoxInformation),
                score=210, # Super high so it beats web search
                action=lambda a=formatted: self.copy_to_clipboard(a.split()[0])
            )]

        except Exception:
            return []

    def copy_to_clipboard(self, value):
        from PyQt6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(str(value))
