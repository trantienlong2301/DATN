import socket
import json
import time
import math
import struct
def recvall(sock, n):
    """Nhận đủ n byte từ socket."""
    data = b""
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            return None  # Nếu kết nối bị đóng
        data += packet
    return data

HOST = "172.20.10.4"  # Địa chỉ IP của ESP32
PORT = 80              # Cổng mà ESP32 đang lắng nghe
current_position = [0,0]
# Tạo socket TCP
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, PORT))
print("Đã kết nối đến ESP32")
buffer = ""
try:
    while True:
        receive_time = time.time()
        start = [0,0]
        goal = [1000, 1000]
        d_travelled = math.hypot(current_position[0]-start[0],current_position[1]-start[1])
        d_remain = math.hypot(current_position[0]-goal[0],current_position[1]-goal[1])
        if d_remain < 100:
            break
        v_desired = min(math.sqrt(2 * 50 * d_travelled) if d_travelled > 0 else 1,
                            100,
                            math.sqrt(2 * 50 * d_remain) if d_remain > 0 else 1)
        # Tạo dữ liệu điều khiển
        control_data = {
            "velocity": v_desired,
            "start": start,
            "goal": goal
        }
        time.sleep(0.01)
        # Gửi dữ liệu dạng JSON
        json_data = json.dumps(control_data)
        client.sendall((json_data + "\n").encode('utf-8'))
        print(" da gui:", json_data)
        # Ghi nhận thời gian gửi
        send_time = time.time()
        elapsed_time = send_time - receive_time
        print("time1: ",elapsed_time)
        #Nhận phản hồi từ ESP32 (nếu có)
        try:
            client.settimeout(2.0)
            header = recvall(client, 4)
            if header is None:
                print("Kết nối bị đóng khi nhận header.")
                break

            # Giải mã header theo network byte order ("!I" định dạng số nguyên 4 byte)
            msg_length = struct.unpack("!I", header)[0]

            # Nhận nội dung JSON theo độ dài vừa có được
            json_payload = recvall(client, msg_length)
            if json_payload is None:
                print("Kết nối bị đóng khi nhận payload.")
                break
            receive_time = time.time()

            # Tính thời gian phản hồi
            elapsed_time = receive_time - send_time
            print("time2: ",elapsed_time)

            
            response_data = json.loads(json_payload.decode("utf-8"))
            print("Vị trí hiện tại của robot:")
            print("  x =", response_data["x"])
            print("  y =", response_data["y"])
            current_position = [response_data["x"], response_data["y"]]
            
        except socket.timeout:
            print(" Khong nhan phan hoi.")

        # time.sleep(0.1)  # Đợi 1 giây trước khi gửi lần tiếp theo
except KeyboardInterrupt:
    print("Đóng kết nối...")


finally:
    client.close()
    print(" da dong ket noi.")
