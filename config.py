# config.py

import threading
import ctypes
import os
import sys

def get_resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

class Config:
    CAMERA_WIDTH = 640
    CAMERA_HEIGHT = 480
    EMA_ALPHA = 0.5
    
    # Umbrales de histéresis invariantes a la escala (relativos al tamaño de la mano)
    CLICK_IN_THRESHOLD = 0.6
    CLICK_OUT_THRESHOLD = 0.9
    
    RIGHT_CLICK_IN_THRESHOLD = 0.6
    RIGHT_CLICK_OUT_THRESHOLD = 0.9
    
    MIDDLE_CLICK_IN_THRESHOLD = 0.6
    MIDDLE_CLICK_OUT_THRESHOLD = 0.9
    
    SCROLL_IN_THRESHOLD = 0.6
    SCROLL_OUT_THRESHOLD = 0.9
    
    MINIMIZE_IN_THRESHOLD = 0.6
    MINIMIZE_OUT_THRESHOLD = 0.9
    
    DRAG_DELAY = 0.5 # Segundos requeridos de pinza para activar el modo arrastrar
    
    ROI_MARGIN_PERCENT = 0.20 # 20% margin for ROI
    
    # Global state
    tracking_active = True
    tracking_lock = threading.Lock()
    
    # Resolución dinámica del sistema
    try:
        user32 = ctypes.windll.user32
        user32.SetProcessDPIAware()
        SCREEN_WIDTH = user32.GetSystemMetrics(0)
        SCREEN_HEIGHT = user32.GetSystemMetrics(1)
    except Exception:
        SCREEN_WIDTH = 1920
        SCREEN_HEIGHT = 1080

    @classmethod
    def set_tracking(cls, state):
        with cls.tracking_lock:
            cls.tracking_active = state

    @classmethod
    def is_tracking(cls):
        with cls.tracking_lock:
            return cls.tracking_active
