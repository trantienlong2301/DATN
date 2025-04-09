import sys
import asyncio
import aiohttp
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout
from PyQt5.QtCore import QTimer
from qasync import QEventLoop, asyncSlot

esp_ip = "http://192.168.158.239"
speed_value = 0.5  # tốc độ m/s

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.label = QLabel("Đang gửi dữ liệu...")
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)

        # Tạo session aiohttp
        self.session = aiohttp.ClientSession()

        # Gọi lần đầu tiên sau 100ms
        QTimer.singleShot(100, self.send_speed)

    @asyncSlot()  # Chạy coroutine với PyQt
    async def send_speed(self):
        try:
            async with self.session.get(f"{esp_ip}/setSpeed", params={"value": speed_value}) as resp:
                text = await resp.text()
                self.label.setText(f"Đã gửi: {text}")
                print("Đã gửi tốc độ:", text)
        except Exception as e:
            self.label.setText(f"Lỗi: {e}")
            print("Lỗi khi gửi:", e)

        # Lặp lại sau 100ms
        QTimer.singleShot(100, lambda: asyncio.create_task(self.send_speed()))

    async def closeEvent(self, event):
        await self.session.close()
        event.accept()

# Khởi tạo Qt + asyncio event loop
app = QApplication(sys.argv)
loop = QEventLoop(app)
asyncio.set_event_loop(loop)

window = MainWindow()
window.setWindowTitle("Điều khiển ESP32 qua WiFi")
window.show()

with loop:
    loop.run_forever()
