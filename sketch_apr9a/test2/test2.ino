#include <WiFi.h>

// Thay bằng SSID và password của bạn
const char* ssid     = "Long Pho 20";
const char* password = "tienlong94";

WiFiServer server(1234);
WiFiClient client;
bool tasksCreated = false;

// Task để đọc dữ liệu từ Python
void ReadTask(void* pvParameters) {
  WiFiClient* cli = (WiFiClient*) pvParameters;
  static unsigned long prevRecvTime = 0;
  while (cli->connected()) {
    if (cli->available()) {
      unsigned long now = millis();
      String msg = cli->readStringUntil('\n');
      Serial.print("[From Python] ");
      Serial.println(msg);

      if (prevRecvTime != 0) {
        unsigned long delta = now - prevRecvTime;
        Serial.print("[Interval] ");
        Serial.print(delta);
        Serial.println(" ms");
      }

      // Cập nhật prevRecvTime
      prevRecvTime = now;
    }
    vTaskDelay(10 / portTICK_PERIOD_MS);
  }
  vTaskDelete(NULL);
}

// Task để gửi dữ liệu đến Python
void WriteTask(void* pvParameters) {
  WiFiClient* cli = (WiFiClient*) pvParameters;
  int counter = 0;
  while (cli->connected()) {
    String out = "ESP32 says hello #" + String(counter++);
    cli->println(out);
    // Serial.print("[To Python] ");
    // Serial.println(out);
    vTaskDelay(100 / portTICK_PERIOD_MS);  // send every 1 second
  }
  vTaskDelete(NULL);
}

void setup() {
  Serial.begin(115200);
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    Serial.print('.');
    delay(500);
  }
  Serial.println();
  Serial.print("Connected! IP address: ");
  Serial.println(WiFi.localIP());

  server.begin();
  Serial.println("TCP server started on port 1234");
}

void loop() {
  // Accept new client
  if (!tasksCreated) {
    client = server.available();
    if (client) {
      Serial.println("Python client connected!");
      // Tạo 2 task song song, truyền con trỏ client vào
      xTaskCreatePinnedToCore(
        ReadTask, "ReadTask", 4096, &client, 1, NULL, 0
      );
      xTaskCreatePinnedToCore(
        WriteTask, "WriteTask", 4096, &client, 1, NULL, 1
      );
      tasksCreated = true;
    }
  }
  delay(10);
}
