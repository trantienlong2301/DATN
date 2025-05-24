import socket
import time
import select

HOST = '192.168.1.38'
PORT = 1234

RECONNECT_DELAY = 2
SEND_INTERVAL = 0.1

def connect_to_esp32():
    while True:
        try:
            print("🔄 Đang cố gắng kết nối đến ESP32...")
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(10)
            s.connect((HOST, PORT))
            s.settimeout(0)  # non-blocking mode
            print("✅ Đã kết nối đến ESP32.")
            return s
        except Exception as e:
            print(f"❌ Kết nối thất bại: {e}")
            time.sleep(RECONNECT_DELAY)

def receive_full_message(sock, timeout=5):
    data = b""
    start_time = time.time()
    while True:
        ready = select.select([sock], [], [], 0.5)
        if ready[0]:
            chunk = sock.recv(1024)
            if not chunk:
                raise ConnectionError("ESP32 đóng kết nối")
            data += chunk
            if b'\n' in data:
                break
        if time.time() - start_time > timeout:
            raise TimeoutError("Timeout khi nhận dữ liệu từ ESP32")
    return data.decode().strip()

def main_loop():
    s = connect_to_esp32()

    while True:
        try:
            left_speed = 150
            right_speed = 150
            msg = f">{left_speed},{right_speed}\n"
            print(f"📤 Gửi: {msg.strip()}")
            s.sendall(msg.encode())

            data = receive_full_message(s)
            print("📥 ESP32 trả lời:", data)

            time.sleep(SEND_INTERVAL)

        except (socket.error, ConnectionError, TimeoutError) as e:
            print("⚠️ Lỗi truyền/nhận hoặc mất kết nối:", e)
            print("🔌 Đang đóng kết nối và thử lại...")
            s.close()
            time.sleep(RECONNECT_DELAY)
            s = connect_to_esp32()

if __name__ == "__main__":
    main_loop()
