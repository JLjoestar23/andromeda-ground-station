#include <WiFi.h>
#include <WiFiUDP.h>

WiFiUDP udp;
// Test with OLIN-Robotics WiFi but we'll want to start our AP again
// const char* ssid = "OLIN-ROBOTICS"; // Did not work on OLIN private network - does work on public network
//char ssid[] = {'O', 'L', 'I', 'N', '-', 'R', 'O', 'B', 'O', 'T', 'I', 'C', 'S', '\0'}; // Try to switch dtypes and see what happens
//const char* password = "R0B0TS-RULE!";
const char* ssid = "MiniAvionics";
char serverAddress[] = "192.168.16.122"; // confirm we'll only have one (There is a constraint based on how many people can access WiFi on ESP32?)
unsigned int localUdpPort = 4210;
unsigned int numArr = 27;
unsigned int MAX_SIZE = 27 * sizeof(float) + 26; // # of floats (27) * 4 (each float takes 4 bytes) + 26 for commas

float message[27] = {
  28, 29, 30, 42, 4002, 4, 3.5, 8.5, 9.5, 10.5, 
  99.1, 89.7, 76.5, 80, 90, 100.1, 200.1, 100.1, 
  200, 300.2, 400.1, 400.1, 124.42, 11.1, 24.1, 26.1
  };

// setup the WiFi connection once - this is maintained across function calls
void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println(ssid); // For debugging purposes - know where it's connecting too
  
  if (!WiFi.softAP(ssid)) {
    Serial.println("Failed to start the soft AP");
  } else {
    Serial.println("Soft AP started successfully");
    IPAddress myIP = WiFi.softAPIP();
    Serial.print("AP IP Address: ");
    Serial.println(myIP.toString());
  }
  udp.begin(localUdpPort);
}

// define the max char array and [6] defines max number of char/null terminator. This definition is helpful for the compiler to compute offsets in the array
// Our intention in serializing is to ensure data adheres to a specific format on T/R ends and we know the order bytes should be sent in
void sendArrOverUDP(float message[]) {
  char serializedMessage[MAX_SIZE]; // This is an estimate based on # of strings (28) * (# of chars + 1 for null terminator)
  int offset = 0;
  for (int i = 0; i < 27; i++) {
    memcpy(serializedMessage + offset, &message[i], sizeof(float)); // (address of dest, addr of source, # of bytes to copy)
    offset += sizeof(float); // offset's position changes based on the length of the string so it knows where in the buffer to write next
    if (i < 26) {
      serializedMessage[offset] = ',';
      offset++; // increment offset by 1 because we've added delimiter
      }
    }
  udp.beginPacket(serverAddress, localUdpPort);
  Serial.printf("Sending packet to %s:%d\n", serverAddress, localUdpPort);
  Serial.print("Packet contents: ");
  // Loop taken from online
  for (int i = 0; i < offset; i++) {
    Serial.printf("%02X ", serializedMessage[i]);  // Print each byte in hex
  }
  Serial.println();
  
  udp.write((const uint8_t*)serializedMessage, offset);
  bool status = udp.endPacket(); // Returns 1 if the packet is sent successfully, 0 if otherwise (https://www.arduino.cc/reference/en/libraries/wifi/wifiudp.endpacket/)
  if (status) {
    Serial.printf("Sent ...");
  } else {
    Serial.println("Sent unsuccessfully...");
  }
}

void loop() {
  sendArrOverUDP(message);
  delay(1000);
}