#https://matplotlib.org/stable/gallery/lines_bars_and_markers/bar_label_demo.html
def sum(a,b):
	global c
	c = 100
	return (a//b + c)

print(sum(5,2))



if(True == False):
	print('OK',sum(5,2))
elif 3 < 5:
		print(5)
else:
	print('NOK')

spam  = 0
while spam < 10:
	print(spam)
	spam +=spam +1

for i in [0,19,2]:
	print(i)

a = range(1,5)
print(a)


import os
print(os.getcwd())

import matplotlib.pyplot as plt
import numpy as np

plt.plot([1, 2, 3, 4])
plt.ylabel('some numbers')
plt.show()

