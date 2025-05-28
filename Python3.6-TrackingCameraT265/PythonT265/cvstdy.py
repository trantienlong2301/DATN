
#import sys
#print(sys.path)
#https://stackoverflow.com/questions/7624765/converting-an-opencv-image-to-black-and-white
#https://learnopencv.com/find-center-of-blob-centroid-using-opencv-cpp-python/
import cv2
print(cv2.__version__)
import numpy as np
from matplotlib import pyplot as plt

img = cv2.imread('img.png')
# convert the image to grayscale
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
# convert the grayscale image to binary image
ret,thresh = cv2.threshold(gray,127,255,cv2.THRESH_BINARY)
#cv2.imshow('image', image)
#cv2.imshow('gray', gray)
#cv2.imshow('bw', thresh)

# find contours in the binary image
im2, contours, hierarchy = cv2.findContours(thresh,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)

for c in contours:
   # calculate moments for each contour
   M = cv2.moments(c)

   # calculate x,y coordinate of center
   cX = int(M["m10"] / M["m00"])
   cY = int(M["m01"] / M["m00"])
   cv2.circle(img, (cX, cY), 5, (255, 255, 255), -1)
   cv2.putText(img, "centroid", (cX - 25, cY - 25),cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)


cv2.imshow("Image", img)



#plt.imshow(thresh1,'gray',vmin=0,vmax=255)
cv2.waitKey(0)
cv2.destroyAllWindows()


