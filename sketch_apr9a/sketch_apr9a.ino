#include <WiFi.h>

// Thay đổi thông tin WiFi theo mạng của bạn
const char* ssid = "Long Pho 20";
const char* password = "tienlong94";

WiFiServer server(80);  // Khởi tạo server ở port 80

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
    Serial.println("Có client kết nối");
    
    // Khi đã có client, giữ kết nối và giao tiếp liên tục
    while (client.connected()) {
      // Nếu có dữ liệu từ client, xử lý dữ liệu đó
      if (client.available()) {
        String data = client.readStringUntil('\n');
        Serial.println("Nhận được: " + data);
        // Gửi phản hồi lại cho client
        client.println("Pong from ESP32");
      }
      // Có thể thêm delay ngắn nếu cần tránh lặp quá nhanh
      delay(10);
    }
    
    // Khi client ngắt kết nối, dọn dẹp
    client.stop();
    Serial.println("Client ngắt kết nối");
  }
}

