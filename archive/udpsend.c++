/* INCLUDE LIBRARIES */
#include <WiFi.h>
#include <WiFiUDP.h>
#include "SPIFFS.h"
#include <iostream>
#include <cstring>

WiFiUDP udp;
unsigned int localUdpPort = 4210;
const char* ssid = "MiniAvionics";
const char* serverAddress = "192.168.4.1";
WiFiServer server(80);
char incomingPacket[255]; // Adjust size as needed
// Init baud rate, port to listen to, and print these values so I know they're correct
void setup() {
  Serial.begin(115200);
  WiFi.softAP(ssid); // Start the ssid access point (was this the error?)
  udp.begin(localUdpPort);  // Start the server with a port to listen to
  Serial.printf("Now listening at IP %s, UDP port %d\n", WiFi.softAPIP().toString().c_str(), localUdpPort);
}

void loop() {
  udp.beginPacket("192.168.4.2", 4210); // move this before if statement so we don't repeatedly open a new UDP packet
  while (Serial.available() == 0) {
  }
  int readInteger = Serial.parseInt(); 
  // String inputString = Serial.readStringUntil('\n'); // take an input until you see a new line character
  udp.write(readInteger);
  udp.endPacket();
  Serial.println(readInteger);
  }