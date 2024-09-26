import socket

HOST = '192.168.4.1' # IP Address of the server
PORT = 4210

with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
    while True:
        message = input('Type something to send over socket.')
        message = message.encode('utf-8')
        s.sendto(message, (HOST, PORT))