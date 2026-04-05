from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QCheckBox, QLineEdit, QPushButton, 
                             QMessageBox, QScrollArea, QListWidget, QStackedWidget,
                             QListWidgetItem, QApplication, QFileDialog)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt6.QtGui import QFont, QPixmap, QIcon
import os
import sys
import winreg
import threading
import subprocess
from core.updater import AutoUpdater

class StoreFetcher(QObject):
    finished = pyqtSignal(list)
    def fetch(self):
        def _pull():
            try:
                from core.flow_store import FlowStoreAPI
                manifest = FlowStoreAPI().fetch_manifest()
                self.finished.emit(manifest)
            except:
                self.finished.emit([])
        threading.Thread(target=_pull, daemon=True).start()

class PluginInstallSignal(QObject):
    done = pyqtSignal(bool, str)

class SettingsWindow(QWidget):
    def __init__(self, config_manager, hotkey_manager, plugin_mgr=None):
        super().__init__()
        self.config_manager = config_manager
        self.hotkey_manager = hotkey_manager
        self.plugin_manager = plugin_mgr
        
        self.updater = AutoUpdater()
        self.updater.update_available.connect(self.on_update_available)
        self.updater.update_finished.connect(self.on_update_finished)
        
        self.setWindowTitle("Settings")
        self.setFixedSize(760, 520)
        self.setAttribute(Qt.WidgetAttribute.WA_QuitOnClose, False)
        
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "icon.png")
        self.setWindowIcon(QIcon(icon_path))
        
        self.reg_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        self.app_name = "Ultimate Launcher"

        self.init_ui()

    def _prompt_restart(self, title, message):
        from PyQt6.QtWidgets import QApplication
        import subprocess
        
        reply = QMessageBox.question(
            self, title, 
            message + "\n\nWould you like to automatically restart Ultimate Launcher now?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Mirror the active Python executable path and explicitly calculate the main script location
            main_script = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "main.py")
            subprocess.Popen([sys.executable, main_script])
            QApplication.quit()

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # --- Sidebar ---
        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(230)
        self.sidebar.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.sidebar.setStyleSheet("""
            QListWidget {
                background-color: #1a1a1a;
                border: none;
                border-right: 1px solid #2d2d2d;
                outline: none;
                padding: 10px 5px;
            }
            QListWidget::item {
                color: #e0e0e0;
                font-family: 'Inter', 'Segoe UI', sans-serif;
                font-size: 13px;
                font-weight: 500;
                padding: 8px 12px;
                border-radius: 6px;
                margin: 2px 5px;
            }
            QListWidget::item:selected {
                background-color: rgba(255, 255, 255, 25);
                color: white;
            }
            QListWidget::item:hover {
                background-color: rgba(255, 255, 255, 10);
            }
        """)
        
        # --- Content Stack ---
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("""
            QStackedWidget {
                background-color: #1e1e1e;
            }
            QLabel {
                color: #e0e0e0;
                font-family: 'Inter', 'Segoe UI', sans-serif;
                font-size: 13px;
            }
            QLineEdit {
                background: #111;
                border: 1px solid #333;
                color: white;
                padding: 8px;
                border-radius: 6px;
            }
            QPushButton {
                background: #2d2d2d;
                border: 1px solid #444;
                color: white;
                padding: 6px 12px;
                border-radius: 6px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: #3d3d3d;
            }
            QCheckBox {
                font-family: 'Inter', 'Segoe UI', sans-serif;
                font-size: 13px;
                color: white;
                font-weight: 500;
            }
            QCheckBox::indicator {
                width: 32px;
                height: 18px;
                border-radius: 9px;
            }
            QCheckBox::indicator:unchecked {
                background-color: #444;
            }
            QCheckBox::indicator:checked {
                background-color: #0A84FF;
            }
            QScrollArea {
                border: none;
                background: transparent;
            }
        """)
        
        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.stack)
        
        # --- Populate Core Pages ---
        self._add_sidebar_row("General", self._build_general_tab())
        self._add_sidebar_row("Keyboard & Shortcuts", self._build_shortcuts_tab())
        self._add_sidebar_row("Themes", self._build_themes_tab())
        self._add_sidebar_row("Plugin Store", self._build_store_tab())
        self._add_sidebar_row("Installed Extensions", self._build_installed_tab())
        self._add_sidebar_row("Advanced", self._build_advanced_tab())
        self._add_sidebar_row("About", self._build_about_tab())
                
        self.sidebar.currentRowChanged.connect(self.stack.setCurrentIndex)
        self.sidebar.setCurrentRow(0)

    def _add_sidebar_row(self, name, widget):
        item = QListWidgetItem(name)
        self.sidebar.addItem(item)
        self.stack.addWidget(widget)

    def on_update_available(self, version, desc):
        reply = QMessageBox.question(
            self,
            "Ultimate Launcher Update",
            f"A new version ({version}) has been deployed to GitHub.\n\nDescription:\n{desc}\n\nDo you want to securely fetch and install it now?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.settings_msg = QMessageBox(self)
            self.settings_msg.setWindowTitle("Updating")
            self.settings_msg.setText(f"Synchronizing payload bindings from native repository... Do not close Ultimate Launcher.")
            self.settings_msg.setStandardButtons(QMessageBox.StandardButton.NoButton)
            self.settings_msg.show()
            self.updater.install_update()

    def on_update_finished(self, success, msg):
        if hasattr(self, 'settings_msg'):
            self.settings_msg.accept()
            
        if success:
            self._prompt_restart("Update Complete", msg + "\n\nUltimate Launcher must execute an OS execution swap loop to map the newest logic gracefully. Proceed?")
        else:
            QMessageBox.critical(self, "Update Failed", msg)

    def _build_general_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Header
        title = QLabel("General")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: white;")
        layout.addWidget(title)
        
        # Option: Follow System Appearance (Dummy for Raycast UI parity)
        theme_box = self._create_row_toggle("Follow System Appearance", True)
        layout.addWidget(theme_box)
        
        # Option: Run on Startup
        startup_box = QWidget()
        sl = QHBoxLayout(startup_box)
        sl.setContentsMargins(0,0,0,0)
        sl.addWidget(QLabel("Open at Login"))
        self.startup_cb = QCheckBox()
        self.startup_cb.setChecked(self.config_manager.get("run_on_startup"))
        self.startup_cb.stateChanged.connect(self.on_startup_changed)
        sl.addStretch()
        sl.addWidget(self.startup_cb)
        layout.addWidget(startup_box)
        
        # Option: Hotkey
        hotkey_box = QWidget()
        hl = QHBoxLayout(hotkey_box)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.addWidget(QLabel("Raycast Hotkey"))
        hl.addStretch()
        self.hotkey_input = QLineEdit()
        self.hotkey_input.setText(self.config_manager.get("hotkey"))
        self.hotkey_input.setFixedWidth(120)
        hl.addWidget(self.hotkey_input)
        
        btn = QPushButton("Bind")
        btn.clicked.connect(self.apply_hotkey)
        hl.addWidget(btn)
        
        # Option: Automatic Updates
        update_box = QWidget()
        ul = QHBoxLayout(update_box)
        ul.setContentsMargins(0, 0, 0, 0)
        
        version_label = QLabel(f"Version: v{self.updater.get_local_version()}")
        version_label.setStyleSheet("color: #8C8C8C; font-size: 13px;")
        ul.addWidget(version_label)
        
        ul.addStretch()
        check_btn = QPushButton("Check for Updates")
        check_btn.setFixedWidth(130)
        check_btn.clicked.connect(self.updater.check_for_updates)
        ul.addWidget(check_btn)
        
        layout.addWidget(update_box)
        
        layout.addStretch()
        return page

    def _create_row_toggle(self, text, default_checked):
        box = QWidget()
        l = QHBoxLayout(box)
        l.setContentsMargins(0,0,0,0)
        l.addWidget(QLabel(text))
        l.addStretch()
        cb = QCheckBox()
        cb.setChecked(default_checked)
        l.addWidget(cb)
        return box

    def _build_shortcuts_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)
        
        title = QLabel("Keyboard & Shortcuts")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: white;")
        layout.addWidget(title)
        
        layout.addSpacing(15)
        layout.addWidget(QLabel("A 'Hyperkey' maps Caps Lock to (Ctrl + Shift + Alt + Win),\ngiving you a pristine modifier for Ultimate Launcher search natively."))
        
        layout.addSpacing(20)
        layout.addWidget(QLabel("To bind your Caps Lock to Hyperkey effortlessly:"))
        layout.addWidget(QLabel("1. Install 'Microsoft PowerToys' from the Microsoft Store."))
        layout.addWidget(QLabel("2. Open the 'Keyboard Manager' tool natively inside PowerToys."))
        layout.addWidget(QLabel("3. Remap a Key: Map 'Caps Lock' to 'Ctrl+Shift+Alt+Win'."))
        layout.addWidget(QLabel("4. In General Tab above, set the activation shortcut to 'hyper'."))
        
        layout.addStretch()
        return page
        
    def _build_themes_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)
        
        title = QLabel("Application Themes")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: white;")
        layout.addWidget(title)
        
        from core.theme_manager import ThemeManager
        tm = ThemeManager()
        available_themes = tm.fetch_flow_themes()
        
        layout.addWidget(QLabel("Select a live WPF (.xaml) or JSON style blueprint:"))
        self.theme_list = QListWidget()
        self.theme_list.setStyleSheet("background: #111; border: 1px solid #333; border-radius: 6px; outline: none; padding: 5px;")
        self.theme_list.addItems(available_themes)
        
        curr = self.config_manager.get("active_theme", "default.json")
        for i in range(self.theme_list.count()):
            if self.theme_list.item(i).text() == curr:
                self.theme_list.setCurrentRow(i)
                break
                
        apply_btn = QPushButton("Apply Active Theme")
        apply_btn.clicked.connect(self._apply_theme)
        
        import_btn = QPushButton("Import Custom Theme")
        import_btn.clicked.connect(self._import_theme)
        
        layout.addWidget(self.theme_list)
        layout.addWidget(apply_btn)
        layout.addWidget(import_btn)
        return page

    def _apply_theme(self):
        item = self.theme_list.currentItem()
        if item:
            theme_name = item.text()
            self.config_manager.set("active_theme", theme_name)
            self._prompt_restart("Theme Applied", f"Active theme implicitly updated to '{theme_name}'.")

    def _import_theme(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Import Flow Theme", "", "Theme Files (*.xaml *.json)")
        if file_path:
            try:
                import shutil
                theme_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "themes")
                if not os.path.exists(theme_dir):
                    os.makedirs(theme_dir)
                dist = os.path.join(theme_dir, os.path.basename(file_path))
                shutil.copy2(file_path, dist)
                
                self.theme_list.addItem(os.path.basename(file_path))
                QMessageBox.information(self, "Theme Imported", f"Successfully linked {os.path.basename(file_path)} into the execution tree.")
            except Exception as e:
                QMessageBox.critical(self, "Import Failed", f"Critical disk failure while bypassing: {e}")

    def _build_store_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 20, 30, 20)
        
        title = QLabel("Plugin Store")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: white;")
        layout.addWidget(title)
        
        layout.addWidget(QLabel("Fetch third-party extensions seamlessly from the open-source repository."))
        
        self.store_list = QScrollArea()
        self.store_list.setWidgetResizable(True)
        self.store_content = QWidget()
        self.store_layout = QVBoxLayout(self.store_content)
        self.store_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.store_list.setWidget(self.store_content)
        layout.addWidget(self.store_list)
        
        self.fetch_btn = QPushButton("Refresh GitHub Manifest")
        self.store_fetcher = StoreFetcher()
        self.store_fetcher.finished.connect(self._on_store_manifest_ready)
        
        self.fetch_btn.clicked.connect(self._start_store_fetch)
        layout.addWidget(self.fetch_btn)
        
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(50, self._start_store_fetch)
        
        return page

    def _start_store_fetch(self):
        self.fetch_btn.setText("Fetching Manifest...")
        self.fetch_btn.setEnabled(False)
        self.store_fetcher.fetch()

    def _on_store_manifest_ready(self, manifest):
        self.fetch_btn.setText("Refresh GitHub Manifest")
        self.fetch_btn.setEnabled(True)
        
        # Clear layout safely on main thread
        for i in reversed(range(self.store_layout.count())): 
            w = self.store_layout.itemAt(i).widget()
            if w:
                w.setParent(None)
                w.deleteLater()
                
        if not manifest:
            self.store_layout.addWidget(QLabel("Failed to fetch manifest API. Check internet latency."))
            return
            
        for p in manifest:
            # Ultimate Launcher JSON-RPC bridge currently strictly supports out-of-process Python executables natively, 
            # dynamically filtering out compiled C# .dll reflection modules.
            if p.get("Language", "").lower() not in ["python", "python3"]:
                continue
                
            card = QWidget()
            card.setStyleSheet("background: #252525; padding: 12px; border-radius: 8px;")
            cl = QHBoxLayout(card)
            cl.setContentsMargins(10,5,10,5)
            
            info = QVBoxLayout()
            n = QLabel(p.get("Name", "Unknown Plugin"))
            n.setStyleSheet("font-weight: 600; font-size: 14px; color: white;")
            d = QLabel(p.get("Description", "")[:60] + "...")
            d.setStyleSheet("color: #8C8C8C; font-size: 11px;")
            info.addWidget(n)
            info.addWidget(d)
            
            dl_btn = QPushButton("Install")
            
            proxy = PluginInstallSignal()
            def _handle_result(success, msg, btn=dl_btn):
                if success:
                    btn.setText("Installed")
                    self._prompt_restart("Plugin Installed", "The package was successfully extracted natively.")
                else:
                    btn.setText("Failed")
                    QMessageBox.critical(self, "Download Failed", f"The original Flow Registry API target is broken natively or actively rejecting connections:\n\n{msg}")
            
            proxy.done.connect(_handle_result)
            
            def _install_curried(checked=False, meta=p, btn=dl_btn, px=proxy):
                btn.setText("Downloading...")
                btn.setEnabled(False)
                from core.flow_store import FlowStoreAPI
                fs = FlowStoreAPI()
                def _cb(success, msg):
                    px.done.emit(success, msg)
                fs.install_plugin_async(meta, _cb)
                
            dl_btn.clicked.connect(_install_curried)
            
            cl.addLayout(info)
            cl.addStretch()
            cl.addWidget(dl_btn)
            self.store_layout.addWidget(card)

    def _build_advanced_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)
        
        title = QLabel("Advanced")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: white;")
        layout.addWidget(title)
        
        purge_clip_btn = QPushButton("Purge Clipboard Memory (RAM)")
        purge_clip_btn.setFixedWidth(250)
        purge_clip_btn.clicked.connect(self._purge_clipboard_memory)
        layout.addWidget(purge_clip_btn)
        
        layout.addStretch()
        return page

    def _purge_clipboard_memory(self):
        if self.plugin_manager:
            for p in self.plugin_manager.plugins:
                if p.id == "clipboard":
                    p.history = []
                    QMessageBox.information(self, "Memory Flushed", "In-memory clipboard structures completely purged.")
                    return
        QMessageBox.warning(self, "Error", "Clipboard Plugin unhooked.")

    def _build_about_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Load and display logo
        logo_label = QLabel()
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "icon.png")
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path).scaled(80, 80, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            logo_label.setPixmap(pixmap)
        layout.addWidget(logo_label)

        title = QLabel("Ultimate Launcher v1.0")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: white; margin-top: 10px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        desc = QLabel("Made by Mukunth P.R, built on Python, open source.<br><br><b>GitHub:</b> <a href='https://github.com/mukunthpr/UltimateLauncher' style='color:#7AA2F7;'>mukunthpr/UltimateLauncher</a>")
        desc.setOpenExternalLinks(True)
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setStyleSheet("color: #8C8C8C; font-size: 14px;")
        
        layout.addWidget(title)
        layout.addWidget(desc)
        return page

    def _build_installed_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 20, 30, 20)
        
        title = QLabel("Installed Extensions")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: white;")
        layout.addWidget(title)
        layout.addWidget(QLabel("Manage your dynamically loaded command registries and prefix aliases."))
        
        from PyQt6.QtWidgets import QFrame
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        cl = QVBoxLayout(content)
        cl.setContentsMargins(0, 10, 0, 10)
        cl.setSpacing(10)
        
        if self.plugin_manager:
            for p in self.plugin_manager.plugins:
                card = QWidget()
                card.setStyleSheet("background: #252525; padding: 12px; border-radius: 8px;")
                card_layout = QHBoxLayout(card)
                card_layout.setContentsMargins(10,5,10,5)
                
                info = QVBoxLayout()
                n = QLabel(p.name)
                n.setStyleSheet("font-weight: 600; font-size: 14px; color: white;")
                d = QLabel(p.id)
                d.setStyleSheet("color: #8C8C8C; font-size: 11px;")
                info.addWidget(n)
                info.addWidget(d)
                card_layout.addLayout(info)
                
                card_layout.addStretch()
                
                en_cb = QCheckBox("Enabled")
                p_config = self.config_manager.get("plugins", {}).get(p.id, {})
                en_cb.setChecked(p_config.get("enabled", True))
                card_layout.addWidget(en_cb)
                
                line = QFrame()
                line.setFrameShape(QFrame.Shape.VLine)
                card_layout.addWidget(line)
                
                card_layout.addWidget(QLabel("Action Key:"))
                pre_in = QLineEdit()
                pre_in.setFixedWidth(80)
                pre_in.setText(p_config.get("prefix_alias", p.prefix_alias))
                card_layout.addWidget(pre_in)
                
                save_btn = QPushButton("Save")
                save_btn.clicked.connect(lambda _, pid=p.id, cb=en_cb, pr=pre_in: self._apply_extension(pid, cb.isChecked(), pr.text()))
                card_layout.addWidget(save_btn)
                
                cl.addWidget(card)
                
        cl.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)
        return page

    def _apply_extension(self, p_id, enabled, prefix):
        plugins_config = self.config_manager.get("plugins", {})
        if p_id not in plugins_config:
            plugins_config[p_id] = {}
        plugins_config[p_id]["enabled"] = enabled
        plugins_config[p_id]["prefix_alias"] = prefix.strip()
        
        self.config_manager.set("plugins", plugins_config)
        if self.plugin_manager:
            for p in self.plugin_manager.plugins:
                if p.id == p_id:
                    p.prefix_alias = prefix.strip()
                    break
        self._prompt_restart("Extension Saved", f"Configuration for '{p_id}' natively applied on disk, and runtime triggers updated globally.")

    def on_startup_changed(self, state):
        is_checked = (state == 2)
        self.config_manager.set("run_on_startup", is_checked)
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.reg_path, 0, winreg.KEY_SET_VALUE)
            if is_checked:
                venv_python = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".venv", "Scripts", "pythonw.exe")
                main_script = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "main.py")
                if not os.path.exists(venv_python):
                    venv_python = sys.executable.replace("python.exe", "pythonw.exe")
                command = f'"{venv_python}" "{main_script}"'
                winreg.SetValueEx(key, self.app_name, 0, winreg.REG_SZ, command)
            else:
                try:
                    winreg.DeleteValue(key, self.app_name)
                except FileNotFoundError:
                    pass
            winreg.CloseKey(key)
        except Exception as e:
            QMessageBox.warning(self, "Startup Settings", f"Failed to update startup registry:\n{e}")

    def apply_hotkey(self):
        new_hotkey = self.hotkey_input.text().strip()
        if not new_hotkey: return
        try:
            self.hotkey_manager.update_hotkey(new_hotkey)
            QMessageBox.information(self, "Hotkey Updated", f"Global hook swapped to: {new_hotkey}")
        except Exception as e:
            QMessageBox.critical(self, "Hotkey Error", f"Keybind failure:\n{e}")
            self.hotkey_input.setText(self.config_manager.get("hotkey"))
