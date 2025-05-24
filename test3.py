import socket
import threading
import time   # <-- thêm import

ESP32_IP = '192.168.1.38'
ESP32_PORT = 1234

def receiver(sock):
    """Continuously receive data from ESP32 and print to console."""
    prev_time = None  # <-- thêm biến lưu thời gian lần nhận trước đó
    while True:
        try:
            data = sock.recv(1024)
            if not data:
                print("Connection closed by ESP32.")
                break

            # Thời điểm hiện tại
            now = time.time()
            msg = data.decode().strip()
            print("[From ESP32]", msg)

            # Nếu đã có prev_time, in khoảng thời gian (s)
            if prev_time is not None:
                delta = now - prev_time
                print(f"[Interval] {delta:.3f} s")

            # Cập nhật prev_time
            prev_time = now

        except ConnectionResetError:
            print("Connection lost.")
            break

def sender(sock):
    """Continuously send data to ESP32 and print send-times."""
    while True:

        left_speed = 150
        right_speed = 150
        msg = f">{left_speed},{right_speed}\n"
        print(f"📤 Gửi: {msg.strip()}")
        sock.sendall(msg.encode())
        
        time.sleep(0.1)   

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print(f"Connecting to {ESP32_IP}:{ESP32_PORT}...")
    sock.connect((ESP32_IP, ESP32_PORT))
    print("Connected!")

    t_recv = threading.Thread(target=receiver, args=(sock,), daemon=True)
    t_send = threading.Thread(target=sender, args=(sock,), daemon=True)

    t_recv.start()
    t_send.start()

    t_send.join()
    print("Main thread exiting.")

if __name__ == "__main__":
    main()
