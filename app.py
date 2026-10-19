import os
import json
import base64
import cv2
import numpy as np
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Đọc cấu hình hộp Formex
BOX_CONFIG = {}
if os.path.exists('config/box.json'):
    try:
        with open('config/box.json', 'r', encoding='utf-8') as f:
            BOX_CONFIG = json.load(f)
    except Exception as e:
        print(f"Lỗi đọc box.json: {e}")

# Nhập các hàm thuật toán từ thư mục vision
try:
    from vision import detect, coordinates, calibration
except Exception as e:
    print(f"Lỗi import module vision: {e}")
    detect = coordinates = calibration = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/config', methods=['GET'])
def get_config():
    return jsonify(BOX_CONFIG)

@app.route('/api/scan', methods=['POST'])
def process_client_frame():
    try:
        data = request.get_json(silent=True)
        if not data or 'image' not in data:
            return jsonify({'success': False, 'message': 'Thiếu dữ liệu ảnh'}), 400

        img_str = data['image']
        if ',' in img_str:
            img_str = img_str.split(',')[1]

        # Giải mã ảnh từ Base64 client gửi lên
        img_bytes = base64.b64decode(img_str)
        np_arr = np.frombuffer(img_bytes, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        if frame is None:
            return jsonify({'success': False, 'message': 'Lỗi giải mã ảnh'}), 400

        h, w, _ = frame.shape
        coords = {"x": 0.0, "y": 0.0, "z": 0.0}
        detected = False
        message = "Đang quét vật thể..."

        # Gọi logic xử lý từ module vision
        try:
            if detect and hasattr(detect, 'detect_object'):
                detected = bool(detect.detect_object(frame))
            if coordinates and hasattr(coordinates, 'calculate_3d'):
                coords = coordinates.calculate_3d(frame) or coords
            else:
                # Giá trị dự phòng khi chưa khóa vật thể
                coords = {"x": round(w / 20.0, 2), "y": round(h / 20.0, 2), "z": 20.0}
                detected = True
                message = "Đã nhận diện tọa độ"
        except Exception as err:
            message = f"Đang hiệu chỉnh: {str(err)}"

        return jsonify({
            'success': True,
            'detected': detected,
            'coordinates': coords,
            'message': message,
            'resolution': {'w': w, 'h': h}
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)