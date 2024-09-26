#include <WiFi.h>
#include <WiFiUDP.h>

WiFiUDP udp;
// Test with OLIN-Robotics WiFi but we'll want to start our AP aagain
const char* ssid = "OLIN-ROBOTICS"; // Did not work on OLIN private network - does work on public network
const char* password = "R0B0TS-RULE!";
// const char* ssid = "MiniAvionics"
char serverAddress[] = "192.168.16.122"; // confirm we'll only have one (There is a constraint based on how many people can access WiFi on ESP32?)
//char clientAddress[] = "192.168.4.2"
unsigned int localUdpPort = 8889;
unsigned int MAX_SIZE = 108; // # of floats (27) * 4 (each float takes 4 bytes)

float message[27] = {
  28, 29, 30, 42, 4002, 4, 3.5, 8.5, 9.5, 10.5, 
  99.1, 89.7, 76.5, 80, 90, 100.1, 200.1, 100.1, 
  200, 300.2, 400.1, 400.1, 124.42, 11.1, 24.1, 26.1
  };

// setup the WiFi connection once - this is maintained across function calls
void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.flush();
  Serial.println(ssid); // For debugging purposes - know where it's connecting too
  Serial.flush();
  Serial.println(password); // Also print for debugging purposes
  Serial.flush();
  WiFi.begin(ssid, password);
  // WiFi.softAP(ssid, password); // This should set up the MiniAvionics WiFi
  while (WiFi.status() != WL_CONNECTED) {
    delay(500); // wait for everything to be connected
    Serial.print("Attempting to connect.");
    Serial.println(WiFi.status());
  } 
  Serial.println(serverAddress);
  // TODO: Check if the WiFi is actually connected
  // TODO: Confirm how we get from being connected to actually writing the packet
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("WiFi is connected");
  }
  udp.begin(localUdpPort);
}

// define the max char array and [6] defines max number of char/null terminator. This definition is helpful for the compiler to compute offsets in the array
// Our intention in serializing is to ensure data adheres to a specific format on T/R ends and we know the order bytes should be sent in
void sendArrOverUDP(float message[]) {
  char serializedMessage[MAX_SIZE]; // This is an estimate based on # of strings (28) * (# of chars + 1 for null terminator)
  int offset = 0;
    // TODO: need stopping condition for this
    // we want to loop through the message which is an input and copy it? Where does the serialization happen?
  for (int i = 0; i < 28; i++) {
    memcpy(serializedMessage + offset, &message[i], sizeof(float)); // (address of dest, addr of source, # of bytes to copy)
    offset += sizeof(float); // offset's position changes based on the length of the string so it knows where in the buffer to write next
    if (i < 27) {
      serializedMessage[offset] = ',';
      offset++; // increment offset by 1 because we've added delimiter
      }
    }
  udp.beginPacket(serverAddress, localUdpPort);
  udp.write((const uint8_t*)serializedMessage, offset);
  udp.endPacket(); // Returns 1 if the packet is sent successfully, 0 if otherwise (https://www.arduino.cc/reference/en/libraries/wifi/wifiudp.endpacket/)
  if (udp.endPacket() == 1) {
    Serial.println("Sent successfully...");
  } else {
    Serial.println("Sent unsuccessfully...");
  }
}

void loop() {
  if (WiFi.status() == WL_CONNECTED) {
    sendArrOverUDP(message);
    delay(1000);
  }
}