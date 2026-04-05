from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QListWidget, QListWidgetItem, 
                             QGraphicsDropShadowEffect, QApplication)
from PyQt6.QtCore import Qt, QEvent, QSize
from PyQt6.QtGui import QColor, QFont

class ActionMenuWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.setFixedWidth(320)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        
        self.container = QWidget()
        self.container.setObjectName("ActionContainer")
        self.container.setStyleSheet("""
            QWidget#ActionContainer {
                background-color: rgba(22, 22, 22, 250);
                border-radius: 12px;
                border: 1px solid rgba(255, 255, 255, 25);
            }
            QListWidget {
                background: transparent;
                border: none;
                outline: none;
            }
            QListWidget::item {
                border-radius: 6px;
                margin: 2px 8px;
                padding-left: 4px;
                color: white;
            }
            QListWidget::item:selected {
                background-color: rgba(255, 255, 255, 25);
            }
        """)
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 180))
        shadow.setOffset(0, 4)
        self.container.setGraphicsEffect(shadow)
        
        c_layout = QVBoxLayout(self.container)
        c_layout.setContentsMargins(0, 8, 0, 8)
        
        self.list_widget = QListWidget()
        c_layout.addWidget(self.list_widget)
        layout.addWidget(self.container)
        
        self.list_widget.itemActivated.connect(self._on_activated)
        
        self.current_actions = []
        
        # Capture critical layout routing hooks
        self.installEventFilter(self)
        self.list_widget.installEventFilter(self)

    def show_actions(self, search_result, main_rect):
        self.current_actions = []
        self.list_widget.clear()
        
        font = QFont("Inter", 11)
        if not font.exactMatch(): font = QFont("Segoe UI", 11)
        
        # Primary Default Action
        if search_result.action:
            self.current_actions.append({"name": "Open", "action": search_result.action})
            item = QListWidgetItem("Open")
            item.setSizeHint(QSize(0, 36))
            item.setFont(font)
            item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter)
            self.list_widget.addItem(item)
            
        # Extraneous Context Engine Actions
        for action_dict in getattr(search_result, 'context_actions', []):
            self.current_actions.append(action_dict)
            item = QListWidgetItem(action_dict["name"])
            item.setSizeHint(QSize(0, 36))
            item.setFont(font)
            if "icon" in action_dict and action_dict["icon"]:
                item.setIcon(action_dict["icon"])
            self.list_widget.addItem(item)
            
        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)
            
        # Draw layout geometry bounding vectors
        height = max(50, min(400, (self.list_widget.count() * 40) + 40))
        self.setFixedHeight(height)
        
        # Position it to the true-right of the main layout, aligned to the absolute bottom row
        x = main_rect.x() + main_rect.width() - 25
        y = main_rect.y() + main_rect.height() - height
        
        # Secure boundaries against viewport overflow clipping
        screen = QApplication.primaryScreen().geometry()
        if x + self.width() > screen.width():
            x = main_rect.x() - self.width() + 25
            
        self.move(x, y)
        self.show()
        self.raise_()
        self.activateWindow()
        self.list_widget.setFocus()
        
    def _on_activated(self, item):
        idx = self.list_widget.row(item)
        if 0 <= idx < len(self.current_actions):
            action_func = self.current_actions[idx].get("action")
            if action_func:
                action_func()
                
        # Command successfully executed; collapse UI tree natively
        self.hide()
        if self.parent():
            self.parent().hide()
            self.parent().search_box.clear()

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.KeyPress:
            key = event.key()
            if key == Qt.Key.Key_Escape:
                self.hide()
                if self.parent():
                    self.parent().activateWindow()
                    self.parent().search_box.setFocus()
                return True
            elif key == Qt.Key.Key_Return or key == Qt.Key.Key_Enter:
                item = self.list_widget.currentItem()
                if item:
                    self._on_activated(item)
                return True
                
        if event.type() == QEvent.Type.WindowDeactivate:
            self.hide()
            
        return super().eventFilter(obj, event)
