#!/usr/bin/env python3
import os
import socket
from threading import Lock,Semaphore,Thread
HOST = ''          # The server's hostname or IP address
PORT = 2021        # The port used by the server

name = socket.gethostname()
HOST_MSG = socket.gethostbyname(name)#"127.0.0.1"   #if you dont specify address it will took localhost
PORT_MSG = 2022       # for client to listen to messages from server
print(HOST_MSG)
mu_print = Lock()
DISCONNECT_S = Semaphore(1)
DISCONNECT = False
QUIT = False

def protocolMessage(data:str):
    if data=="":
        return "",[]
    command=data.split()
    action = command[0]
    len_command = len(command)
    if len_command==1:
        if action in ["lu","lf","disconnect"]:
            message = action.upper()
        else:
            print("command doesn't exist:", action)  
            return '',[]
    elif len_command==2:
        if action == "read":
            if os.path.exists(command[1]):
                print("file already exists,",command[1])
                return "",[]
        elif action in ["write", "overwrite"]:
            if not os.path.exists(command[1]):
                print("file doesn't exists,",command[1])
                return "",[]
        message = f"{action.upper()} {command[1]}"
            
    elif len_command>=3:
        if action == "connect":
            global HOST
            username = command[1]
            HOST = command[2]
            message = f"{action.upper()} {username}"
        elif action == "send":
            message = f"MESSAGE {command[1]}"
        elif action == "append":
            message = f"{action.upper()} {command[-1]}"
        elif action == "appendfile":
            if not os.path.exists(command[1]):
                print("file doesn't exists,",command[1])
                return "",[]
            message = f"{action.upper()} {command[1]} {command[2]}"    
        else:
            return '',[]
    else:
        print("command doesn't exist:", command)
        return '',[]
    message+='\n' #commands are always terminated by \n character   
    
    return message,command

def recieving_untill_special_char(special_char:str,s:socket.socket)->str:
    full_string= ""
    while True:
        char = s.recv(1).decode()
        if char == special_char:
            break
        full_string+=char
    return full_string

def sending_thread(s:socket.socket):
    global HOST
    isUserConnected = False
    global DISCONNECT
    global QUIT
    while True:
        DISCONNECT_S.acquire() # no need for using semaphore if disconnect wasnt issued in port 2022
        if DISCONNECT:
            isUserConnected = False
            s.close() #old socket closed
            if QUIT:
                DISCONNECT_S.release()
                break
            s = socket.socket() #new created with the same name
            HOST = ''
            DISCONNECT = False
        DISCONNECT_S.release()
        mu_print.acquire()
        data = input(">")
        if data == 'quit':
            data = 'disconnect'
            QUIT = True
        if data == "disconnect":
            DISCONNECT_S.acquire()
        message,command = protocolMessage(data)
        if message == "":
            mu_print.release()
            continue
        if command[0]=="connect":
            if not isUserConnected:
                try:
                    s.connect((HOST, PORT))
                    isUserConnected = True
                except socket.error as e:
                    print(e)
                    s.close()
                    mu_print.release()
                    break
            else:
                print("you already connected, disconnect first",command[1])
                mu_print.release()
                continue
        else:
            if not isUserConnected :
                print("try to connect first")
                mu_print.release()
                continue
        s.sendall(message.encode('ascii'))
        response_code = recieving_untill_special_char('\n',s)
        print(f"Response Code: {response_code}")
        mu_print.release()
        if response_code == "ERROR" and command[0] == "connect":
            isUserConnected = False
            s.close()
            s = socket.socket()
            print("connect again, the given user already registered",command[1])
            continue
        elif response_code == "OK" and command[0] == "connect":
            isUserConnected = True
            print("connected successfully",s)
            continue
        if response_code == "ERROR":
            continue
            
        if command[0] == "send":
            text = " ".join(command[2:]).replace('"','')
            size = len(text)
            s.sendall(f"{size} {text}".encode('ascii'))
        elif command[0] == "lu":
            users = recieving_untill_special_char('\n',s)
            mu_print.acquire()
            print(users)
            mu_print.release()
        elif command[0] == "read":
            filename = command[1]
            size_str = recieving_untill_special_char(' ',s)
            with open(filename,"w") as f:
                f.write(s.recv(int(size_str)).decode())
        elif command[0] == "write":
            filename = command[1]
            size = os.path.getsize(filename)
            with open(filename, 'r') as f:
                s.sendall((f"{size} {f.read()}").encode('ascii'))                   
        elif command[0] == "overread":
            filename = command[1]
            size_str = recieving_untill_special_char(' ',s)
            with open(filename,"w") as f:
                f.write(s.recv(int(size_str)).decode())
        elif command[0] == "lf":
            files = recieving_untill_special_char('\n',s)
            mu_print.acquire()
            print(files)
            mu_print.release()
        elif command[0] == "overwrite":
            filename = command[1]
            size = os.path.getsize(filename)
            with open(filename, 'r') as f:
                s.sendall((f"{size} {f.read()}").encode('ascii'))
        elif command[0] == "append":
            text = " ".join(command[1:-1]).replace('"','')
            size = len(text)
            s.sendall(f"{size} {text}".encode('ascii'))
        elif command[0] == "appendfile":
                filename = command[1]
                size = os.path.getsize(filename)
                with open(filename,"r") as f:
                    s.sendall(f"{size} {f.read()}".encode('ascii'))
def recieving_thread(s:socket.socket):#recieving message after command ends
    global DISCONNECT
    s.bind((HOST_MSG, PORT_MSG))
    s.listen()
    while True:
        conn, addr = s.accept()
        with conn:
            command = recieving_untill_special_char('\n',conn)
            if command == "MESSAGE":
                size_of_msg = recieving_untill_special_char(' ',conn)
                msg = conn.recv(int(size_of_msg)).decode()
                mu_print.acquire()
                print(f"[RECIEVED MESSAGE]: {msg}")
                mu_print.release()
            elif command == "DISCONNECT":
                DISCONNECT = True
                DISCONNECT_S.release()
                if QUIT:
                    s.close()
                    break
recieving_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
recieving_socket.setsockopt( socket.SOL_SOCKET, socket.SO_REUSEADDR, 1 )

sending_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sending = Thread(target=sending_thread,args=(sending_socket,))       #sending proto messages and recieving server response
recieving = Thread(target=recieving_thread,args=(recieving_socket,)) #recieving messages from other clients from the server
sending.start()
recieving.start()
sending.join()
print("sending")
recieving.join()
print("recieving")
