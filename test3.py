import socket
import time 

HOST = '172.20.10.3'  # Địa chỉ IP của ESP32
PORT = 80               # Port đang sử dụng trên ESP32

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))
print("Đã kết nối đến ESP32")

try:
    while True:
        # Gửi dữ liệu tới ESP32
        s.sendall(b'Ping from Python\n')
        # Nhận dữ liệu phản hồi từ ESP32
        data = s.recv(1024)
        print('Nhận từ ESP32:', data.decode().strip())
        # Dừng 0.1 giây trước lần gửi tiếp theo
        time.sleep(1)
except KeyboardInterrupt:
    print("Đóng kết nối...")
finally:
    s.close()