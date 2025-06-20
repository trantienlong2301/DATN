import socket
import time

HOST = '192.168.1.38'  # Thay bằng địa chỉ IP của ESP32
PORT = 8000

prev_receive_time = None

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    print("Kết nối tới ESP32...")
    s.connect((HOST, PORT))
    print("Đã kết nối!")

    while True:
        # Nhận 1 dòng dữ liệu
        data = b''
        while not data.endswith(b'\n'):
            chunk = s.recv(1)
            if not chunk:
                print("ESP32 ngắt kết nối.")
                exit()
            data += chunk

        try:
            line = data.decode().strip()
            parts = line.split(',')
            if len(parts) != 2:
                continue

            count = int(parts[0])
            esp32_time = int(parts[1])  # timestamp từ ESP32 (ms)
            receive_time = int(time.time() * 1000)  # timestamp hiện tại (ms)

            delay = receive_time - esp32_time
            interval = 0
            if prev_receive_time is not None:
                interval = receive_time - prev_receive_time
            prev_receive_time = receive_time

            print(f"[#{count}] ESP32: {esp32_time} | Python: {receive_time} | Delay: {delay} ms | Interval: {interval} ms")

        except Exception as e:
            print("Lỗi:", e)
