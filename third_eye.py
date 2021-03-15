"""
pip3 install pillow
pip3 install opencv-python
pip3 install playsound
"""

from PIL import ImageGrab
from PIL import Image
from time import sleep
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

#Images PATH
img_out_raw = 'sc.png'
img_out = 'img_processed.bmp'
alarm_sound = 'alarm2.mp3'

def sigint_handler(sig, frame):
    try:
        i = input("Execution suspended, press Enter to resume or Ctrl+D to exit")
    except:
        sys.exit()
    print("Resumed.")

signal.signal(signal.SIGINT, sigint_handler)
print("Third eye online")
while(True):
    cycle_time = 1
    image = ImageGrab.grab(bbox=(x1,y1,x2,y2))
    image.save(img_out_raw)

    image = cv2.imread(img_out_raw, cv2.IMREAD_GRAYSCALE)
    ret,image = cv2.threshold(image, 230, 255, cv2.THRESH_BINARY)
    cv2.imwrite(img_out,image)

    in_file = open(img_out, "rb") # opening for [r]eading as [b]inary
    data = in_file.read()
    in_file.close()

    if b_pattern in data:
        print("Neut found!")
        playsound.playsound(alarm_sound)
        cycle_time = 5
    sleep(cycle_time)
