#!/usr/bin/env python3
import socket
from threading import *
import os

# NUM_OF_USERS = 0
# mu = Lock()
ONLINE_USERS = dict()
name = socket.gethostname()

HOST = "127.0.1.1" #socket.gethostbyname(name)   

PORT = 2021        # Port to listen on (non-privileged ports are > 1023)

PORT_MSG = 2022
BUFF = 100
print(HOST)
def recieving_untill_special_char(special_char:str,s:socket.socket)->str:
    full_string= ""
    while True:
        char = s.recv(1).decode()
        if char == special_char:
            break
        full_string+=char
    return full_string


def clientThread(conn, addr):  
    with conn:
        print('Connected by', addr)
        while True:
            message = conn.recv(BUFF).decode()
            if message == "QUIT":
                exit()
            print(message)
            command = message.split()
            if command[0] == "CONNECT":
                global ONLINE_USERS
                # global mu
                if command[1] not in ONLINE_USERS:
                    # mu.acquire()
                    ONLINE_USERS[command[1]] = "127.0.0."+ str(len(ONLINE_USERS)+1)
                    # mu.release()
                    
                    print(ONLINE_USERS[command[1]])
                    conn.sendall(b"OK\n")
                else:
                    conn.sendall(b"ERROR\n")
            elif command[0] == "LF":
                conn.sendall(b"OK\n")
                files = ""
                for f in os.listdir('.'):
                     if os.path.isfile(f):
                         files+=f+" "
                files+="\n"
                conn.sendall(files.encode())
            elif command[0] == "LU":
                conn.sendall(b"OK\n")
                list_of_users = ""
                for i in ONLINE_USERS:
                    list_of_users+=str(i+" ")
                list_of_users+="\n"
                conn.sendall(list_of_users.encode())
            elif command[0] == "MESSAGE":
                if command[1] in ONLINE_USERS:
                    conn.sendall(b"OK\n")
                    size_str = recieving_untill_special_char(' ',conn) 
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as message_socket:
                        message_socket.connect((ONLINE_USERS[command[1]], PORT_MSG))
                        print(ONLINE_USERS[command[1]], message_socket) 
                        message_socket.sendall(f"MESSAGE\n{size_str} {conn.recv(int(size_str)).decode()}".encode())    #updated    
                else:
                    conn.sendall(b"ERROR\n")
            elif command[0] == "READ":
                filename = command[1]
                if os.path.exists(filename):
                    conn.sendall(b"OK\n")
                    size = os.path.getsize(filename)
                    with open(filename, 'r') as f:
                        conn.sendall((f"{size} {f.read()}").encode())
                else:
                    conn.sendall(b"ERROR\n")
            elif command[0]=="WRITE":
                filename = command[1]
                if os.path.exists(filename):
                    conn.sendall(b"ERROR\n")
                else:
                    conn.sendall(b"OK\n")
                    size_str =recieving_untill_special_char(' ',conn)
                    with open(command[1],"w") as f:
                        f.write(conn.recv(int(size_str)).decode())
            elif command[0] == "OVERREAD":
                filename = command[1]
                if os.path.exists(filename):
                    conn.sendall(b"OK\n") 
                    size = os.path.getsize(filename)
                    with open(filename, 'r') as f:
                        conn.sendall((f"{size} {f.read()}").encode())
                else:
                    conn.sendall(b"ERROR\n")
            elif command[0] == "OVERWRITE":
                filename = command[1]
                conn.sendall(b"OK\n")
            
                size_str = recieving_untill_special_char(' ',conn)
                with open(command[1],"w") as f: 
                    f.write(conn.recv(int(size_str)).decode())
            elif command[0] == "APPEND":
                filename = command[1]
                if os.path.exists(filename):
                    conn.sendall(b"OK\n")
                    size_str = recieving_untill_special_char(' ',conn)
                    with open(filename,"a") as f:
                        f.write(conn.recv(int(size_str)).decode())
                else:
                    conn.sendall(b"ERROR\n")
            elif command[0] == "APPENDFILE":
                filename = command[-1]
                if os.path.exists(filename):
                    conn.sendall(b"OK\n")
                    size_str = recieving_untill_special_char(' ',conn)
                    with open(filename,"a") as f:
                        f.write(conn.recv(int(size_str)).decode())
                else:
                    conn.sendall(b"ERROR\n")
            elif command[0] == "DISCONNECT":
                conn.sendall(b"OK\n")
                for key in ONLINE_USERS:
                    print(key)
                    if ONLINE_USERS[key]==addr[0]:
                        del_addr = ONLINE_USERS.pop(key)
                        break
                    
                print(del_addr)
                with socket.socket() as message_socket:
                    message_socket.connect((del_addr,PORT_MSG))
                    message_socket.sendall("DISCONNECT\n".encode())
                    break

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.setsockopt( socket.SOL_SOCKET, socket.SO_REUSEADDR, 1 )

    s.bind((HOST, PORT))

    while True:
        s.listen(1)
        conn, addr = s.accept()
        newClient = Thread(target=clientThread, args=(conn, addr))
        newClient.start()
