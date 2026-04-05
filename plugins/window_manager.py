import ctypes
from plugins.base_plugin import PluginBase, SearchResult

user32 = ctypes.windll.user32

class RECT(ctypes.Structure):
    _fields_ = [
        ('left', ctypes.c_long),
        ('top', ctypes.c_long),
        ('right', ctypes.c_long),
        ('bottom', ctypes.c_long)
    ]

# Helper structs and constants
class MONITORINFO(ctypes.Structure):
    _fields_ = [
        ('cbSize', ctypes.c_ulong),
        ('rcMonitor', RECT),
        ('rcWork', RECT),
        ('dwFlags', ctypes.c_ulong)
    ]

class WindowManagerPlugin(PluginBase):
    id = "window_manager"
    name = "Window Management"

    def __init__(self):
        super().__init__()
        self.commands = [
            {"aliases": ["maximize window", "full screen window"], "title": "Maximize Window", "mode": "maximize"},
            {"aliases": ["center window", "middle window"], "title": "Center Window", "mode": "center"},
            {"aliases": ["left half", "snap left"], "title": "Left Half", "mode": "left"},
            {"aliases": ["right half", "snap right"], "title": "Right Half", "mode": "right"},
            {"aliases": ["top half", "snap top"], "title": "Top Half", "mode": "top"},
            {"aliases": ["bottom half", "snap bottom"], "title": "Bottom Half", "mode": "bottom"},
        ]

    def query(self, text: str):
        text = text.strip().lower()
        if not text:
            return []

        from PyQt6.QtWidgets import QApplication, QStyle
        style = QApplication.style()
        icon = style.standardIcon(QStyle.StandardPixmap.SP_DesktopIcon)

        results = []
        is_wm_prefix = text == "wm" or text.startswith("wm ")
        search_term = text[3:].strip() if text.startswith("wm ") else text

        for cmd in self.commands:
            matched = False
            score = 0
            
            if is_wm_prefix and not search_term:
                score = 250
                matched = True
            else:
                for alias in cmd["aliases"]:
                    if search_term == alias:
                        score = 250 + (50 if is_wm_prefix else 0)
                        matched = True
                        break
                    elif search_term in alias:
                        score = 120 + (100 if is_wm_prefix else 0)
                        matched = True
                        break

            if matched:
                results.append(SearchResult(
                    title=f"WM: {cmd['title']}",
                    subtitle=f"Resize the active window to {cmd['title']}",
                    icon=icon,
                    score=score,
                    action=lambda m=cmd["mode"]: self.snap_window(m)
                ))
                
        return results

    def get_target_window(self):
        hwnd_launcher = user32.GetForegroundWindow()
        hwnd = user32.GetWindow(hwnd_launcher, 2) # GW_HWNDNEXT
        while hwnd:
            if user32.IsWindowVisible(hwnd) and not user32.IsIconic(hwnd):
                length = user32.GetWindowTextLengthW(hwnd)
                if length > 0:
                    return hwnd
            hwnd = user32.GetWindow(hwnd, 2)
        return None

    def snap_window(self, mode):
        hwnd = self.get_target_window()
        if not hwnd: return
        
        # SW_RESTORE = 9
        user32.ShowWindow(hwnd, 9)
        
        # Get Work Area (excluding taskbar)
        hmonitor = user32.MonitorFromWindow(hwnd, 2) # MONITOR_DEFAULTTONEAREST
        mi = MONITORINFO()
        mi.cbSize = ctypes.sizeof(MONITORINFO)
        user32.GetMonitorInfoW(hmonitor, ctypes.byref(mi))
        
        work_rect = mi.rcWork
        w = work_rect.right - work_rect.left
        h = work_rect.bottom - work_rect.top
        x = work_rect.left
        y = work_rect.top
        
        if mode == "maximize":
            # SW_MAXIMIZE = 3
            user32.ShowWindow(hwnd, 3)
            return
        elif mode == "center":
            nw, nh = int(w * 0.7), int(h * 0.7)
            nx, ny = x + (w - nw) // 2, y + (h - nh) // 2
        elif mode == "left":
            nx, ny, nw, nh = x, y, w // 2, h
        elif mode == "right":
            nx, ny, nw, nh = x + w // 2, y, w // 2, h
        elif mode == "top":
            nx, ny, nw, nh = x, y, w, h // 2
        elif mode == "bottom":
            nx, ny, nw, nh = x, y + h // 2, w, h // 2
            
        # SWP_NOZORDER = 0x0004
        user32.SetWindowPos(hwnd, 0, nx, ny, nw, nh, 0x0004)
