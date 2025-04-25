import socket
import json
import time
import math
class SenData:
    def __init__(self):
        self.ip = None
        self.port = None
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connected = False
        self.path = None   #mảng gồm 2 phần tử, path[0] là tọa độ điểm đầu, path[1] là tọa độ điểm cuối
        self.current_pos = None #tọa độ robot hiện tại
        self.current_angle = None # góc của robot hiện tại
        self.vel_right = None # vận tốc bánh phải
        self.vel_left = None    # vận tốc bánh trái
        self.flag = None # cờ lưu góc ban đầu của robot
        self.initial_angle = None

    def SetPath(self,path):
        self.path = path

    def SetPos(self,pos):
        pass

    def connect(self):
        try:
            self.sock.connect((self.ip, self.port))
            self.connected = True
            print(f"Connected to ESP32 at {self.ip}:{self.port}")
        except socket.error as e:
            print(f"Connection failed: {e}")

    def SetVelStraight(self):  
        a = 100 # gia tốc
        K = 0.2 # hệ số điều chỉnh tốc độ
        d_travelled = math.hypot(self.path[0][0]-self.current_pos[0],self.path[0][1]-self.current_pos[1])
        d_remain = math.hypot(self.path[1][0]-self.current_pos[0],self.path[1][1]-self.current_pos[1])
        v_desired = min(math.sqrt(2 * a * d_travelled) if d_travelled > 0 else 50,
                                    1000,
                                    math.sqrt(2 * a * d_remain) if d_remain > 0 else 50)
        angle = self.calculate_angle_deg(self.current_pos[0],self.current_pos[1],self.path[1][0],self.path[1][1])
        delta_angle = self.current_angle - angle
        if d_remain > 100:
            if abs(delta_angle) < 1:
                self.vel_left =v_desired
                self.vel_right = v_desired
            elif delta_angle < 0:
                self.vel_left = v_desired * (1 - K*delta_angle)
                self.vel_right = v_desired
            elif delta_angle > 0:
                self.vel_left = v_desired 
                self.vel_right = v_desired * (1 - K*delta_angle)

    def SetVelCurve(self):
        alpha = 1 # gia tốc góc
        K = 100 # hệ số liên hệ giữa vận tốc bánh xe và vận tốc góc
        if not self.flag:
            self.initial_angle = self.current_angle
            self.flag = True
        target_angle = self.calculate_angle_deg(self.path[0][0],self.path[0][1],self.path[1][0],self.path[1][1])
        angle_diff = target_angle - self.initial_angle
        angle_travelled = abs(self.current_angle - self.initial_angle)
        angle_remain = abs(target_angle - self.current_angle)
        if angle_travelled > 180:
            angle_travelled = 360 - angle_travelled
        if angle_remain > 180:
            angle_remain = 360 - angle_remain
        if angle_remain < 1:
            self.flag = None
            return
        v_desired_angle = min(math.sqrt(2 * alpha * angle_travelled) if angle_travelled > 0 else 1,
                                                50,
                                                math.sqrt(2 * alpha * angle_remain))
        if (angle_diff > 0 and abs(angle_diff) < 180) or ((angle_diff < 0) and abs(angle_diff) > 180):
            self.vel_left = - K * v_desired_angle
            self.vel_right = K * v_desired_angle
        else:
            self.vel_left =  K * v_desired_angle
            self.vel_right = - K * v_desired_angle

    def send_data(self):
        if not self.connected:
            print("Not connected. Call connect() first.")
            return
        
        try:
            data_dict ={
                "r": self.vel_right,
                "l": self.vel_left
            }
            # Chuyển dict sang JSON và encode thành bytes
            json_data = json.dumps(data_dict)
            self.sock.sendall(json_data.encode('utf-8'))
            print("Sent:", json_data)
        except socket.error as e:
            print(f"Send failed: {e}")

    def close(self):
        if self.connected:
            self.sock.close()
            self.connected = False
            print("Connection closed.")

    def calculate_angle_deg(self,x1, y1, x2, y2):
        dx = x2 - x1
        dy = y2 - y1
        angle_rad = math.atan2(dy, dx)
        angle_deg = math.degrees(angle_rad)
        return angle_deg



if __name__ == "__main__":
    s = SenData
