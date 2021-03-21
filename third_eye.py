# Mulithreading doesn't work propertly inside python interpreter
# because input() call freezes all the threads unlike terminal.
# in windows terminal(console) all works fine.
"""
pip3 install pillow
pip3 install opencv-python
pip3 install playsound
pip3 install win32gui
"""

from PIL import ImageGrab
from PIL import Image
import numpy
import os
import copy
import time
import io
import cv2
import playsound
import signal
import sys
import threading
import win32gui

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

settings = {
'header_offset' : 0x435,
'img_out_raw' : 'img_raw.png',
'img_out' : 'img_processed.bmp',
'alarm_sound' : 'alarm2.mp3',
'notification_sound' : "notification2.mp3",
'is_running' : True,
'alarm_repeat' : True,
'alarm_repeat_time' : 5,
'image_ref_rate' : 1,
'bmp_image_buffer_prev' : bytes(),
'bmp_image_buffer' : bytes(),
'global_lock' : threading.Lock(),
'eve_win_hwnd' : int(),
#debug settings
'save_images' : False,
'save_img_bin_dump' : False
}

#functions
def check_local_boost():
    global settings
    while True:
        settings['global_lock'].acquire()
        val1 = settings['bmp_image_buffer'].count(0xff)
        val2 = settings['bmp_image_buffer_prev'].count(0xff)
        settings['global_lock'].release()
        if val1 > val2:
            print(time.strftime("[%H:%M:%S]") + "Local boosted")
            playsound.playsound(settings['notification_sound'])
        settings['bmp_image_buffer_prev'] = settings['bmp_image_buffer']
        time.sleep(1)

def check_neutrals():
    global settings
    while True:
        settings['global_lock'].acquire()
        pos = settings['bmp_image_buffer'].find(b_pattern)
        settings['global_lock'].release()
        if pos != -1:
            print(time.strftime("[%H:%M:%S]") + "Neut found!")
            playsound.playsound(settings['alarm_sound'])
            time.sleep(settings['alarm_repeat_time'])
            continue
        time.sleep(1)

def image_capture():
    global settings
    while(True):
        settings['global_lock'].acquire()
        #check is eve window are active, if not - wait.
        while True:
            if settings['eve_win_hwnd'] != win32gui.GetForegroundWindow():
                time.sleep(1)
                continue
            else:
                break

        image = ImageGrab.grab(bbox=(x1,y1,x2,y2))

        image = cv2.cvtColor(numpy.array(image), cv2.COLOR_BGR2GRAY)
        if settings['save_images']: #save image if enabled
            cv2.imwrite(settings['img_out_raw'],image) 
        
        ret,image = cv2.threshold(image, 230, 255, cv2.THRESH_BINARY)
        if settings['save_images']: #save image if enabled
            cv2.imwrite(settings['img_out'],image)

        ret,buffer = cv2.imencode(".bmp", image)
        settings['bmp_image_buffer'] = io.BytesIO(buffer)
        settings['bmp_image_buffer'].flush()
        settings['bmp_image_buffer'].seek(settings['header_offset'])
        settings['bmp_image_buffer'] = settings['bmp_image_buffer'].read()
        
        if settings['save_img_bin_dump']:
            with open('img_dump', 'w') as file:
                file.write(str(settings['bmp_image_buffer']))
        settings['global_lock'].release()
        #print(time.strftime("[%H:%M:%S]") + "img captured") # Debug line
        time.sleep(settings['image_ref_rate'])

def print_variables():
    global settings
    print(f"\
settings[is_running] = {settings['is_running']}\n\
settings[alarm_repeat] = {settings['alarm_repeat']}\n\
settings[alarm_repeat_time] = {settings['alarm_repeat_time']}\n\
settings[image_ref_rate] = {settings['image_ref_rate']}\n\
settings[eve_win_hwnd] = {settings['eve_win_hwnd']} : {win32gui.GetWindowText(settings['eve_win_hwnd'])}\n\
")

#TODO: make alarm repeat and time
def print_usage():
    print("\
s - start\stop script\n\
w - change eve window\n\
u - print usage\n\
v - print settings\n\
r[xx] - set alarm repeat (0 - repeat off)\n\
E - exit script\n\
")

def command_processing():
    global settings
    print(time.strftime("[%H:%M:%S]") + "Third eye online.")
    print_usage()
    while True:
        cmd = input()
        if cmd[0] == 's':
            if settings['is_running'] == True:
                settings['global_lock'].acquire()
                settings['is_running'] = False
                print("Script suspended")
            else:
                settings['global_lock'].release()
                settings['is_running'] = True
                print("Script resumed")
        elif cmd[0] == 'u':
            print_usage()
        elif cmd[0] == 'v':
            print_variables()
        elif cmd[0] == 'E':
            os._exit(0)
        elif cmd[0] == 'w':
            select_eve_window()
        else:
            print("Unknown cmd")

def get_eve_win_list( hwnd, win_list ):
    if ('EVE -' in win32gui.GetWindowText(hwnd)) and (hwnd not in win_list):
        win_list.append(hwnd)

def select_eve_window():
    global settings
    eve_win_list = list()
    settings['global_lock'].acquire()
    while True:
        win32gui.EnumWindows(get_eve_win_list, eve_win_list)
        if len(eve_win_list):
            for i in eve_win_list:
                print(f"[{eve_win_list.index(i)}] : [{win32gui.GetWindowText(i)}]")
        win_num = input("select window or hit Enter to refresh: ")
        if win_num:
            settings['eve_win_hwnd'] = eve_win_list[int(win_num[0])]
            settings['global_lock'].release()
            return


###############-MAIN-###############

#init threads
threads = {
'cn' : threading.Thread(target=check_neutrals),
'cb' : threading.Thread(target=check_local_boost),
'ic' : threading.Thread(target=image_capture),
'cp' : threading.Thread(target=command_processing)
}

select_eve_window()

#start threads
threads['cn'].start()
threads['cb'].start()
threads['ic'].start()
threads['cp'].start()

while True:
    time.sleep(1)