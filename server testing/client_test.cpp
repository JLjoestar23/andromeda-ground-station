#include <stdio.h>
#include <WinSock2.h>
#include <WS2tcpip.h>
#include <assert.h>
#include "uudp.h"


int main(){
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

    // initializing a connection to the desired socket
    // s is the initialized socket
    // (sockaddr*)&addr is pointer to "addr", which is of type sockaddr_in, casted as socketaddr* due to "connects" input expectation of a pointer to socketaddr
    // sizeof(addr), specifies the size in bytes of the desired address to connect to
    result = connect(s, (sockaddr*)&addr, sizeof(addr)); 
    assert(result != SOCKET_ERROR); // checks if connection is established

    // 64-bit int to store packet number sent
    long long sequence = 1;

    // Infinite loop for sending packets
    while (true) {
        data_packet packet; // Initializing variable "packet" of type data_packet
        packet.sequence = sequence; // sets the sequence within data_packet
        packet.timestamp = time(NULL); // sets the timestamp to a null time

        // sending the data packet to socket s
        result = send(s, (char*)&packet, sizeof(data_packet), 0);
        assert(result != SOCKET_ERROR);

        // indexes through sequence
        sequence += 1;
        
    }
}



