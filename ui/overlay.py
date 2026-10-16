import sys
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import Qt, QTimer, QPointF
from PyQt6.QtGui import QPainter, QColor, QPen, QRadialGradient

class ConfidenceOverlay(QWidget):
    def __init__(self):
        super().__init__()
        
        # Transparent, click-through, always on top, no frame
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.WindowTransparentForInput |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Full screen
        self.showFullScreen()
        
        self.cursor_x = -100
        self.cursor_y = -100
        self.confidence = 1.0
        
        # We need a timer to update the drawing if we want smooth animations,
        # but we can also just call update() from the main loop via signals.
        # To avoid threading issues between OpenCV and PyQt, we use a QTimer to poll a shared state.
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(16) # ~60fps
        
        # Shared state class reference
        self.shared_state = None
        
    def set_shared_state(self, state_dict):
        self.shared_state = state_dict

    def paintEvent(self, event):
        if self.shared_state:
            self.cursor_x = self.shared_state.get('x', -100)
            self.cursor_y = self.shared_state.get('y', -100)
            self.confidence = self.shared_state.get('confidence', 1.0)
            
        if self.cursor_x < 0 or self.cursor_y < 0:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Aura color based on confidence (Blue = 1.0, Orange = 0.0)
        # Blue: (0, 150, 255), Orange: (255, 100, 0)
        r = int((1 - self.confidence) * 255 + self.confidence * 0)
        g = int((1 - self.confidence) * 100 + self.confidence * 150)
        b = int((1 - self.confidence) * 0 + self.confidence * 255)
        
        center = QPointF(self.cursor_x, self.cursor_y)
        radius = 30
        
        gradient = QRadialGradient(center, radius)
        gradient.setColorAt(0.0, QColor(r, g, b, 100))
        gradient.setColorAt(1.0, QColor(r, g, b, 0))
        
        painter.setBrush(gradient)
        painter.setPen(Qt.PenStyle.NoPen)
        
        painter.drawEllipse(center, radius, radius)
        painter.end()

def launch_overlay(shared_state):
    app = QApplication(sys.argv)
    overlay = ConfidenceOverlay()
    overlay.set_shared_state(shared_state)
    overlay.show()
    app.exec()
