import math
import numpy as np

class State:
    """Trạng thái của xe: x, y, yaw (rad)."""
    def __init__(self, Ban_kinh, Khoang_cach_banh):
        self.R = Ban_kinh
        self.b = Khoang_cach_banh

    def velocity(self,angle,Wr,Wl):
        velx = self.R/2 * math.cos(angle) * Wr + self.R/2 * math.cos(angle) * Wl
        vely = self.R/2 * math.sin(angle) * Wr + self.R/2 * math.sin(angle) * Wl
        velang = self.R/self.b * Wr - self.R/self.b * Wl
        return velx, vely,velang

class PurePursuit:
    """Bộ điều khiển Pure Pursuit."""
    def __init__(self, path, lookahead_dist, wheelbase):
        """
        path: danh sách các điểm (x, y) của quỹ đạo
        lookahead_dist: khoảng nhìn trước Ld [m]
        wheelbase: chiều dài cơ sở L [m]
        """
        self.path = path
        self.Ld = lookahead_dist
        self.L = wheelbase
        self.old_target_idx = 0

    def _find_target_index(self, state):
        """
        Tìm chỉ số điểm mục tiêu đầu tiên sao cho khoảng cách từ xe tới
        điểm đó >= Ld.
        """
        # Tính khoảng cách từ trạng thái hiện tại đến từng điểm
        dists = [math.hypot(px - state[0], py - state[1]) for px, py in self.path]
        idx = self.old_target_idx
        # Tìm từ chỉ số trước cho hiệu quả
        while idx < len(self.path):
            if dists[idx] > self.Ld:
                break
            idx += 1
        # Nếu không tìm được, chọn điểm cuối
        target_idx = min(idx, len(self.path) - 1)
        self.old_target_idx = target_idx
        return target_idx

    def control(self, state, v):
        """
        Tính góc lái delta [rad] cho trạng thái và vận tốc v.
        Trả về (delta, target_idx).
        """
        target_idx = self._find_target_index(state)
        tx, ty = self.path[target_idx]
        # Chuyển toạ độ điểm mục tiêu về hệ tọa độ xe
        dx = tx - state[0]
        dy = ty - state[1]
        angle = math.atan2(dy, dx) - state[2]
        # Công thức Pure Pursuit
        delta = math.atan2(2 * self.L * math.sin(angle), self.Ld)
        # vel_right = v * (1 + self.L * math.sin(angle)/self.Ld)
        # vel_left = v * (1 - self.L * math.sin(angle)/self.Ld)
        vel_right = v * (1 + math.tan(delta))
        vel_left = v * (1 - math.tan(delta))
        return delta, vel_right, vel_left

class rotation:
    def __init__(self,target_angle,velocity):
        self.target = target_angle
        self.vel = velocity

    def control(self, state):
        angle_diff = self.target - state
        direction = 1 if angle_diff > 0 else -1
        right_speed = direction * self.vel
        left_speed = -direction * self.vel
        return left_speed, right_speed
