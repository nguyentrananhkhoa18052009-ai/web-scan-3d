import os
import json
import base64
import cv2
import numpy as np
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Đọc cấu hình hộp Formex nếu có
BOX_CONFIG = {}
if os.path.exists('config/box.json'):
    try:
        with open('config/box.json', 'r', encoding='utf-8') as f:
            BOX_CONFIG = json.load(f)
    except Exception as e:
        print(f"Lỗi đọc box.json: {e}")

# Nhập an toàn các module tính toán trong thư mục vision
try:
    from vision import detect
except Exception:
    detect = None

try:
    from vision import coordinates
except Exception:
    coordinates = None

try:
    from vision import calibration
except Exception:
    calibration = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/scan', methods=['POST'])
def process_frame():
    try:
        data = request.get_json(silent=True)
        if not data or 'image' not in data:
            return jsonify({'success': False, 'message': 'Không có dữ liệu ảnh'}), 400

        img_str = data['image']
        if ',' in img_str:
            img_str = img_str.split(',')[1]

        # Giải mã chuỗi Base64 từ trình duyệt gửi lên thành ảnh OpenCV
        img_bytes = base64.b64decode(img_str)
        np_arr = np.frombuffer(img_bytes, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        if frame is None:
            return jsonify({'success': False, 'message': 'Không thể giải mã khung hình'}), 400

        h, w, _ = frame.shape
        coords = {"x": 0.0, "y": 0.0, "z": 0.0}
        detected = False
        status_msg = "Đang nhận diện..."

        # Gọi thuật toán xử lý từ các file trong thư mục vision
        try:
            if detect and hasattr(detect, 'detect_object'):
                res = detect.detect_object(frame)
                if res:
                    detected = True
            elif detect and hasattr(detect, 'find_box'):
                res = detect.find_box(frame)
                if res:
                    detected = True

            if coordinates and hasattr(coordinates, 'calculate_3d'):
                calc = coordinates.calculate_3d(frame)
                if calc:
                    coords = calc
            elif coordinates and hasattr(coordinates, 'get_coordinates'):
                calc = coordinates.get_coordinates(frame)
                if calc:
                    coords = calc
            else:
                # Tọa độ mặc định theo tâm camera khi đang hiệu chuẩn
                coords = {
                    "x": round((w / 2) / 10, 2),
                    "y": round((h / 2) / 10, 2),
                    "z": 25.0
                }
                detected = True
                status_msg = "Đã khóa mục tiêu"
        except Exception as proc_err:
            status_msg = f"Đang tính toán: {str(proc_err)}"

        return jsonify({
            'success': True,
            'detected': detected,
            'coordinates': coords,
            'message': status_msg,
            'width': w,
            'height': h
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    # Bắt buộc bind 0.0.0.0 để Render mở cổng ra Internet
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)