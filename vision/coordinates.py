import numpy as np

class CoordinateTransformer:
    def __init__(self, box_limits=(30.0, 30.0, 30.0)):
        self.box_limits = box_limits

    def pixel_to_world_xy(self, pixel_point, H):
        if H is None:
            return None, "Chua hieu chuan camera."

        pt_homogeneous = np.array([pixel_point[0], pixel_point[1], 1.0], dtype=np.float32)
        world_homogeneous = np.dot(H, pt_homogeneous)

        if np.isclose(world_homogeneous[2], 0.0):
            return None, "Loi suy bien toa do."

        x_cm = world_homogeneous[0] / world_homogeneous[2]
        y_cm = world_homogeneous[1] / world_homogeneous[2]

        is_valid = (0.0 <= x_cm <= self.box_limits[0]) and (0.0 <= y_cm <= self.box_limits[1])

        return {
            "x": round(float(x_cm), 2),
            "y": round(float(y_cm), 2),
            "z": None,
            "z_status": "Chua do duoc",
            "is_valid": is_valid
        }, "Thanh cong" if is_valid else "Ngoai pham vi day hop."