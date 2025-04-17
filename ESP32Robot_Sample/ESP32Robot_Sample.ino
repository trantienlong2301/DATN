#include <WiFi.h>
#include <WebServer.h>
#include "HardwareSerial.h"
#include "TrinamicStepper.h"

#define MOTOR_NUM 3     // Number of the motor module
int SetSpeeds[MOTOR_NUM] = {50,50,50};// default 50%
int MotorId = 1;
unsigned long previousMillis = 0;       // will store last time LED was updated
const long    MotorInterval = 24;       // interval 

TrinamicStepper stepper(Serial2);

void setup() {
  // Initialize SoftwareSerial
  Serial.begin(38400);
  delay(100);  // Wait for stabilization
}

void loop() {
   
    unsigned long currentMillis = millis();
    if (currentMillis - previousMillis >= MotorInterval) {
    previousMillis = currentMillis;
        if(MotorId > 3) MotorId = 1;
        stepper.rotateRight(MotorId, SetSpeeds[MotorId-1], true);
        MotorId++;
        Serial.print("sent. received:");
        Serial.println(stepper.getStatus()); 
    }
 
}

  
