#include <WiFi.h>
#include <HardwareSerial.h>
#include <TrinamicStepper.h>

#define MOTOR_NUM 2     
int SetSpeeds[MOTOR_NUM] = {0,0};
int MotorId = 1;
unsigned long previousMillis = 0;  
unsigned long previousMillis1 = 0;   
unsigned long previousMillis2 = 0;   
const long MotorInterval = 25;  

// WiFi cấu hình
const char* ssid = "Long Pho 20";
const char* password = "tienlong94";

WiFiServer server(1234);

// UART1 cho Trinamic
TrinamicStepper stepper(Serial1);

char buffer[8];
int dataValue[3] = {0,0,0};
int cnt = 0, num = 0;

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial1.begin(38400, SERIAL_8N1, 16, 17);

  WiFi.begin(ssid, password);
  Serial.println("Kết nối Wi-Fi...");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nĐã kết nối Wi-Fi");
  Serial.print("IP ESP32: ");
  Serial.println(WiFi.localIP());

  server.begin();
  Serial.println("Đã khởi động server TCP");
}

void loop() {
  WiFiClient client = server.available();
  if (client) {
    
    Serial.println("Client mới kết nối.");
    while (client.connected()) {
      if (client.available()) {
        unsigned long currentMillis1 ;
        unsigned long t ;
        unsigned long currentMillis2 ;
        unsigned long t2 ;
        previousMillis1 = currentMillis1;
        char c = client.read();
        switch (c) {
          case '>':
            previousMillis2 = millis();
            cnt = 0;
            num = 0;
            memset(buffer, 0, sizeof(buffer));
            continue;

          case ',':
            if (num < 2) {
              dataValue[num++] = atoi(buffer);
            }
            cnt = 0;
            memset(buffer, 0, sizeof(buffer));
            continue;

          case '\n':
            currentMillis2 = millis();
            t2 = currentMillis2 - previousMillis2;
            Serial.printf("thoi gian xu ly: %d \n",t2);
            if (num < 3) {
              dataValue[num] = atoi(buffer);
            }
            currentMillis1 = millis();
            t = currentMillis1 - previousMillis1;
            Serial.printf("thoi gian nhan: %d \n",t);
            previousMillis1 = currentMillis1;
            Serial.printf("Tốc độ nhận: Trái = %d, Phải = %d, stt = %d\n", dataValue[0], dataValue[1],dataValue[2]);
            SetSpeeds[0] = dataValue[0];
            SetSpeeds[1] = dataValue[1];

            client.println("OK");
            client.flush();
            delay(10);  // Gửi ngay không đọng buffer

            cnt = 0;
            num = 0;
            memset(buffer, 0, sizeof(buffer));
            continue;

          default:
            if (cnt < sizeof(buffer) - 1) {
              buffer[cnt++] = c;
            }
            continue;
        }
      }

      unsigned long currentMillis = millis();
      if (currentMillis - previousMillis >= MotorInterval) {
        previousMillis = currentMillis;
        if (MotorId > MOTOR_NUM) MotorId = 1;
        stepper.rotateRight(MotorId, SetSpeeds[MotorId - 1], true);
        Serial.printf("Motor %d tốc độ = %d\n", MotorId, SetSpeeds[MotorId - 1]);
        MotorId++;
      }
    }
    client.stop();
    Serial.println("Client đã ngắt kết nối.");
  }
}
