#include <WiFi.h>
#include <WiFiClient.h>
#include <ArduinoJson.h>
// Thay đổi thông tin WiFi theo mạng của bạn
const char* ssid = "Long Pho 20";
const char* password = "tienlong94";
// const char* ssid = "6h50";
// const char* password = "00000000";
float currentx = 0.0;
float currenty = 0.0;
WiFiServer server(80);  // Khởi tạo server ở port 80
uint32_t htonl_custom(uint32_t x) {
  return ((x & 0xFF) << 24) | ((x & 0xFF00) << 8) |
         ((x & 0xFF0000UL) >> 8) | ((x & 0xFF000000UL) >> 24);
}
void setup() {
  
  Serial.begin(115200);
  WiFi.begin(ssid, password);
  Serial.print("Đang kết nối đến WiFi...");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("");
  Serial.print("Đã kết nối, địa chỉ IP: ");
  Serial.println(WiFi.localIP());

  server.begin();  // Bắt đầu server
}

void loop() {
  WiFiClient client = server.available();
  if (client) {
    Serial.println("Client mới kết nối.");
    while (client.connected()){
      String request = "";
      
      while (client.available()) {
        char c = client.read();
        request += c;
      }
      

      if (request.length() > 0) {
        // Parse JSON
        StaticJsonDocument<200> doc;
        DeserializationError error = deserializeJson(doc, request);
        if (!error) {
          float velocity = doc["velocity"];
          float startX = doc["start"][0];
          float startY = doc["start"][1];
          float goalX  = doc["goal"][0];
          float goalY  = doc["goal"][1];
          Serial.printf("Vận tốc: %.2f\n", velocity);
          Serial.printf("Điểm đầu: (%.2f, %.2f)\n", startX, startY);
          Serial.printf("Điểm cuối: (%.2f, %.2f)\n", goalX, goalY);

          currentx += velocity * 0.1;
          currenty += velocity * 0.1 ;
          StaticJsonDocument<100> responseDoc;
          responseDoc["x"] = currentx;
          responseDoc["y"] = currenty;
          String jsonResponse;
          serializeJson(responseDoc, jsonResponse);

          // Tính độ dài của JSON response
          uint32_t len = jsonResponse.length();
          // Chuyển độ dài sang network byte order (big-endian)
          uint32_t header = htonl_custom(len);
          
          // Gửi header 4 byte
          client.write((uint8_t*)&header, sizeof(header));
          // Gửi chuỗi JSON
          client.print(jsonResponse);
          client.flush();
          Serial.println("Đã gửi phản hồi với header.");
        } else {
          client.println("JSON lỗi.");
        }
      }
      delay(10);
    }

    client.stop();
    Serial.println("Ngắt kết nối client.");
  }
}
