#include <WiFi.h>
#include <WebServer.h>

// Cấu hình WiFi
const char* ssid = "RedmiK60";
const char* password = "123456788";

// Tạo web server chạy ở cổng 80
WebServer server(80);

// Biến tốc độ và vị trí robot (giả lập)
float speed = 0;
float position = 0;

unsigned long lastUpdate = 0;

void handleSetSpeed() {
  if (server.hasArg("value")) {
    speed = server.arg("value").toFloat();
    server.send(200, "text/plain", "Toc do da cap nhat: " + String(speed));
  } else {
    server.send(400, "text/plain", "Thiếu tham số tốc độ");
  }
}

void handleGetPosition() {
  server.send(200, "text/plain", String(position));
}

void setup() {
  Serial.begin(115200);

  WiFi.begin(ssid, password);
  Serial.print("Đang kết nối WiFi...");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nĐã kết nối!");
  Serial.println(WiFi.localIP());  // In địa chỉ IP của ESP32

  // Đăng ký các route
  server.on("/setSpeed", handleSetSpeed);
  server.on("/getPosition", handleGetPosition);

  server.begin();
}

void loop() {
  server.handleClient();

  // Giả lập robot di chuyển mỗi 100ms
  if (millis() - lastUpdate >= 100) {
    position += speed * 0.1;  // cập nhật vị trí theo tốc độ (x = v * t)
    lastUpdate = millis();
  }
}
