#!/usr/bin/env python3
import socket
from threading import Lock,Semaphore,Thread
import os
import time
import signal
import sys


ONLINE_USERS = dict()
# name = socket.gethostname()
#socket.gethostbyname(name)
HOST_SND = "127.0.1.1"


mu_RW = Lock() #mutex for RW
READER_WRITER = dict()  # Readerwriter[filename] = RW



PORT_SND = 2021        # PORT_SND to listen on (non-privileged ports are > 1023)
PORT_MSG = 2022
print(HOST_SND)
def recieving_untill_special_char(special_char:str,s:socket.socket)->str:
    full_string= ""
    while True:
        char = s.recv(1).decode()
        if char == special_char:
            break
        full_string+=char
    return full_string

class RW:
  def __init__(self, readcount, mu,write_mu):
    self.readcount = readcount
    self.mu = mu
    self.write_mu = write_mu


def clientThread(conn, addr):
    global UPDATING_FILES  
    # global readcount,writecount,write_mu
    with conn:
        print('Connected by', addr)
        while True:
            message = recieving_untill_special_char('\n',conn)
            print(message)
            command = message.split()
            
            if command[0] == "LF":
                conn.sendall(b"OK\n")
                files = ""
                for f in os.listdir('.'):
                     if os.path.isfile(f):
                         files+=f+" "
                files+="\n"
                conn.sendall(files.encode())
            elif command[0] == "DISCONNECT":
                conn.sendall(b"OK\n")
                print(ONLINE_USERS)
                print(addr[0])
                for key in ONLINE_USERS:
                    # if ONLINE_USERS[key]==addr[0]:#use addr[0] here when it is locally available but in localhost it wont work
                    del_addr = ONLINE_USERS.pop(key)
                    print(ONLINE_USERS)
                    break
                print(del_addr)#unbound local variable
                with socket.socket() as message_socket:
                    message_socket.connect((del_addr,PORT_MSG))
                    message_socket.sendall("DISCONNECT\n".encode())
                    break
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
                if filename not in READER_WRITER:
                    READER_WRITER[filename] = RW(0,Lock(),Lock())
                rw = READER_WRITER[filename]
                rw.mu.acquire()
                rw.readcount += 1
                if rw.readcount == 1:
                    rw.write_mu.acquire()
                rw.mu.release()

                
                if os.path.exists(filename):
                    conn.sendall(b"OK\n")
                    size = os.path.getsize(filename)
                    with open(filename, 'r') as f:
                        conn.sendall((f"{size} {f.read()}").encode())
                else:
                    conn.sendall(b"ERROR\n")
                rw.mu.acquire()
                rw.readcount-=1
                if rw.readcount == 0:
                    rw.write_mu.release()
                rw.mu.release()
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
                mu_RW.acquire()
                if filename not in READER_WRITER:
                    READER_WRITER[filename] = RW(0,Lock(),Lock())
                rw = READER_WRITER[filename]
                mu_RW.release()

                rw.mu.acquire()
                rw.readcount += 1
                if rw.readcount == 1:
                    rw.write_mu.acquire()
                rw.mu.release()
                

                if os.path.exists(filename):
                    conn.sendall(b"OK\n") 
                    size = os.path.getsize(filename)
                    with open(filename, 'r') as f:
                        conn.sendall((f"{size} {f.read()}").encode())
                else:
                    conn.sendall(b"ERROR\n")
                rw.mu.acquire()
                rw.readcount-=1
                if rw.readcount == 0:
                    rw.write_mu.release()
                rw.mu.release()
            elif command[0] == "OVERWRITE":
                filename = command[1]
                mu_RW.acquire()
                if filename not in READER_WRITER:
                    READER_WRITER[filename] = RW(0,Lock(),Lock())
                rw = READER_WRITER[filename]
                mu_RW.release()

                rw.write_mu.acquire()
                conn.sendall(b"OK\n")
            
                size_str = recieving_untill_special_char(' ',conn)
                with open(command[1],"w") as f: 
                    f.write(conn.recv(int(size_str)).decode())
                rw.write_mu.release()
            elif command[0] == "APPEND":
                filename = command[1]
                mu_RW.acquire()
                if filename not in READER_WRITER:
                    READER_WRITER[filename] = RW(0,Lock(),Lock())
                rw = READER_WRITER[filename]
                mu_RW.release()
                rw.write_mu.acquire()
                if os.path.exists(filename):
                    conn.sendall(b"OK\n")
                    size_str = recieving_untill_special_char(' ',conn)
                    with open(filename,"a") as f:
                        f.write(conn.recv(int(size_str)).decode())
                else:
                    conn.sendall(b"ERROR\n")
                rw.write_mu.release()       
            elif command[0] == "APPENDFILE":
                filename = command[-1]
                mu_RW.acquire()
                if filename not in READER_WRITER:
                    READER_WRITER[filename] = RW(0,Lock(),Lock())
                rw = READER_WRITER[filename]
                mu_RW.release()
                rw.write_mu.acquire()
                time.sleep(5)
                if os.path.exists(filename):
                    conn.sendall(b"OK\n")
                    size_str = recieving_untill_special_char(' ',conn)
                    with open(filename,"a") as f:
                        f.write(conn.recv(int(size_str)).decode())
                else:
                    conn.sendall(b"ERROR\n")
                rw.write_mu.release()
                
def signal_handler(sig, frame):
    print('You pressed Ctrl+C!')
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:

    s.setsockopt( socket.SOL_SOCKET, socket.SO_REUSEADDR, 1 )
    s.bind((HOST_SND, PORT_SND))

    while True:
        s.listen(1)
        conn, addr = s.accept()
        message = recieving_untill_special_char('\n',conn)
        command = message.split()
        while True:
            if command[0] == "CONNECT":
                if command[1] not in ONLINE_USERS:
                    # mu.acquire()
                    ONLINE_USERS[command[1]] = "127.0.0."+ str(len(ONLINE_USERS)+1)
                    # mu.release()
                    
                    print(ONLINE_USERS[command[1]])
                    conn.sendall(b"OK\n")
                    break
                else:
                    conn.sendall(b"ERROR\n")
        newClient = Thread(target=clientThread, args=(conn, addr))
        newClient.start()

