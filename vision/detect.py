import cv2
import numpy as np

class ObjectDetector:
    def __init__(self):
        self.bg_frame = None

    def capture_background(self, frame):
        if frame is not None:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            self.bg_frame = cv2.GaussianBlur(gray, (21, 21), 0)
            return True
        return False

    def detect(self, frame):
        if self.bg_frame is None or frame is None:
            return False, None, None, None, None

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        # Giảm ngưỡng từ 28 xuống 18 để bắt cả vật thể trong suốt hoặc phản chiếu ánh sáng
        diff = cv2.absdiff(self.bg_frame, gray)
        _, thresh = cv2.threshold(diff, 18, 255, cv2.THRESH_BINARY)
        thresh = cv2.dilate(thresh, None, iterations=2)

        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Hạ diện tích tối thiểu từ 600 xuống 150 để nhận diện được các phần nhỏ của vật thể
        valid_contours = [c for c in contours if cv2.contourArea(c) > 150]

        if not valid_contours:
            return False, None, None, None, None

        max_c = max(valid_contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(max_c)
        base_pt = (int(x + w / 2.0), int(y + h))

        return True, (x, y, w, h), base_pt, (int(x + w / 2.0), int(y + h / 2.0)), max_c