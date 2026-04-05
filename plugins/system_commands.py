import os
import ctypes
from plugins.base_plugin import PluginBase, SearchResult

class SystemCommandsPlugin(PluginBase):
    id = "system_commands"
    name = "System Commands"
    prefix_alias = "sys"

    def __init__(self):
        super().__init__()
        
        self.commands = [
            {
                "aliases": ["sleep", "suspend"],
                "title": "Sleep",
                "subtitle": "Put the computer to sleep",
                "action": self.sleep_pc
            },
            {
                "aliases": ["lock", "lock screen"],
                "title": "Lock Screen",
                "subtitle": "Lock the workstation",
                "action": self.lock_pc
            },
            {
                "aliases": ["shutdown", "turn off"],
                "title": "Shutdown",
                "subtitle": "Turn off the computer",
                "action": self.shutdown_pc
            },
            {
                "aliases": ["restart", "reboot"],
                "title": "Restart",
                "subtitle": "Restart the computer",
                "action": self.restart_pc
            },
            {
                "aliases": ["empty recycle bin", "empty trash"],
                "title": "Empty Recycle Bin",
                "subtitle": "Permanently delete files in the Recycle Bin",
                "action": self.empty_recycle_bin
            },
            {
                "aliases": ["volume up", "louder"],
                "title": "Volume Up",
                "subtitle": "Increase system volume",
                "action": lambda: self.adjust_volume(0xAF)
            },
            {
                "aliases": ["volume down", "quieter"],
                "title": "Volume Down",
                "subtitle": "Decrease system volume",
                "action": lambda: self.adjust_volume(0xAE)
            },
            {
                "aliases": ["mute", "mute volume"],
                "title": "Mute Volume",
                "subtitle": "Toggle system volume mute",
                "action": lambda: self.adjust_volume(0xAD)
            }
        ]

    def query(self, text: str):
        text = text.strip().lower()
        if not text:
            return []

        from PyQt6.QtWidgets import QApplication, QStyle
        style = QApplication.style()

        def get_icon(title):
            if "Sleep" in title or "Lock" in title:
                return style.standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
            elif "Shutdown" in title or "Restart" in title:
                return style.standardIcon(QStyle.StandardPixmap.SP_BrowserReload)
            elif "Volume" in title:
                return style.standardIcon(QStyle.StandardPixmap.SP_MediaVolume)
            elif "Bin" in title:
                return style.standardIcon(QStyle.StandardPixmap.SP_TrashIcon)
            return style.standardIcon(QStyle.StandardPixmap.SP_DriveHDIcon)

        results = []
        is_sys_prefix = text in ["sys", "system"] or text.startswith("sys ") or text.startswith("system ")
        
        if text.startswith("system "):
            search_term = text[7:].strip()
        elif text.startswith("sys "):
            search_term = text[4:].strip()
        else:
            search_term = text

        for cmd in self.commands:
            matched = False
            score = 0
            
            if is_sys_prefix and not search_term:
                matched = True
                score = 300
            else:
                for alias in cmd["aliases"]:
                    if search_term == alias:
                        matched = True
                        score = 300 + (50 if is_sys_prefix else 0)
                        break
                    elif search_term in alias:
                        matched = True
                        score = 150 + (100 if is_sys_prefix else 0)
                        break
            
            if matched:
                results.append(SearchResult(
                    title=f"SYS: {cmd['title']}",
                    subtitle=cmd["subtitle"],
                    icon=get_icon(cmd["title"]),
                    score=score,
                    action=cmd["action"]
                ))
        return results

    def sleep_pc(self):
        os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")

    def lock_pc(self):
        ctypes.windll.user32.LockWorkStation()

    def shutdown_pc(self):
        os.system("shutdown /s /t 0")

    def restart_pc(self):
        os.system("shutdown /r /t 0")

    def empty_recycle_bin(self):
        # SHERB_NOCONFIRMATION = 1, SHERB_NOPROGRESSUI = 2, SHERB_NOSOUND = 4 => 7
        try:
            result = ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 7)
            if result != 0:
                print("Recycle Bin is already empty or failed to empty.")
        except Exception as e:
            print(f"Failed to empty recycle bin: {e}")

    def adjust_volume(self, vk_code):
        # Sends a virtual keystroke corresponding to volumetric media keys
        user32 = ctypes.windll.user32
        user32.keybd_event(vk_code, 0, 0, 0)     # Key Down
        user32.keybd_event(vk_code, 0, 2, 0)     # Key Up
