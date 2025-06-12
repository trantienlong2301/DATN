import socket
import time

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

client_connection = True
while client_connection:
    time.sleep(1)
    print("Try connect to server...")
    try:
        #s.connect((socket.gethostname(), 1243))
        print(str(client_connection))
        s.connect(('127.0.0.1', 8000))
        
    except:
         continue

    message = "pose"  # take input

    while message.lower().strip() != 'bye':
            message = input(" -> ")  # again take input
            try:
                for _ in range(1):
                    s.send(message.encode())  # send message
                    time.sleep(0.001)
                    data = s.recv(1024).decode()  # receive response
                    print('Received from server: ' + data)  # show in terminal
            except:
                print("Lost Connection")
                break
    if  message =='end' or 'bye': 
        client_connection = False
        break
s.close()  # close the connection