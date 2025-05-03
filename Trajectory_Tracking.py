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
        print(self.path[target_idx])
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

def simulate(path, initial_state, controller, v, dt, max_time):
    """
    Mô phỏng xe đi theo quỹ đạo.
    Trả về danh sách x, y, yaw theo thời gian.
    """
    state = initial_state
    x_hist, y_hist, yaw_hist = [state.x], [state.y], [state.yaw]
    time = 0.0

    while time < max_time:
        delta, target_idx = controller.control(state, v)
        state.update(v, delta, dt, controller.L)
        x_hist.append(state.x)
        y_hist.append(state.y)
        yaw_hist.append(state.yaw)
        time += dt
        # Nếu đã tới gần điểm cuối quỹ đạo thì dừng
        if target_idx >= len(path) - 1:
            break

    return x_hist, y_hist, yaw_hist

if __name__ == "__main__":
    # Tạo quỹ đạo mẫu: hình tròn bán kính R
    path = []
    R = 8.0
    for theta in np.linspace(0, 2 * math.pi, 200):
        path.append((R * math.cos(theta), R * math.sin(theta)))

    # Trạng thái ban đầu: tại (R, 0), hướng quay lên (pi/2)
    init_state = State(x=R, y=0.0, yaw=math.pi/2)

    # Tham số điều khiển
    lookahead = 1.5   # khoảng nhìn trước [m]
    L = 2.9           # chiều dài cơ sở [m]
    pp = PurePursuit(path, lookahead, L)

    # Tham số mô phỏng
    velocity = 2.0    # vận tốc [m/s]
    dt = 0.1          # bước thời gian [s]
    max_t = 100.0     # thời gian tối đa [s]

    # Chạy mô phỏng
    xs, ys, yaws = simulate(path, init_state, pp, velocity, dt, max_t)

    # Vẽ kết quả
    plt.figure()
    plt.plot([p[0] for p in path], [p[1] for p in path], "--", label="Quỹ đạo tham chiếu")
    plt.plot(xs, ys, label="Quỹ đạo xe đi được")
    plt.axis("equal")
    plt.xlabel("X [m]")
    plt.ylabel("Y [m]")
    plt.legend()
    plt.title("Pure Pursuit - Theo dõi quỹ đạo")
    plt.show()
