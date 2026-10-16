import sys
import cv2
import time
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QProgressBar
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QPalette, QColor, QImage, QPixmap

class CalibrationUI(QWidget):
    def __init__(self, camera, detector, gestures, on_complete_callback):
        super().__init__()
        self.camera = camera
        self.detector = detector
        self.gestures = gestures
        self.on_complete_callback = on_complete_callback
        
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.resize(700, 550)
        
        screen = QApplication.primaryScreen().geometry()
        self.move((screen.width() - self.width()) // 2, (screen.height() - self.height()) // 2)
        
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor("#121214"))
        palette.setColor(QPalette.ColorRole.WindowText, QColor("#FFFFFF"))
        self.setPalette(palette)
        
        self.setStyleSheet("""
            QWidget {
                border-radius: 15px;
                border: 1px solid #2D2D30;
            }
            QLabel {
                border: none;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(15)
        self.setLayout(layout)
        
        self.title = QLabel("Configuración de Seguimiento")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title.setFont(QFont("Segoe UI", 22, QFont.Weight.Light))
        self.title.setStyleSheet("color: #FFFFFF; letter-spacing: 2px;")
        layout.addWidget(self.title)
        
        self.status = QLabel("Iniciando sensores...")
        self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status.setFont(QFont("Segoe UI", 13))
        self.status.setStyleSheet("color: #00E5FF;")
        layout.addWidget(self.status)
        
        self.feed_label = QLabel()
        self.feed_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.feed_label.setFixedSize(600, 350)
        self.feed_label.setStyleSheet("background-color: #101012; border-radius: 10px;")
        layout.addWidget(self.feed_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(4)
        self.progress.setStyleSheet("""
            QProgressBar { background-color: #2D2D30; border: none; border-radius: 2px; }
            QProgressBar::chunk { background-color: #00D2FF; border-radius: 2px; }
        """)
        layout.addWidget(self.progress)
        
        self.state = "WAIT_HAND"
        self.progress.setValue(10)
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.process_frame)
        self.timer.start(30)
        self.done_time = 0
        
    def process_frame(self):
        ret, frame = self.camera.read()
        if not ret or frame is None:
            return
            
        timestamp_ms = int(time.time() * 1000)
        results = self.detector.process(frame, timestamp_ms)
        
        hand_landmarks = None
        is_clicking = False
        is_minimizing = False
        
        # Mirror the frame for UI so the user sees themselves as in a mirror
        display_frame = cv2.flip(frame, 1)
        h, w, c = display_frame.shape
        
        if results.hand_landmarks:
            # We must remember that results.hand_landmarks are based on the ORIGINAL frame.
            # So when drawing on the MIRRORED frame, we must invert the X coordinate!
            hand_landmarks = results.hand_landmarks[0]
            
            # Draw skeleton connections
            from mediapipe.python.solutions.drawing_utils import draw_landmarks
            from mediapipe.python.solutions.hands import HAND_CONNECTIONS
            
            # Draw custom modern skeleton on the mirrored frame
            for connection in HAND_CONNECTIONS:
                start_idx, end_idx = connection
                lm_start = hand_landmarks[start_idx]
                lm_end = hand_landmarks[end_idx]
                
                cx1, cy1 = int((1.0 - lm_start.x) * w), int(lm_start.y * h)
                cx2, cy2 = int((1.0 - lm_end.x) * w), int(lm_end.y * h)
                cv2.line(display_frame, (cx1, cy1), (cx2, cy2), (0, 210, 255), 2)
                
            for lm in hand_landmarks:
                cx, cy = int((1.0 - lm.x) * w), int(lm.y * h)
                cv2.circle(display_frame, (cx, cy), 4, (0, 255, 136), cv2.FILLED)
                
            _, is_clicking, _, _, _, is_minimizing, _ = self.gestures.process(hand_landmarks)
        else:
            self.gestures.reset()
            
        rgb_image = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
        bytes_per_line = rgb_image.strides[0]
        q_img = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        self.feed_label.setPixmap(QPixmap.fromImage(q_img).scaled(
            self.feed_label.width(), self.feed_label.height(),
            Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            
        self.check_calibration_state(hand_landmarks is not None, is_clicking, is_minimizing)

    def check_calibration_state(self, hand_visible, is_clicking, is_minimizing):
        if self.state == "WAIT_HAND":
            self.status.setText("Paso 1: Coloca tu mano frente a la cámara")
            if hand_visible:
                self.progress.setValue(30)
                self.state = "WAIT_CLICK"
        elif self.state == "WAIT_CLICK":
            self.status.setText("Paso 2: Junta el índice y pulgar (Hacer CLIC)")
            if is_clicking:
                self.progress.setValue(60)
                self.state = "WAIT_MINIMIZE"
        elif self.state == "WAIT_MINIMIZE":
            self.status.setText("Paso 3: Junta todos los dedos (Minimizar)")
            if is_minimizing:
                self.progress.setValue(100)
                self.status.setText("¡Calibración exitosa! Iniciando...")
                self.status.setStyleSheet("color: #00FF88;")
                self.state = "DONE"
                self.done_time = time.time()
        elif self.state == "DONE":
            if time.time() - self.done_time > 1.5:
                self.timer.stop()
                self.close()
                self.on_complete_callback()
