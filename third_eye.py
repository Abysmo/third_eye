"""
pip3 install pillow
pip3 install opencv-python
pip3 install playsound
"""

from PIL import ImageGrab
from PIL import Image
import numpy
import copy
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

#screenshot params (x1-x2 diff should be == 10px)
x1 = 692
x2 = 702
y1 = 675
y2 = 1000

#variables
header_offset = 0x435
img_out_raw = 'img_raw.png'
img_out = 'img_processed.bmp'
alarm_sound = 'alarm2.mp3'
notification_sound = "notification2.mp3"
bmp_image_buffer_prev = bytes()
#debug settings
save_images = False
save_img_bin_dump = False


def sigint_handler(sig, frame):
    try:
        i = input("Execution suspended, press Enter to resume or Ctrl+C to exit")
    except:
        sys.exit()
    print("Resumed.")

def check_local_boost(bin_array, bin_array_prev):
    val1 = bin_array.count(0xff)
    val2 = bin_array_prev.count(0xff)
    if val1 > val2:
        print(time.strftime("[%H:%M:%S]") + "Local boosted")
        playsound.playsound(notification_sound)
    bin_array_prev = bin_array
    return bin_array_prev

def check_neutrals(bin_array):
    if b_pattern in bin_array:
            print(time.strftime("[%H:%M:%S]") + "Neut found!")
            playsound.playsound(alarm_sound)
            cycle_time = 7

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
    bmp_image_buffer = io.BytesIO(buffer)
    bmp_image_buffer.flush()
    bmp_image_buffer.seek(header_offset)
    bmp_image_buffer = bmp_image_buffer.read()
    
    if save_img_bin_dump:
        with open('img_dump', 'w') as file:
            file.write(str(bmp_image_buffer))

    bmp_image_buffer_prev = check_local_boost(bmp_image_buffer,bmp_image_buffer_prev)
    check_neutrals(bmp_image_buffer)
    
    time.sleep(cycle_time)
