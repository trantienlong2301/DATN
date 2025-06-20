#include <WiFi.h>
#include <WiFiClient.h>
#include <WiFiServer.h>
#include <sys/time.h>

const char* ssid     = "Long Pho 20";
const char* password = "tienlong94";

WiFiServer server(8000);
WiFiClient client;

uint32_t packet_count = 0;  // đếm số bản tin

void setup() {
  Serial.begin(115200);
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  // Đồng bộ thời gian NTP
  configTime(0, 0, "pool.ntp.org");
  delay(5000); // chờ NTP

  server.begin();
  Serial.println("\nESP32 đã khởi tạo server TCP.");
  Serial.print("IP ESP32: ");
  Serial.println(WiFi.localIP());
}

void loop() {
  

  // Lấy thời gian hiện tại (epoch ms)
  struct timeval now;
  gettimeofday(&now, NULL);
  uint64_t timestamp_ms = now.tv_sec * 1000ULL + now.tv_usec / 1000;

  // Tăng số bản tin
  packet_count++;

  // Gửi chuỗi dữ liệu: số_thứ_tự,timestamp\n
  String message = String(packet_count) + "," + String(timestamp_ms) + "\n";
  client.print(message);
  Serial.print("Đã gửi: ");
  Serial.print(message);

  delay(10);  // gửi mỗi giây
}
