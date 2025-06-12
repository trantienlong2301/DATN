# https://pythonprogramming.net/buffering-streaming-data-sockets-tutorial-python-3/
# https://www.digitalocean.com/community/tutorials/python-socket-programming-server-client
# First import the library
# https://github.com/IntelRealSense/librealsense/tree/master/wrappers/python
import socket
import time 
import os
import pyrealsense2 as rs
import math as m

interval = 10

# Declare RealSense pipeline, encapsulating the actual device and sensors
pipe = rs.pipeline()

# Build config object and request pose data
cfg = rs.config()
cfg.enable_stream(rs.stream.pose)

# Start streaming with requested config
pipe.start(cfg)

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#s.bind((socket.gethostname(), 1243))
s.bind(('127.0.0.1', 8000))
s.listen(1)

server_connection = True

while server_connection:
    # now our endpoint knows about the OTHER endpoint.
    print("Waiting for a reconnection...")
    clientsocket, address = s.accept()
    print(f"New Connection from {address} has been established.")
    #msg = "Welcome to the server!"
    #clientsocket.send(bytes(msg,"utf-8"))
    client_connected = True
    previousMillis = int(round(time.time() * 1000))
    while client_connected:
        currentMillis = int(round(time.time() * 1000))
        if (currentMillis - previousMillis) >= interval:
            previousMillis = currentMillis
            # receive data stream. it won't accept data packet greater than 1024 bytes
            try:
                #recdata = clientsocket.recv(1024).decode()
                # Wait for the next set of frames from the camera
                frames = pipe.wait_for_frames()
                # Fetch pose frame
                pose = frames.get_pose_frame()
                # Print some of the pose data to the terminal
                data = pose.get_pose_data()
                msg = data.translation
                w = data.rotation.w
                x = -data.rotation.z
                y = data.rotation.x
                z = -data.rotation.y
                pitch =  -m.asin(2.0 * (x*z - w*y)) * 180.0 / m.pi;
                roll  =  m.atan2(2.0 * (w*x + y*z), w*w - x*x - y*y + z*z) * 180.0 / m.pi;
                yaw   =  m.atan2(2.0 * (w*z + x*y), w*w + x*x - y*y - z*z) * 180.0 / m.pi;  
                repdata = "{0:.7f},{1:.7f},{2:.7f},{3:.7f},{4:.7f},{5:.7f}".format(data.translation.x,data.translation.y,data.translation.z, pitch, -yaw, -roll) + os.linesep
                clientsocket.send(repdata.encode())  # send data to the client
                print("Frame #{}".format(pose.frame_number))
            except:
                client_connected = False
                clientsocket.close()
                print("The client disconnected...")
                break
            #print("Message from connected client: " + str(recdata))
            #recdata = ''
            #if pose:
pipe.stop()
s.close()