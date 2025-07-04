# https://pythonprogramming.net/buffering-streaming-data-sockets-tutorial-python-3/
# https://www.digitalocean.com/community/tutorials/python-socket-programming-server-client
# First import the library
# https://github.com/IntelRealSense/librealsense/tree/master/wrappers/python
import socket
import time 
import os
import pyrealsense2 as rs
import math as m

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#s.bind((socket.gethostname(), 1243))
s.bind(('127.0.0.1', 8000))
s.listen(1)

interval = 100

# Declare RealSense pipeline, encapsulating the actual device and sensors
pipe = rs.pipeline()
# Build config object and request pose data
cfg = rs.config()
cfg.enable_stream(rs.stream.pose)
# Start streaming with requested config
t265_ok = False

print("Hello, this is T265 server")

while not t265_ok:
    try:
        pipe.start(cfg)
        t265_ok = True
    except:
        print("The device was not connected")
        time.sleep(1) # Sleep for 1 seconds
        print("Reconnecting...")

while t265_ok:
    # now our endpoint knows about the OTHER endpoint.
    print("Waiting for a reconnection...")
    clientsocket, address = s.accept()
    print(f"New Connection from {address} has been established.")
    client_connected = True
    previousMillis = int(round(time.time() * 1000))
    while client_connected:
        currentMillis = int(round(time.time() * 1000))
        if (currentMillis - previousMillis) >= interval:
            previousMillis = currentMillis
            # receive data stream. it won't accept data packet greater than 1024 bytes
            #recdata = clientsocket.recv(1024).decode()
            try:   
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
                repdata = "{0:.3f},{1:.3f},{2:.3f},{3:.3f},{4:.3f},{5:.3f}".format(1000*data.translation.x,1000*data.translation.y,1000*data.translation.z, pitch, -yaw, -roll) + os.linesep
            except:
                print("The connection is lost")
                try:
                    print("Reconnecting...")
                    pipe.start(cfg)
                except:
                    time.sleep(1) # Sleep for 1 seconds
                continue
            try:    
                clientsocket.send(repdata.encode())  # send data to the client
                print("Frame #{}".format(pose.frame_number))
            except:
                client_connected = False
                clientsocket.close()
                print("The client disconnected...")
                break
pipe.stop()
s.close()