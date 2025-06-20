#include <WiFi.h>
#include <WiFiClient.h>
#include <sys/time.h>  // dùng gettimeofday để lấy thời gian chính xác

const char* ssid     = "Long Pho 20";
const char* password = "tienlong94";

WiFiServer server(8000);

// Biến toàn cục để lưu thời gian nhận lần trước
uint64_t prev_receive_ms = 0;

void setup() {
  Serial.begin(115200);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  configTime(0, 0, "pool.ntp.org");  // đồng bộ thời gian NTP
  delay(5000);  // chờ đồng bộ

  server.begin();
  Serial.println("\nESP32 đã sẵn sàng.");
  Serial.print("IP ESP32: ");
  Serial.println(WiFi.localIP());
}

void loop() {
  WiFiClient client = server.available();
  if (client) {
    Serial.println("Client kết nối");
    String data = "";

    while (client.connected()) {
      if (client.available()) {
        char c = client.read();
        if (c == '\n') {
          // Parse timestamp từ Python (ms)
          uint64_t t_python_ms = strtoull(data.c_str(), NULL, 10);

          // Thời gian hiện tại từ ESP32 (ms)
          struct timeval now;
          gettimeofday(&now, NULL);
          uint64_t t_esp32_ms = now.tv_sec * 1000ULL + now.tv_usec / 1000;

          // Tính độ trễ truyền tín hiệu
          int64_t delay_ms = (int64_t)(t_esp32_ms - t_python_ms);

          // Tính khoảng thời gian giữa 2 lần nhận tín hiệu liên tiếp
          int64_t interval_ms = 0;
          if (prev_receive_ms > 0) {
              interval_ms = (int64_t)(t_esp32_ms - prev_receive_ms);
          }
          prev_receive_ms = t_esp32_ms;

          Serial.printf("Python: %llu ms | ESP32: %llu ms | Delay: %lld ms | Interval: %lld ms\n",
                        t_python_ms, t_esp32_ms, delay_ms, interval_ms);

          data = "";
        } else {
          data += c;
        }
      }
    }

    client.stop();
    Serial.println("Client ngắt kết nối");
    prev_receive_ms = 0;  // reset khi mất kết nối
  }
}

