#include <stdio.h>
#include <WinSock2.h>
#include <WS2tcpip.h>
#include <assert.h>
#include "uudp.h"

int main() {
    // iniitalizing WS2 Library
    int result; // declaring an int for initialization status checks
    WSAData wsa; // declaring wsa as a type WSAData
    result = WSAStartup(MAKEWORD(2,2), &wsa); //  initializing Winsock to latest supported version, return is stored as "result"
    assert(result == NO_ERROR); // checks if it was properly initialized

    // initializing the socket as variable "s"
    // AF_INET (Address Family - Internet), indicates usage of IPV4
    // SOCK_DGRAM (Socket Type: Datagram), specifies the socket type as "Datagram"
    // IPPROTO_UDP, specifies the socket should operate with UDP as a transport protocol
    SOCKET s = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
    assert(s != INVALID_SOCKET); // checks that the socket was initialized properly

    sockaddr_in addr; // declares "addr" as a type sockaddr_in; specifies endpoint address for sockets using IPV4; contains info relating to address family, port number, and IP address
    addr.sin_addr.s_addr = inet_addr("127.0.0.1"); // sets the IP address in "addr" 
    addr.sin_family = AF_INET; // sets the address family of the socket to use IPV4
    addr.sin_port = htons(4000); // sets the port number for the socket; htons() converts port number from host byte order to network byte order (for compatibility)

    // bind and listen to on the port specified on the client side
    // s is the initialized socket
    // (sockaddr*)&addr is pointer to "addr", which is of type sockaddr_in, casted as sockaddr* due to "connects" input expectation of a pointer to sockaddr
    // sizeof(addr), specifies the size in bytes of the desired address to connect to
    result = bind(s, (sockaddr*)&addr, sizeof(addr)); 
    assert(result != SOCKET_ERROR);

    data_packet packet; // initializing variable "packet" of type data_packet

    long long total_packets = 0; // counting total number of packets sent by client
    long long packets_recieved = 0; // counting number of packets recieved
    long long last_sequence = -1; // stores the sequence ID of the last packet, keeps track of order
    long long out_of_order = 0; // counting out of order packets

    long long last_packet_arrival_time = -1; // stores last packet's arrival time
    long long acc_delay = 0; // accumulated delay, used to calculate average jitter

    while (true) {
        // recieve the packet and write its data to the packet struct
        result = recv(s, (char*)&packet, sizeof(data_packet), 0);
        assert(result != SOCKET_ERROR);

        long long arrival_time = time(NULL); // Calculating arrival time

        // if not the first packet, calculate delay
        if (last_packet_arrival_time != -1) {
            acc_delay += arrival_time - last_packet_arrival_time;
        }

        // if the current packet sequence is larger than last, update total packet count
        if (packet.sequence > last_sequence) {
            total_packets = packet.sequence;
        } else {
            // if it's not the latest packet, packet is out of order
            out_of_order += 1;
        }

        packets_recieved += 1; // update counter because we recieved a packet

        // updating last values to current values for next loop
        last_sequence = packet.sequence;
        last_packet_arrival_time = arrival_time;
        

        double loss = (1 - (double)packets_recieved / total_packets) * 100; // calculating % of packets lost
        
        double jitter = (double)acc_delay / packets_recieved; // calculating average jitter

        /*
        printf("Loss: %.1f\n", loss);
        printf("Jitter: %.0fms\n", jitter * 1000);
        printf("Out of order: %lld\n", out_of_order);
        
        if (packet.sequence % 10) {
            printf("%s\n", packet.test_string);
        }
        */
        
        printf("%s\n", packet.test_string);
        
    }

}



