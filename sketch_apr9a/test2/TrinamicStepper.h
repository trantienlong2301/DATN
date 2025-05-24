// TrinamicStepper.h
/*
 *
 * Created: 10/17/2024 9:42:43 AM
 * Author : Lac
 */ 

#ifndef TRINAMICSTEPPER_H
#define TRINAMICSTEPPER_H

#include <Arduino.h>

// TMCL Command Definitions
#define TMCL_CMD_ROR  1
#define TMCL_CMD_ROL  2
#define TMCL_CMD_MST  3
#define TMCL_CMD_MVP  4
#define TMCL_CMD_SAP  5 //set axis parameter
#define TMCL_CMD_GAP  6 //get axis parameter
#define TMCL_CMD_STAP 7
#define TMCL_CMD_RSAP 8
#define TMCL_CMD_RFS  13
#define TMCL_CMD_SIO  14
#define TMCL_CMD_GIO  15
#define TMCL_REPLY_ACK 100
#define TMCL_PACKET_LENGTH 9 // TMCL Packet Length
#define BAUD_RATE 38400      // Communication baud rate

//Hardware Serial 2 pins
//#define RXD2 16
//#define TXD2 17
// Define RS485 pins
#define DI_PIN 17     // DI pin (TX) for RS485
#define RO_PIN 16     // RO pin (RX) for RS485
#define DE_PIN 18     // Driver Enable pin
#define RE_PIN 19     // Receiver Enable pin

class TrinamicStepper {
	public:
	// Constructor
	TrinamicStepper(HardwareSerial &serial, long baudRate = 38400);
	// Destructor
	~TrinamicStepper();
	private:
	HardwareSerial &serialPort;
  uint8_t tmclPacket[TMCL_PACKET_LENGTH];
  uint8_t tmclByteIndex;
  uint8_t tmclStatus;
  int32_t tmclValue;
  bool sendCommand(uint8_t moduleAddress, uint8_t command, uint8_t type, uint8_t motor, int32_t value);// Send TMCL command
  bool readResponse(void);// Read response from TMCL module
  uint8_t calculateChecksum(uint8_t *data, uint8_t length);// Calculate checksum
  public:
  // Read feedback functions
  uint8_t getStatus(void);// Read Status response from TMCL module
  int32_t getValue(void);// Read Value response from TMCL module
  // Control functions
  bool rotateRight(uint8_t moduleAddress, int velocity, bool readBack = false);// Rotate motor right
  bool rotateLeft(uint8_t moduleAddress, int velocity, bool readBack = false);// Rotate motor left
  bool stopMotor(uint8_t moduleAddress, bool readBack = false);// Stop motor
};

#endif // TRINAMICSTEPPER_H
