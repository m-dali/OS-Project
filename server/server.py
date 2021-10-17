#!/usr/bin/env python3
import socket
import time
HOST = '127.0.0.1'  # Standard loopback interface address (localhost)
PORT = 2021        # Port to listen on (non-privileged ports are > 1023)
BUFF = 100
#The arguments passed to socket() 
# specify the address family and socket type.
#  AF_INET is the Internet address family for IPv4. 
# SOCK_STREAM is the socket type for TCP, 
# the protocol that will be used to 
# transport our messages in the network.
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    conn, addr = s.accept()
    with conn:
        
        # print('Connected by', addr)
        """ length = int(conn.recv(2).decode())
                length: how to make sure
                that it will not take sth from second 
                "send func" that sends the actual message
        print("Length of message:",length)"""
        while True:
            message = conn.recv(BUFF).decode()
            if message == "QUIT":
                exit()
            print(message)
            command = message.split()
            conn.sendall(f"{command}\nOK".encode())
            