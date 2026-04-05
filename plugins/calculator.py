from plugins.base_plugin import PluginBase, SearchResult
import re
from PyQt6.QtWidgets import QApplication, QStyle

class CalculatorPlugin(PluginBase):
    id = "calculator"
    name = "Calculator"

    def __init__(self):
        # Allow basic math characters only
        self.math_regex = re.compile(r'^[0-9+\-*/().\s]+$')

    def query(self, text: str):
        text_lower = text.strip().lower()
        if not text_lower:
            return []

        is_calc_prefix = text_lower.startswith("calc ")
        if is_calc_prefix:
            text = text_lower[5:].strip()

        if not self.math_regex.match(text):
            return []

        try:
            # Safely evaluate simple math
            result = eval(text, {"__builtins__": None}, {})
            # Only valid numbers
            if isinstance(result, (int, float)):
                if isinstance(result, float) and result.is_integer():
                    res_str = str(int(result))
                else:
                    res_str = str(result)
        except Exception:
            # Retain the massive Calculator visual layout dynamically if trailing operators exist
            if any(op in text for op in "+-*/()"):
                res_str = "..."
            else:
                return []
                
        style = QApplication.style()

        return [
            SearchResult(
                title=res_str,
                subtitle=f"Calculation: {text}",
                icon=style.standardIcon(QStyle.StandardPixmap.SP_MessageBoxInformation),
                score=250 + (50 if is_calc_prefix else 0), # Massive boost to ensure math suppresses file matches mid-type
                action=lambda text=res_str: self.copy_to_clipboard(text) if text != "..." else None,
                is_calculator=True,
                query=text
            )
        ]

    def copy_to_clipboard(self, text):
        QApplication.clipboard().setText(text)
