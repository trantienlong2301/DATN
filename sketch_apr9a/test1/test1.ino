#include <WiFi.h>
#include <WiFiClient.h>
#include <ArduinoJson.h>
#include <math.h>
// Thay đổi thông tin WiFi theo mạng của bạn
// const char* ssid = "Long Pho 20";
// const char* password = "tienlong94";
const char* ssid = "6h50";
const char* password = "00000000";
float currentx = 0.0;
float currenty = 0.0;
int a = 0;
unsigned long startReceiveTime = 0;
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
      //startReceiveTime = millis();
      String request = "";
      while (client.available()) {
        if (a ==0){
        unsigned long receiveTime = millis() - startReceiveTime;
        startReceiveTime = millis();
        Serial.printf("Thời gian nhận tín hiệu: %lu ms\n", receiveTime);
        a = 1;
        }
        char c = client.read();
        request += c;
      }
      // unsigned long receiveTime = millis() - startReceiveTime;
      // Serial.printf("Thời gian nhận tín hiệu: %lu ms\n", receiveTime);
      //if (request.length() > 0) {
        // Parse JSON
        a = 0;
        StaticJsonDocument<200> doc;
        DeserializationError error = deserializeJson(doc, request);
        if (!error) {
          float velocity = doc["velocity"];
          float startX = doc["start"][0];
          float startY = doc["start"][1];
          float goalX  = doc["goal"][0];
          float goalY  = doc["goal"][1];
          Serial.printf("Vận tốc: (%.2f)\n", velocity);
          Serial.printf("Điểm đầu: (%.2f, %.2f)\n", startX, startY);
          Serial.printf("Điểm cuối: (%.2f, %.2f)\n", goalX, goalY);
          if (currentx == 0 && currenty == 0){
            currentx = startX;
            currenty = startY;
          }
          StaticJsonDocument<100> responseDoc;
          responseDoc["x"] = startX + velocity;
          responseDoc["y"] = startY + velocity;
          String jsonResponse;
          serializeJson(responseDoc, jsonResponse);

          // Tính độ dài của JSON response
          uint32_t len = jsonResponse.length();
          // Chuyển độ dài sang network byte order (big-endian)
          uint32_t header = htonl_custom(len);

          unsigned long startSendTime = millis();
          // Gửi header 4 byte
          client.write((uint8_t*)&header, sizeof(header));
          // Gửi chuỗi JSON
          client.print(jsonResponse);
          client.flush();

          unsigned long sendTime = millis() - startSendTime;
          Serial.printf("Đã gửi phản hồi với header. Thời gian gửi tín hiệu: %lu ms\n", sendTime);
        } else {
          client.println("JSON lỗi.");
        }
      
      delay(10);
    }

    client.stop();
    Serial.println("Ngắt kết nối client.");
  }
}

