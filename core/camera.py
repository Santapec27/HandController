import cv2
import threading
from config import Config

class ThreadedCamera:
    def __init__(self, src=0):
        self.cap = cv2.VideoCapture(src, cv2.CAP_DSHOW)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, Config.CAMERA_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, Config.CAMERA_HEIGHT)
        self.ret, self.frame = self.cap.read()
        self.new_frame = True
        self.stopped = False
        self.lock = threading.Lock()

    def start(self):
        t = threading.Thread(target=self.update, args=())
        t.daemon = True
        t.start()
        return self

    def update(self):
        while True:
            if self.stopped:
                return
            ret, frame = self.cap.read()
            with self.lock:
                self.ret = ret
                self.frame = frame
                self.new_frame = True

    def read(self):
        with self.lock:
            if self.new_frame:
                self.new_frame = False
                return self.ret, self.frame
            else:
                return False, None

    def release(self):
        self.stopped = True
        self.cap.release()
