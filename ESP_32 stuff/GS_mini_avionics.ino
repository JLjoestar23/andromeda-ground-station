/* INCLUDE LIBRARIES */
#include <WiFi.h>
#include <WiFiUDP.h>
#include "SPIFFS.h"
#include <iostream>
#include <string>
#include <cstring>

WiFiUDP udp;
unsigned int localUdpPort = 4210;
char incomingPacket[255];
const char* ssid = "MiniAvionics";
const char* serverAddress = "192.168.4.1";

WiFiServer server(80);

void setup() {
  Serial.begin(115200);

  WiFi.softAP(ssid);  // Set up the access point
  if (!WiFi.softAP(ssid)) {
    Serial.println("Failed to start the soft AP");
  } else {
    Serial.println("Soft AP started successfully");
  }

  udp.begin(localUdpPort);  // Start the server with a port to listen to

  Serial.printf("Now listening at IP %s, UDP port %d\n", WiFi.softAPIP().toString().c_str(), localUdpPort);

  // Check if the log file exists in the SPIFFS system on ESP32
  if (!SPIFFS.begin(true)) {
    Serial.println("An Error has occured while mounting");
  } else {
    Serial.println("SPIFFS mounted successfuly");
  }

  Serial.println(SPIFFS.exists("/4_21_2082_refactored.txt"));
}

void loop() {
  int packetSize = udp.parsePacket();  // parse the incoming packet size
  if (packetSize) {
    memset(incomingPacket, 0, sizeof(incomingPacket));
    int len = udp.read(incomingPacket, sizeof(incomingPacket) - 1);
    if (len > 0) {
      incomingPacket[len] = 0;
    }
    Serial.printf("Received packet of size %d from %s:%d\n    (Hex: %s)\n", packetSize, udp.remoteIP().toString().c_str(), udp.remotePort(), incomingPacket);
    if (strcmp(incomingPacket, "start") == 0) {
      Serial.println("Start command received. Sending file.");
      sendFileOverUDP();
    } else {
      Serial.println("Failed to open file for reading"); // print this line every time you don't get "start" string from the client side
    }
  }
}

void sendFileOverUDP() {
  File file = SPIFFS.open("/4_21_2082_refactored.txt");
  char fileBuffer[128];
  while (file.available()) {
    String fileString = file.readStringUntil('\n'); 
    udp.beginPacket("192.168.4.2", 4210);  // prepares to start sending data over UDP
    const char* buffer = fileString.c_str();
    udp.write((const uint8_t*)fileString.c_str(), fileString.length()); // change from length() to strlen() so we get the length in valid format
    udp.endPacket();
  }
  file.close();
}