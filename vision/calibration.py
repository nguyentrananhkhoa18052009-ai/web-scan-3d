import cv2
import numpy as np
import json
import os

class BoxCalibrator:
    def __init__(self, box_size_cm=30.0, config_file="calibration.json"):
        self.box_size_cm = box_size_cm
        self.config_file = config_file
        self.homography_matrix = None
        self.calibrated = False
        self.corner_points = []
        
        # Tu dong doc lai 4 goc cu neu da tung hieu chuan truoc do
        self.load_calibration()

    def calibrate_from_corners(self, corners):
        """
        corners: Danh sach 4 diem [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]
        Theo thu tu:
        0: Goc O (0, 0)
        1: Diem X (30, 0)
        2: Diem Cheo (30, 30)
        3: Diem Y (0, 30)
        """
        if len(corners) != 4:
            return False, "Can dung 4 diem goc."

        src_pts = np.float32(corners)
        dst_pts = np.float32([
            [0, 0],
            [self.box_size_cm, 0],
            [self.box_size_cm, self.box_size_cm],
            [0, self.box_size_cm]
        ])

        H, _ = cv2.findHomography(src_pts, dst_pts)
        if H is None:
            return False, "Khong the tinh ma tran phoi canh."

        self.homography_matrix = H
        self.calibrated = True
        self.corner_points = corners

        # Ghi vao file de khong bi mat khi tat server
        self.save_calibration()
        return True, "Hieu chuan thanh cong va da luu cau hinh vinh vien!"

    def save_calibration(self):
        try:
            data = {
                "corners": self.corner_points,
                "homography": self.homography_matrix.tolist() if self.homography_matrix is not None else None,
                "calibrated": self.calibrated
            }
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print("Loi khi luu calibration:", e)

    def load_calibration(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if data.get("calibrated") and data.get("homography"):
                        self.corner_points = data.get("corners", [])
                        self.homography_matrix = np.array(data["homography"], dtype=np.float32)
                        self.calibrated = True
                        print("[INFO] Da tu dong tai lai 4 goc hop cu tu calibration.json")
            except Exception as e:
                print("Loi khi doc file calibration:", e)