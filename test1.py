import asyncio
import aiohttp

# Địa chỉ IP của ESP32, cập nhật theo mạng của bạn
esp_ip = "http://192.168.158.239"

# Hàm gửi tốc độ và nhận vị trí từ ESP32
async def control_robot(session, speed_value):
    try:
        # Gửi tốc độ đến ESP32
        async with session.get(f"{esp_ip}/setSpeed", params={"value": speed_value}) as resp:
            setSpeed_response = await resp.text()
            print("Cập nhật tốc độ:", setSpeed_response)

        # Lấy vị trí hiện tại của robot
        async with session.get(f"{esp_ip}/getPosition") as resp:
            position = await resp.text()
            print("Vị trí robot:", position)
    except Exception as e:
        print("Lỗi:", e)

# Main loop chạy liên tục mỗi 0.1 giây
async def main():
    # Có thể cấu hình timeout nếu cần
    async with aiohttp.ClientSession() as session:
        # Ví dụ: tốc độ mong muốn có thể được tính toán hoặc lấy từ cảm biến
        speed_value = 0.5  # ví dụ: 0.5 m/s
        while True:
            await control_robot(session, speed_value)
            # Chờ không chặn 0.1 giây
            await asyncio.sleep(0.1)

# Chạy chương trình bất đồng bộ
asyncio.run(main())