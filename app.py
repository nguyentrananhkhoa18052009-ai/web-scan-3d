from flask import Flask, render_template, Response, request, jsonify
import cv2
import numpy as np
import json
import os
import time
import base64
from vision.camera import USBCamera
from vision.detect import ObjectDetector

app = Flask(__name__)

current_cam_index = 0
camera = USBCamera(camera_index=current_cam_index)
detector = ObjectDetector()

is_processing = True
latest_state = {
    "detected": False,
    "coords": None,
    "timestamp": None,
    "message": "He thong dang khoi dong"
}

CALIB_FILE = "calibration_3d.json"
calib_data = {
    "calibrated": False,
    "corners": [],
    "H_floor": None,
    "z_px_scale": 10.0
}

def load_calibration():
    global calib_data
    if os.path.exists(CALIB_FILE):
        try:
            with open(CALIB_FILE, "r") as f:
                data = json.load(f)
                corners = data.get("corners", [])
                if len(corners) >= 4:
                    pts = np.array(corners[:4], dtype=np.float32)
                    dst = np.array([[0, 0], [30, 0], [30, 30], [0, 30]], dtype=np.float32)
                    H, _ = cv2.findHomography(pts, dst)
                    calib_data["H_floor"] = H
                    calib_data["corners"] = corners
                    calib_data["z_px_scale"] = data.get("z_px_scale", 10.0)
                    calib_data["calibrated"] = True
        except Exception as e:
            print("Loi doc calib:", e)

load_calibration()

def estimate_full_3d(bbox):
    if not calib_data["calibrated"] or bbox is None:
        return None, "Chua hieu chuan"

    x, y, w, h = bbox
    H = calib_data["H_floor"]
    corners = calib_data["corners"]
    z_px_scale = calib_data.get("z_px_scale", 10.0)

    cx = x + w / 2.0
    base_y = y + h

    p_img = np.array([[[cx, base_y]]], dtype=np.float32)
    p_floor = cv2.perspectiveTransform(p_img, H)[0][0]
    fx, fy = float(p_floor[0]), float(p_floor[1])

    floor_lowest_y = max(corners[1][1], corners[3][1]) if len(corners) >= 4 else base_y
    elevation_px = max(0.0, floor_lowest_y - base_y)

    if 0.0 <= fx <= 30.0 and 0.0 <= fy <= 30.0:
        calc_z = (h / z_px_scale) * 0.85
        real_x, real_y = fx, fy
    else:
        calc_z = elevation_px / z_px_scale
        shift = calc_z * 0.35
        real_x = fx + shift
        real_y = fy + shift

    return {
        "x": round(max(0.0, min(30.0, real_x)), 2),
        "y": round(max(0.0, min(30.0, real_y)), 2),
        "z": round(max(0.0, min(30.0, calc_z)), 2)
    }, "Da do toa do 3D"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/camera/switch", methods=["POST"])
def switch_camera():
    global camera, current_cam_index
    data = request.json or {}
    idx = int(data.get("index", 0))
    try:
        camera.stop()
        camera = USBCamera(camera_index=idx)
        camera.start()
        current_cam_index = idx
        return jsonify({"success": True, "index": idx})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/api/calibrate/status", methods=["GET"])
def get_calib_status():
    return jsonify({
        "calibrated": bool(calib_data["calibrated"]),
        "corners": calib_data["corners"]
    })

@app.route("/api/calibrate/corners", methods=["POST"])
def calibrate_corners():
    global calib_data
    data = request.json or {}
    pts = data.get("corners", [])

    if len(pts) not in [4, 5]:
        return jsonify({"success": False, "message": "Can gui 4 diem day hoac 5 diem khong gian."}), 400

    try:
        pts_floor = np.array(pts[:4], dtype=np.float32)
        dst = np.array([[0, 0], [30, 0], [30, 30], [0, 30]], dtype=np.float32)
        H, _ = cv2.findHomography(pts_floor, dst)

        calib_data["H_floor"] = H
        calib_data["corners"] = pts

        if len(pts) == 5:
            O = np.array(pts[0], dtype=np.float32)
            Z_top = np.array(pts[4], dtype=np.float32)
            z_len_px = float(np.linalg.norm(Z_top - O))
            calib_data["z_px_scale"] = max(1.0, z_len_px / 30.0)
        else:
            len_side = (np.linalg.norm(pts_floor[1] - pts_floor[0]) + np.linalg.norm(pts_floor[3] - pts_floor[0])) / 2.0
            calib_data["z_px_scale"] = len_side / 30.0

        calib_data["calibrated"] = True

        with open(CALIB_FILE, "w") as f:
            json.dump({
                "corners": pts,
                "z_px_scale": calib_data["z_px_scale"]
            }, f, indent=4)

        return jsonify({"success": True, "message": "Hieu chuan 3D thanh cong!"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/api/background/capture", methods=["POST"])
def capture_background():
    frame = camera.get_frame()
    if frame is None:
        return jsonify({"success": False, "message": "Khong co frame camera."}), 400
    detector.capture_background(frame)
    return jsonify({"success": True, "message": "Da luu nen trong thanh cong."})

@app.route("/api/upload_image", methods=["POST"])
def upload_image():
    global latest_state
    if 'image' not in request.files:
        return jsonify({"success": False, "message": "Khong tim thay file anh."}), 400
    file = request.files['image']
    if file.filename == '':
        return jsonify({"success": False, "message": "Chua chon file anh."}), 400

    try:
        file_bytes = np.frombuffer(file.read(), np.uint8)
        img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        if img is None:
            return jsonify({"success": False, "message": "Anh khong hop le."}), 400

        annotated = img.copy()
        det, bbox, _, _, _ = detector.detect(img)
        coords = None
        msg = "Chua phat hien vat the"

        if det and calib_data["calibrated"]:
            x, y, w, h = bbox
            coords, msg = estimate_full_3d(bbox)
            if coords:
                cv2.rectangle(annotated, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cx, cy = int(x + w / 2.0), int(y + h / 2.0)
                cv2.circle(annotated, (cx, cy), 5, (0, 0, 255), -1)
                txt = f"X:{coords['x']} Y:{coords['y']} Z:{coords['z']}cm"
                cv2.putText(annotated, txt, (x, max(22, y - 8)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                latest_state = {
                    "detected": True,
                    "coords": coords,
                    "timestamp": time.strftime("%H:%M:%S"),
                    "message": "Da phat hien qua anh tai len"
                }
        elif det:
            x, y, w, h = bbox
            cv2.rectangle(annotated, (x, y), (x + w, y + h), (0, 255, 0), 2)
            msg = "Chua hieu chuan hop"

        _, buffer = cv2.imencode('.jpg', annotated, [cv2.IMWRITE_JPEG_QUALITY, 85])
        img_b64 = base64.b64encode(buffer).decode('utf-8')

        return jsonify({
            "success": True,
            "detected": det and (coords is not None),
            "coords": coords,
            "message": msg,
            "image_b64": f"data:image/jpeg;base64,{img_b64}"
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/api/control", methods=["POST"])
def toggle_processing():
    global is_processing
    data = request.json or {}
    is_processing = bool(data.get("running", True))
    return jsonify({"running": is_processing})

@app.route("/api/coordinates", methods=["GET"])
def get_coordinates():
    global latest_state
    return jsonify(latest_state)

def generate_video_stream():
    global latest_state
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 65]
    while True:
        frame = camera.get_frame()
        if frame is None:
            time.sleep(0.02)
            continue

        annotated = frame.copy()

        if is_processing:
            det, bbox, base_pt, _, _ = detector.detect(frame)
            if det and calib_data["calibrated"]:
                x, y, w, h = bbox
                coords, msg = estimate_full_3d(bbox)
                if coords:
                    cv2.rectangle(annotated, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    cx, cy = int(x + w / 2.0), int(y + h / 2.0)
                    cv2.circle(annotated, (cx, cy), 5, (0, 0, 255), -1)
                    txt = f"X:{coords['x']} Y:{coords['y']} Z:{coords['z']}cm"
                    cv2.putText(annotated, txt, (x, max(22, y - 8)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 2)

                    latest_state = {
                        "detected": True,
                        "coords": coords,
                        "timestamp": time.strftime("%H:%M:%S"),
                        "message": "Da phat hien vat the"
                    }
                else:
                    latest_state = {
                        "detected": False,
                        "coords": None,
                        "timestamp": time.strftime("%H:%M:%S"),
                        "message": msg
                    }
            elif det:
                x, y, w, h = bbox
                cv2.rectangle(annotated, (x, y), (x + w, y + h), (0, 255, 0), 2)
                latest_state = {
                    "detected": True,
                    "coords": None,
                    "timestamp": time.strftime("%H:%M:%S"),
                    "message": "Chua hieu chuan hop"
                }
            else:
                latest_state = {
                    "detected": False,
                    "coords": None,
                    "timestamp": time.strftime("%H:%M:%S"),
                    "message": "Chua phat hien vat the"
                }

        ret, buffer = cv2.imencode('.jpg', annotated, encode_param)
        if not ret:
            continue

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
        time.sleep(0.015)

@app.route("/video_feed")
def video_feed():
    return Response(generate_video_stream(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == "__main__":
    camera.start()
    app.run(host="127.0.0.1", port=5000, debug=False, threaded=True)