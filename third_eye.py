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
import threading

#match as "=" in 10xN px. screenshot
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

#settings
header_offset = 0x435
img_out_raw = 'img_raw.png'
img_out = 'img_processed.bmp'
alarm_sound = 'alarm2.mp3'
notification_sound = "notification2.mp3"
alarm_repeat = True
alarm_repeat_time = 5
image_ref_rate = 1
#debug settings
save_images = False
save_img_bin_dump = False

#functions
def sigint_handler(sig, frame):
    image_buffer_lock.acquire()
    try:
        i = input("Execution suspended, press Enter to resume or Ctrl+C to exit")
    except:
        sys.exit()
    image_buffer_lock.release()
    print("Resumed.")

def check_local_boost():
    global bmp_image_buffer
    global bmp_image_buffer_prev
    while True:
        image_buffer_lock.acquire()
        val1 = bmp_image_buffer.count(0xff)
        val2 = bmp_image_buffer_prev.count(0xff)
        image_buffer_lock.release()
        if val1 > val2:
            print(time.strftime("[%H:%M:%S]") + "Local boosted")
            playsound.playsound(notification_sound)
        bmp_image_buffer_prev = bmp_image_buffer
        time.sleep(1)

def check_neutrals():
    global bmp_image_buffer
    while True:
        image_buffer_lock.acquire()
        pos = bmp_image_buffer.find(b_pattern)
        image_buffer_lock.release()
        if pos != -1:
            print(time.strftime("[%H:%M:%S]") + "Neut found!")
            playsound.playsound(alarm_sound)
            time.sleep(alarm_repeat_time)
            continue
        time.sleep(1)

def image_capture():
    global bmp_image_buffer
    while(True):
        image_buffer_lock.acquire()
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
        image_buffer_lock.release()
        time.sleep(image_ref_rate)

#init
signal.signal(signal.SIGINT, sigint_handler)
bmp_image_buffer_prev = bytes()
bmp_image_buffer = bytes()
image_buffer_lock = threading.Lock()

cn = threading.Thread(target=check_neutrals)
cb = threading.Thread(target=check_local_boost)
ic = threading.Thread(target=image_capture)

cn.start()
cb.start()
ic.start()
#main
print("Third eye online. Ctrl+C for suspend.")
while True:
    time.sleep(1)

