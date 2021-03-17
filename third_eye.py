"""
pip3 install pillow
pip3 install opencv-python
pip3 install playsound
"""

from PIL import ImageGrab
from PIL import Image
from time import sleep
import numpy
import time
import io
import cv2
import playsound
import signal
import sys

pattern = [0xff,0xff,0xff,0xff,0xff,
           0x00,0x00,0x00,0x00,0x00,
           0x00,0x00,0x00,0x00,0x00,
           0x00,0x00,0x00,0x00,0x00,
           0x00,0x00,0x00,0x00,0xff,
           0xff,0xff,0xff,0xff]
b_pattern = bytes(pattern)

#screenshot params
x1 = 692
x2 = 702
y1 = 675
y2 = 1000

#variables
save_images = False
img_out_raw = 'img_raw.png'
img_out = 'img_processed.bmp'
alarm_sound = 'alarm2.mp3'


def sigint_handler(sig, frame):
    try:
        i = input("Execution suspended, press Enter to resume or Ctrl+C to exit")
    except:
        sys.exit()
    print("Resumed.")

signal.signal(signal.SIGINT, sigint_handler)
print("Third eye online. Ctrl+C for suspend.")
while(True):
    cycle_time = 1
    image = ImageGrab.grab(bbox=(x1,y1,x2,y2))

    image = cv2.cvtColor(numpy.array(image), cv2.COLOR_BGR2GRAY)
    if save_images: #save image if enabled
        cv2.imwrite(img_out_raw,image) 
    
    ret,image = cv2.threshold(image, 230, 255, cv2.THRESH_BINARY)
    if save_images: #save image if enabled
        cv2.imwrite(img_out,image)

    ret,buffer = cv2.imencode(".bmp", image)
    bmp_image_buffer = io.BytesIO(buffer).read()

    if b_pattern in bmp_image_buffer:
        print(time.strftime("[%H:%M:%S]") + "Neut found!")
        playsound.playsound(alarm_sound)
        cycle_time = 5
    sleep(cycle_time)
