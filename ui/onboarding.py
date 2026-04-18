from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QWidget
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor
import os

class OnboardingWindow(QDialog):
    def __init__(self, config_mgr):
        super().__init__()
        self.config_mgr = config_mgr
        
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.setFixedSize(500, 350)
        
        self.slides = [
            {
                "title": "Welcome to Ultimate Launcher",
                "text": "Your new, lightning-fast productivity hub.\nSearch files, run plugins, and execute commands\ninstantly."
            },
            {
                "title": "Extensible Plugins",
                "text": "Browse the built-in Store to download\nnew tools, converters, and scripts dynamically."
            },
            {
                "title": "Summon Anywhere",
                "text": "Press Alt + Space from any application\nto instantly bring up the search bar."
            }
        ]
        
        self.current_slide = 0
        
        self.init_ui()
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.next_slide)
        self.timer.start(4000) # Switch every 4 seconds
        
    def init_ui(self):
        # Main container with glassmorphism style
        self.container = QWidget(self)
        self.container.setFixedSize(self.width(), self.height())
        self.container.setStyleSheet("""
            QWidget {
                background-color: rgba(28, 28, 30, 0.95);
                border-radius: 12px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
            QLabel#Title {
                color: #ffffff;
                font-size: 24px;
                font-weight: bold;
                background: transparent;
                border: none;
            }
            QLabel#Text {
                color: #a1a1a6;
                font-size: 16px;
                background: transparent;
                border: none;
            }
            QPushButton {
                background-color: #0a84ff;
                color: white;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background-color: #007aff;
            }
        """)

        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        
        self.title_label = QLabel(self.slides[0]["title"])
        self.title_label.setObjectName("Title")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.text_label = QLabel(self.slides[0]["text"])
        self.text_label.setObjectName("Text")
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addStretch()
        layout.addWidget(self.title_label)
        layout.addWidget(self.text_label)
        layout.addStretch()
        
        # Buttons
        btn_layout = QHBoxLayout()
        self.skip_btn = QPushButton("Skip Data")
        self.skip_btn.setStyleSheet("background-color: transparent; color: #636366; font-weight: normal; border: 1px solid #3a3a3c;")
        self.skip_btn.clicked.connect(self.finish)
        
        self.next_btn = QPushButton("Next")
        self.next_btn.clicked.connect(self.manual_next)
        
        btn_layout.addWidget(self.skip_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.next_btn)
        
        layout.addLayout(btn_layout)
        
        # Pagination Dots
        self.dots_layout = QHBoxLayout()
        self.dots_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.dots = []
        for i in range(len(self.slides)):
            dot = QLabel("•")
            dot.setStyleSheet("color: white; font-size: 24px; background: transparent; border: none;") if i == 0 else dot.setStyleSheet("color: #636366; font-size: 24px; background: transparent; border: none;")
            self.dots.append(dot)
            self.dots_layout.addWidget(dot)
            
        layout.addLayout(self.dots_layout)
        
    def next_slide(self):
        self.current_slide += 1
        if self.current_slide >= len(self.slides):
            self.finish()
            return
            
        self.update_content()
        
    def manual_next(self):
        self.timer.start(4000) # Reset timer
        self.next_slide()
        
    def update_content(self):
        self.title_label.setText(self.slides[self.current_slide]["title"])
        self.text_label.setText(self.slides[self.current_slide]["text"])
        
        if self.current_slide == len(self.slides) - 1:
            self.next_btn.setText("Get Started")
            
        for i, dot in enumerate(self.dots):
            if i == self.current_slide:
                dot.setStyleSheet("color: white; font-size: 24px; background: transparent; border: none;")
            else:
                dot.setStyleSheet("color: #636366; font-size: 24px; background: transparent; border: none;")
                
    def finish(self):
        self.timer.stop()
        self.config_mgr.set("first_time_launch", False)
        self.accept()
