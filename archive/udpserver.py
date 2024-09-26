import socket

HOST = '0.0.0.0' # IP Address of the server
PORT = 4210

with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
    s.bind((HOST, PORT))
    # new learning - append binary is a valid mode
    with open('udpservertest.txt', 'ab') as save:
        while True:
            data, addr = s.recvfrom(1024)
            if not data: break
            print(data)
            save.write(data)