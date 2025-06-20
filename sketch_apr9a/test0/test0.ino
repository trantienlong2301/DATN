#include <WiFi.h>

const char* ssid = "Long Pho 20";
const char* password = "tienlong94";

WiFiServer server1(8000);
WiFiServer server2(8001);

void serverTask1(void* parameter) {
  server1.begin();
  while (true) {
    WiFiClient client1 = server1.available();
    if (client1) {
      Serial.println("[Server 1] Có client kết nối");
      while (client1.connected()) {
        if (client1.available()) {
          String msg = client1.readStringUntil('\n');
          Serial.print("[Server 1] Nhận được: ");
          Serial.println(msg);
        }
        vTaskDelay(10 / portTICK_PERIOD_MS);
      }
      client1.stop();
      Serial.println("[Server 1] Client ngắt kết nối");
    }
    vTaskDelay(10 / portTICK_PERIOD_MS);
  }
}

void serverTask2(void* parameter) {
  server2.begin();
  while (true) {
    WiFiClient client2 = server2.available();
    if (client2) {
      Serial.println("[Server 2] Có client kết nối");
      while (client2.connected()) {

        // Đọc từ Serial Monitor và gửi cho client (Python)
        if (Serial.available()) {
          String user_input = Serial.readStringUntil('\n');
          client2.println(user_input);  // Gửi tới Python
          Serial.print("[ESP32 -> Python]: ");
          Serial.println(user_input);
        }

        vTaskDelay(10 / portTICK_PERIOD_MS);
      }

      client2.stop();
      Serial.println("[Server 2] Client ngắt kết nối");
    }

    vTaskDelay(10 / portTICK_PERIOD_MS);
  }
}

void setup() {
  Serial.begin(115200);
  WiFi.begin(ssid, password);
  Serial.print("Đang kết nối WiFi");

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nĐã kết nối WiFi.");
  Serial.print("IP ESP32: ");
  Serial.println(WiFi.localIP());

  // Tạo 2 task, mỗi task chạy 1 server
  xTaskCreatePinnedToCore(serverTask1, "Server1", 4096, NULL, 1, NULL, 0); // core 0
  xTaskCreatePinnedToCore(serverTask2, "Server2", 4096, NULL, 1, NULL, 1); // core 1
}

void loop() {
  // Không làm gì ở đây
}
