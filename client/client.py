#!/usr/bin/env python3
import socket

HOST = ''  # The server's hostname or IP address
PORT = 2021        # The port used by the server



def send_message(s: socket.socket,message:str):
    # s.sendall(str(len(message)).encode())  
    # message length TODO how to send size of
    # time.sleep(1)
    s.sendall(message.encode())  # message

def protocolMessage(data:str)->str:
    message = ""
    command=data.split()
    action = command[0]
    len_command = len(command)
    if len_command==1:
        if action in ["lu","lf","disconnect"]:
            message = action.upper()
        elif action == "quit":
            message = action.upper()
        else:
            print("command doesn't exist:", action)  
    elif len_command==2:
        if action in ["read","write","overwrite","overread"]:#TODO enhancements with the updated server server
            message = f"{action.upper()} {command[1]}"
    elif len_command>=3:
        if action == "connect":
            global HOST
            username = command[1]
            HOST = command[2]
            message = f"{action.upper()} {username}"
        elif action == "send":
            text = " ".join(command[2:]).replace('"','')
            size = len(text)
            message = f"MESSAGE {command[1]}\n{size} {text}"
        elif action == "append":#TODO
            text = " ".join(command[1:-1]).replace('"','')
            length = len(text)
            message = f"{action.upper()} {command[-1]}\n{length} {text}"#TODO text and length is sent after reciving respond codes e.g OK or ERROR

        elif action == "appendfile":#TODO
            message = f"{action.upper()} {command[1]} {command[2]}"
    else:
        print("command doesn't exist:", command)
    return message


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    connected = False
    while True:
        data = input("Write command:")
        message = protocolMessage(data)

        if connected == False:
            if data.split()[0]=="connect":
                #TODO wait for sending thread
                s.connect((HOST, PORT))
                connected = True
            else:
                print("try to connect first")
                continue
        elif connected ==True and data.split()[0]=="connect":
            print("you've already connected")
            continue


        if message=="":
            print("try again")
            continue
        send_message(s,message)
        if data == "quit":
            break
        recieved_data = s.recv(100).decode()
        print(f"Recieved from the server: {recieved_data}")
        
