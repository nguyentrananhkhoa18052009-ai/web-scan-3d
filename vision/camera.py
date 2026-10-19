import cv2
import threading
import time

class USBCamera:
    def __init__(self, camera_index=0):
        self.camera_index = int(camera_index)
        self.cap = None
        self.frame = None
        self.is_running = False
        self.lock = threading.Lock()
        self.thread = None

    def start(self):
        if self.is_running:
            return

        # Dùng CAP_DSHOW chống giật lag trên Windows
        self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
        
        if not self.cap.isOpened():
            self.cap = cv2.VideoCapture(self.camera_index)

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1) # Triệt tiêu trễ bộ nhớ đệm[cite: 1]

        if self.cap.isOpened():
            self.is_running = True
            self.thread = threading.Thread(target=self._update_loop, daemon=True)
            self.thread.start()
        else:
            print(f"[ERROR] Khong the ket noi Camera index {self.camera_index}")

    def _update_loop(self):
        while self.is_running and self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                with self.lock:
                    self.frame = frame
            else:
                time.sleep(0.01)

    def get_frame(self):
        with self.lock:
            if self.frame is not None:
                return self.frame.copy()
            return None

    def stop(self):
        self.is_running = False
        if self.thread is not None:
            self.thread.join(timeout=1.0)
            self.thread = None

        if self.cap is not None:
            self.cap.release()
            self.cap = None

    def is_opened(self):
        return self.is_running and (self.cap is not None) and self.cap.isOpened()