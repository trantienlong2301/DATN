import socket
import json
import time
import math
import struct

HOST = "192.168.1.38"  # Địa chỉ IP của ESP32
PORT = 80              # Cổng mà ESP32 đang lắng nghe
current_position = [0, 0]

# Tạo UDP socket
client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client.settimeout(2.0)
print("Đã tạo UDP socket.")

try:
    while True:
        receive_time = time.time()
        start = [0, 0]
        goal = [1000, 1000]
        d_travelled = math.hypot(current_position[0] - start[0],
                                 current_position[1] - start[1])
        d_remain = math.hypot(current_position[0] - goal[0],
                              current_position[1] - goal[1])
        if d_remain < 100:
            break
        v_desired = min(math.sqrt(2 * 50 * d_travelled) if d_travelled > 0 else 1,
                        100,
                        math.sqrt(2 * 50 * d_remain) if d_remain > 0 else 1)
        control_data = {
            "velocity": v_desired,
            "start": start,
            "goal": goal
        }
        json_data = json.dumps(control_data)
        # Gửi dữ liệu UDP đến ESP32
        client.sendto((json_data + "\n").encode('utf-8'), (HOST, PORT))
        print("Đã gửi:", json_data)
        send_time = time.time()
        elapsed_time = send_time - receive_time
        print("Thời gian gửi:", elapsed_time)

        try:
            # Nhận phản hồi từ ESP32: UDP là dạng datagram, nhận toàn bộ gói
            data, addr = client.recvfrom(1024)
            if len(data) < 4:
                print("Gói nhận không đủ dữ liệu.")
                continue
            header = data[:4]
            msg_length = struct.unpack("!I", header)[0]
            json_payload = data[4:]
            receive_time = time.time()
            elapsed_time = receive_time - send_time
            print("Thời gian phản hồi:", elapsed_time)

            response_data = json.loads(json_payload.decode("utf-8"))
            print("Vị trí hiện tại của robot:")
            print("  x =", response_data["x"])
            print("  y =", response_data["y"])
            current_position = [response_data["x"], response_data["y"]]
        except socket.timeout:
            print("Không nhận phản hồi từ ESP32.")
        time.sleep(0.1)
except KeyboardInterrupt:
    print("Đóng kết nối...")
finally:
    client.close()
    print("Đã đóng kết nối.")
