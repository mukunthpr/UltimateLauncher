from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, 
                             QListWidget, QListWidgetItem, QGraphicsDropShadowEffect, QLabel)
from PyQt6.QtCore import Qt, QEvent, QSize, QTimer
from PyQt6.QtGui import QColor, QFont, QIcon, QPixmap, QPainter, QPainterPath

class ResultItemWidget(QWidget):
    def __init__(self, title, subtitle="", icon=None):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(12)
        
        # Icon Container
        if icon:
            icon_label = QLabel()
            icon_label.setFixedSize(24, 24)
            if isinstance(icon, QIcon):
                icon_label.setPixmap(icon.pixmap(24, 24))
            icon_label.setStyleSheet("background: transparent;")
            layout.addWidget(icon_label)
            
        # Text Column (Title + Subtitle horizontally)
        text_layout = QHBoxLayout()
        text_layout.setSpacing(10)
        
        self.title_label = QLabel(title)
        self.title_label.setProperty("item_type", "title")
        self.title_label.setStyleSheet("font-weight: 600; font-size: 15px; background: transparent;")
        text_layout.addWidget(self.title_label)
        
        if subtitle:
            self.subtitle_label = QLabel(subtitle)
            self.subtitle_label.setProperty("item_type", "subtitle")
            self.subtitle_label.setStyleSheet("font-size: 12px; background: transparent;")
            text_layout.addWidget(self.subtitle_label)
            
        text_layout.addStretch()
        layout.addLayout(text_layout)
        
        # Right aligned trailing label (e.g. 'Command' or 'Application')
        # We can extract this roughly from the subtitle or plugin logic. 
        # For parity, if the subtitle is "Application", we put "Application" there.
        # Otherwise we can treat subtitle as the left label, and put a static "Command" on the right.
        # But wait, our plugins use subtitle dynamically. Let's visually push the subtitle over if it's "Application" or "Web Search", 
        # but to keep it simple, we'll put a trait label on the far right.
        trait_text = "Command"
        if "Application" in subtitle: trait_text = "Application"
        elif "Web Search" in subtitle: trait_text = "Web Search"
        elif "Suggestion" in subtitle: trait_text = "Google"
        elif "File" in subtitle or ":" in subtitle: trait_text = "File"
        # Trait specific styling
        trait_label = QLabel(trait_text)
        trait_label.setProperty("item_type", "trait")
        trait_label.setStyleSheet("font-size: 11px; font-weight: 600; background: transparent;")
        trait_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(trait_label)

class CalculatorResultWidget(QWidget):
    def __init__(self, expression, result):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Left side: Expression
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        expr_label = QLabel(expression)
        expr_label.setStyleSheet("font-size: 32px; font-weight: bold; color: white;")
        expr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        expr_badge = QLabel("Expression")
        expr_badge.setStyleSheet("background: rgba(255, 255, 255, 20); color: white; padding: 4px 8px; border-radius: 4px; font-size: 11px;")
        expr_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        left_layout.addWidget(expr_label)
        left_layout.addSpacing(10)
        left_layout.addWidget(expr_badge, alignment=Qt.AlignmentFlag.AlignHCenter)
        
        # Center: Arrow
        arrow_label = QLabel("→")
        arrow_label.setStyleSheet("font-size: 24px; color: #8C8C8C;")
        arrow_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Right side: Result
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        res_label = QLabel(result)
        res_label.setStyleSheet("font-size: 32px; font-weight: bold; color: white;")
        res_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        res_badge = QLabel("Result")
        res_badge.setStyleSheet("background: rgba(255, 255, 255, 20); color: white; padding: 4px 8px; border-radius: 4px; font-size: 11px;")
        res_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        right_layout.addWidget(res_label)
        right_layout.addSpacing(10)
        right_layout.addWidget(res_badge, alignment=Qt.AlignmentFlag.AlignHCenter)
        
        # Vertical divider line
        divider = QWidget()
        divider.setFixedWidth(1)
        divider.setStyleSheet("background: rgba(255, 255, 255, 10);")
        
        # Use stretch to perfectly center the modules
        layout.addStretch()
        layout.addWidget(left_widget)
        layout.addStretch()
        layout.addWidget(divider)
        layout.addStretch()
        layout.addWidget(arrow_label)
        layout.addStretch()
        layout.addWidget(right_widget)
        layout.addStretch()

class LauncherWindow(QWidget):
    def __init__(self, plugin_manager):
        super().__init__()
        import time
        self.last_toggle = 0
        self.plugin_manager = plugin_manager
        self.current_results = []
        self.init_ui()
        
        from PyQt6.QtWidgets import QApplication
        QApplication.instance().focusChanged.connect(self._on_focus_changed)
        
        # Poll every 300ms: if background web fetch completed for current query, refresh UI
        self._last_refreshed_query = None
        self._refresh_timer = QTimer()
        self._refresh_timer.timeout.connect(self._check_web_results)
        self._refresh_timer.start(300)
        
    def _check_web_results(self):
        """Check if background web/dict results are ready for current query and refresh."""
        text = self.search_box.text().strip()
        if not text or text == self._last_refreshed_query:
            return
        for plugin in self.plugin_manager.plugins:
            if hasattr(plugin, '_cache') and text in plugin._cache:
                self._last_refreshed_query = text
                self.on_search_changed(text)
                return
        
    def _on_focus_changed(self, old, new):
        # When focus moves to None, it means the user clicked entirely outside our PyQt application
        if self.isVisible() and new is None:
            self.hide()

    def init_ui(self):
        # Dark Raycast-like semi-translucent background
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # We NO LONGER call BlurWindow because Windows DWM will natively paint frosted glass
        # across the ENTIRE physical bounding box (740x520), which visibly exposes the 20px transparent 
        # margins we need to draw the drop-shadow! We must rely solely on Qt's RGBA.
        
        # Need margins for drop shadow clipping
        self.setFixedSize(700 + 40, 480 + 40)
        
        # Compile XAML Flow Launcher theme natively
        from core.config import ConfigManager
        from core.theme_manager import ThemeManager
        cfg = ConfigManager()
        tm = ThemeManager()
        active = cfg.get("active_theme", "default.json")
        self.setStyleSheet(tm.compile_theme(active))
        
        # Main Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20) # 20px padding around window for shadow
        layout.setSpacing(0)

        self.container = QWidget(self)
        self.container.setObjectName("MainContainer")
        self.container.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        
        # Drop shadow geometry
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 180))
        shadow.setOffset(0, 8)
        self.container.setGraphicsEffect(shadow)
        
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # Search Box Container
        search_container = QWidget()
        search_layout = QHBoxLayout(search_container)
        search_layout.setContentsMargins(16, 12, 16, 12)
        search_layout.setSpacing(12)
        
        # Procedurally fetch the original Ultimate Launcher logo and mask it
        import os
        
        logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "icon.png")
        if os.path.exists(logo_path):
            original = QPixmap(logo_path).scaled(32, 32, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            
            # Draw native rounded mask over original square PNG background
            masked_pixmap = QPixmap(32, 32)
            masked_pixmap.fill(Qt.GlobalColor.transparent)
            painter = QPainter(masked_pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # Clip into sleek 10px rounded edges
            path = QPainterPath()
            path.addRoundedRect(0, 0, 32, 32, 10, 10)
            painter.setClipPath(path)
            
            painter.drawPixmap(0, 0, original)
            painter.end()
            
            logo_label = QLabel()
            logo_label.setFixedSize(32, 32)
            logo_label.setPixmap(masked_pixmap)
            logo_label.setStyleSheet("background: transparent; margin-right: 4px; margin-left: 2px;")
            
            # Add requested shadow directly to the masked logo
            logo_shadow = QGraphicsDropShadowEffect()
            logo_shadow.setBlurRadius(10)
            logo_shadow.setColor(QColor(0, 0, 0, 220))
            logo_shadow.setOffset(0, 2)
            logo_label.setGraphicsEffect(logo_shadow)
            
            search_layout.addWidget(logo_label)
        
        self.search_box = QLineEdit()
        self.search_box.setObjectName("SearchBox")
        self.search_box.setPlaceholderText("Search for apps and commands...")
        font = QFont("Inter", 18)
        if font.exactMatch() == False:
            font = QFont("Segoe UI", 18)
        self.search_box.setFont(font)
        search_layout.addWidget(self.search_box)
        
        container_layout.addWidget(search_container)

        # Divider
        self.divider = QWidget()
        self.divider.setObjectName("Divider")
        self.divider.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.divider.setFixedHeight(1)
        container_layout.addWidget(self.divider)

        # Results List
        self.results_list = QListWidget()
        self.results_list.setObjectName("ResultsList")
        container_layout.addWidget(self.results_list)

        # Footer
        self.footer = QWidget()
        self.footer.setObjectName("Footer")
        self.footer.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.footer.setFixedHeight(30) # Thinner footer
        footer_layout = QHBoxLayout(self.footer)
        footer_layout.setContentsMargins(15, 0, 15, 0)
        footer_layout.setSpacing(8)
        
        hints_label = QLabel("Open Command ↵  |  Actions Ctrl K")
        hints_label.setObjectName("FooterHint")
        footer_layout.addWidget(hints_label)
        
        footer_layout.addStretch()
        
        container_layout.addWidget(self.footer)

        layout.addWidget(self.container)
        
        self.search_box.textChanged.connect(self.on_search_changed)
        self.search_box.installEventFilter(self)
        self.installEventFilter(self)
        self.results_list.installEventFilter(self)
        
        # Auto-hide inactivity timer (5 seconds of idle)
        self.inactivity_timer = QTimer(self)
        self.inactivity_timer.setSingleShot(True)
        self.inactivity_timer.setInterval(5000)
        self.inactivity_timer.timeout.connect(self.hide)
        
        # Initialize compact mode automatically
        self.on_search_changed("")

    def on_search_changed(self, text):
        from plugins.base_plugin import SearchResult
        self.results_list.clear()
        
        query_text = text.strip().lower()
        
        # --- COMPACT MODE LOGIC ---
        if not query_text:
            self.results_list.hide()
            self.footer.hide()
            self.divider.hide()
            self.setFixedSize(740, 68 + 40) # Ultra-compact height (Search Bar only) + margins
            return
        else:
            self.results_list.show()
            self.footer.show()
            self.divider.show()
            self.setFixedSize(740, 480 + 40) # Expanded default height + margins
        # --------------------------
        
        results = []
        if query_text in ["setting", "settings", "config", "preferences", "options"]:
            if hasattr(self, 'settings_window'):
                results.append(SearchResult(
                    title="Ultimate Launcher Settings",
                    subtitle="Configure hotkeys, behavior, and plugins",
                    icon=None,
                    score=200,
                    action=self.settings_window.show
                ))
                
        results.extend(self.plugin_manager.query(text))
        results.sort(key=lambda x: x.score, reverse=True)
        self.current_results = results
        
        for res in self.current_results:
            item = QListWidgetItem()
            
            if getattr(res, "is_calculator", False):
                item.setSizeHint(QSize(0, 140))  # Massively oversized structural block for math
                row_widget = CalculatorResultWidget(getattr(res, "query", ""), res.title)
            else:
                item.setSizeHint(QSize(0, 42))  # Thinner Raycast row heights 
                row_widget = ResultItemWidget(res.title, res.subtitle, getattr(res, 'icon', None))
                
            self.results_list.addItem(item)
            self.results_list.setItemWidget(item, row_widget)
            
        if self.results_list.count() > 0:
            self.results_list.setCurrentRow(0)

    def eventFilter(self, obj, event):
        # Reset inactivity timer on any user interaction
        if event.type() in (QEvent.Type.KeyPress, QEvent.Type.MouseMove, QEvent.Type.MouseButtonPress, QEvent.Type.Wheel):
            if self.isVisible():
                self.inactivity_timer.start()

        if obj == self.search_box and event.type() == QEvent.Type.KeyPress:
            # Handle Ctrl+K for Context Actions inside Search Box
            if event.modifiers() == Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_K:
                self.show_action_menu()
                return True
                
            key = event.key()
            if key == Qt.Key.Key_Up:
                curr = self.results_list.currentRow()
                if curr > 0:
                    self.results_list.setCurrentRow(curr - 1)
                return True
            elif key == Qt.Key.Key_Down:
                curr = self.results_list.currentRow()
                if curr < self.results_list.count() - 1:
                    self.results_list.setCurrentRow(curr + 1)
                return True
            elif key == Qt.Key.Key_Return or key == Qt.Key.Key_Enter:
                self.execute_current()
                return True
            elif key == Qt.Key.Key_Escape:
                self.hide()
                return True
        elif obj == self.results_list and event.type() == QEvent.Type.KeyPress:
            # Handle Ctrl+K for Context Actions inside Results List
            if event.modifiers() == Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_K:
                self.show_action_menu()
                return True
                
            key = event.key()
            if key == Qt.Key.Key_Return or key == Qt.Key.Key_Enter:
                self.execute_current()
                return True
        return super().eventFilter(obj, event)

    def execute_current(self):
        curr = self.results_list.currentRow()
        if curr >= 0 and curr < len(self.current_results):
            res = self.current_results[curr]
            if res.action:
                res.action()
        self.hide()
        self.search_box.clear()

    def show_action_menu(self):
        curr = self.results_list.currentRow()
        if curr >= 0 and curr < len(self.current_results):
            res = self.current_results[curr]
            if not hasattr(self, 'action_menu'):
                from ui.action_menu import ActionMenuWindow
                self.action_menu = ActionMenuWindow(self)
            
            # Spawn the sophisticated floating contextual frame 
            self.action_menu.show_actions(res, self.geometry())

    def center_window(self):
        screen = self.screen().geometry()
        x = (screen.width() - self.width()) // 2
        y = int(screen.height() * 0.20)
        self.move(x, y)

    def toggle_visibility(self):
        import time
        import ctypes
        if time.time() - self.last_toggle < 0.2:
            return
        self.last_toggle = time.time()
        
        if self.isVisible() and self.isActiveWindow():
            self.hide()
        else:
            self.center_window()
            self.showNormal()
            self.activateWindow()
            self.search_box.setFocus(Qt.FocusReason.ActiveWindowFocusReason)
            self.raise_()
            
            # Force Windows to relinquish keyboard focus bypassing ForegroundLockTimeout safely
            try:
                hwnd = int(self.winId())
                user32 = ctypes.windll.user32
                
                SPI_GETFOREGROUNDLOCKTIMEOUT = 0x2000
                SPI_SETFOREGROUNDLOCKTIMEOUT = 0x2001
                
                timeout = ctypes.c_int(0)
                # Save current timeout
                user32.SystemParametersInfoW(SPI_GETFOREGROUNDLOCKTIMEOUT, 0, ctypes.byref(timeout), 0)
                # Temporarily disable lock
                user32.SystemParametersInfoW(SPI_SETFOREGROUNDLOCKTIMEOUT, 0, ctypes.c_void_p(0), 2)
                
                # Aggressively steal screen focus
                user32.SetForegroundWindow(hwnd)
                user32.BringWindowToTop(hwnd)
                
                # Restore original timeout
                user32.SystemParametersInfoW(SPI_SETFOREGROUNDLOCKTIMEOUT, 0, ctypes.c_void_p(timeout.value), 2)
            except Exception as e:
                pass
            
            def _grab_focus_async():
                self.activateWindow()
                self.search_box.setFocus(Qt.FocusReason.ActiveWindowFocusReason)
                self.search_box.selectAll()
                
            # Allow OS context switches to resolve mathematically before seizing cursor
            QTimer.singleShot(25, _grab_focus_async)
            
            self.inactivity_timer.start()

    def hideEvent(self, event):
        self.inactivity_timer.stop()
        super().hideEvent(event)

    def changeEvent(self, event):
        if event.type() == QEvent.Type.ActivationChange:
            if not self.isActiveWindow():
                self.hide()
        super().changeEvent(event)
