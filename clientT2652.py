import socket
import time

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

client_connection = True
while client_connection:
    time.sleep(1)
    print("Try connect to server...")
    try:
        #s.connect((socket.gethostname(), 1243))d
        print(str(client_connection))
        s.connect(('192.168.158.113', 8000))
        
    except:
         continue

    message = "pose"  # take input
    a = time.time()
    while message.lower().strip() != 'bye':
            try:
                    b = time.time()
                    print(b-a)
                    a = b
                    data = s.recv(1024).decode()  # receive response
                    print('Received from server: ' + data)  # show in terminal
            except:
                print("Lost Connection")
                break
    if  message =='end' or 'bye': 
        client_connection = False
        break
s.close()  # close the connection