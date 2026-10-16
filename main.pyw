import time
import threading
import sys
from PyQt6.QtWidgets import QApplication

from core.camera import ThreadedCamera
from core.detector import HandDetector
from core.gestures import GestureProcessor
from core.input_emitter import InputEmitter
from tray.tray_app import TrayApp
from config import Config

from ui.calibration import CalibrationUI
from ui.overlay import ConfidenceOverlay
from ui.settings_panel import EvolutionPanel

class HandControllerApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)
        # Shared state for overlay
        self.shared_state = {'x': -100, 'y': -100, 'confidence': 1.0}
        
        # Initialize camera and detector early for calibration
        self.camera = ThreadedCamera().start()
        self.detector = HandDetector()
        self.gestures = GestureProcessor()
        self.emitter = None
        self.running = False
        
        self.tray = None
        self.overlay = None
        self.settings_panel = None
        self.loop_thread = None

    def start_calibration(self):
        self.calibration_ui = CalibrationUI(self.camera, self.detector, self.gestures, self.on_calibration_complete)
        self.calibration_ui.show()

    def on_calibration_complete(self):
        # Start core components that shouldn't be active during calibration
        self.emitter = InputEmitter()
        self.running = True
        
        # Start Tray and Overlay
        self.tray = TrayApp(self.stop, self.show_settings)
        
        self.overlay = ConfidenceOverlay()
        self.overlay.set_shared_state(self.shared_state)
        self.overlay.show()
        
        # Start background loop
        self.loop_thread = threading.Thread(target=self.main_loop)
        self.loop_thread.daemon = True
        self.loop_thread.start()

    def show_settings(self):
        if not self.settings_panel:
            self.settings_panel = EvolutionPanel()
        self.settings_panel.load_profile()
        self.settings_panel.show()
        self.settings_panel.raise_()
        self.settings_panel.activateWindow()

    def main_loop(self):
        time.sleep(1.0) # Wait for camera
        
        while self.running:
            if not Config.is_tracking():
                time.sleep(0.1)
                continue
                
            ret, frame = self.camera.read()
            if not ret or frame is None:
                time.sleep(0.01)
                continue
                
            timestamp_ms = int(time.time() * 1000)
            results = self.detector.process(frame, timestamp_ms)
            
            if results.hand_landmarks:
                for hand_landmarks in results.hand_landmarks:
                    pos, is_clicking, is_right_clicking, is_middle_clicking, is_scrolling, is_minimizing, confidence = self.gestures.process(hand_landmarks)
                    self.emitter.emit(pos, is_clicking, is_right_clicking, is_middle_clicking, is_scrolling, is_minimizing)
                    
                    if pos:
                        self.shared_state['x'] = pos[0]
                        self.shared_state['y'] = pos[1]
                        self.shared_state['confidence'] = confidence
                    break
            else:
                self.gestures.reset()
                self.emitter.emit(None, False, False, False, False, False)
                self.shared_state['x'] = -100
                self.shared_state['y'] = -100
                self.shared_state['confidence'] = 1.0

    def stop(self):
        self.running = False
        if self.camera:
            self.camera.release()
        
        # Train ML model on exit
        if self.gestures and self.gestures.ml_engine:
            self.gestures.ml_engine.train_on_logs()
            
        self.app.quit()

    def run(self):
        self.start_calibration()
        sys.exit(self.app.exec())

if __name__ == "__main__":
    app = HandControllerApp()
    app.run()
