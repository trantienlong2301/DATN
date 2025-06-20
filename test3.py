import socket
import time

HOST = '192.168.1.38'  # thay bằng địa chỉ IP của ESP32
PORT = 8000

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    while True:
        # lấy thời gian hiện tại (float giây) và đổi sang mili giây
        timestamp_ms = int(time.time() * 1000)
        msg = f"{timestamp_ms}\n"
        s.sendall(msg.encode())
        print(f"Đã gửi: {timestamp_ms} ms")
        time.sleep(0.01)

