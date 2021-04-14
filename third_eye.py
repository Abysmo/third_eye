"""
pip3 install pillow
pip3 install opencv-python
pip3 install playsound
pip3 install win32gui
pip3 install keyboard
"""

from PIL import ImageGrab
from PIL import Image
from distutils.util import strtobool
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
import keyboard

#match as "=" in 10xN px. screenshot
pattern = [0xff,0xff,0xff,0xff,0xff,
           0x00,0x00,0x00,0x00,0x00,
           0x00,0x00,0x00,0x00,0x00,
           0x00,0x00,0x00,0x00,0x00,
           0x00,0x00,0x00,0x00,0xff,
           0xff,0xff,0xff,0xff]
b_pattern = bytes(pattern)

'''
#screenshot params

(x2-x1 diff should be == 10px) it maches with pattern above.
If diff x2-x1 is changed - match pattern should be updated.
For convenience debug param save_img_bin_dump is added. 
It it set as True - script saves bitmap hex dump near itself,
it can be analysed manually with hex editor to find desired pattern
'''
screenshot_params = {
'scr_x1' : int(),
'scr_x2' : int(),
'scr_y1' : int(),
'scr_y2' : int()
}

settings = {
#static
'header_offset' : 0x435,
'is_running' : True,
'scr_rect_highlight' : False,
'bmp_image_buffer_prev' : bytes(),
'bmp_image_buffer' : bytes(),
'global_lock' : threading.Lock(),
'sound_lock' : threading.Lock(),
'eve_win_hwnd' : int(),
'scr_rect_blinkrate' : 5,
#files
's_file' : 'user.settings',
'img_out_raw' : 'img_raw.png',
'img_out' : 'img_processed.bmp',
'alarm_sound' : 'audio/alarm2.mp3',
'notification_sound' : 'audio/notification2.mp3',
#eve screen
'x1' : int(),
'y1' : int(),
'x2' : int(),
'y2' : int(),
#settings
'alarm_repeat_time' : 5,
'image_ref_rate' : 1,
'save_event_log' : False,        #TODO
#debug settings
'save_images' : False,
'save_img_bin_dump' : False,
}

#functions
def t_check_local_boost(settings):
    while True:
        settings['global_lock'].acquire()
        val1 = settings['bmp_image_buffer'].count(0xff)
        val2 = settings['bmp_image_buffer_prev'].count(0xff)
        settings['global_lock'].release()
        if val1 > val2:
            print(time.strftime("[%H:%M:%S]") + "Local boosted")
            settings['sound_lock'].acquire()
            playsound.playsound(settings['notification_sound'])
            settings['sound_lock'].release()
        settings['bmp_image_buffer_prev'] = settings['bmp_image_buffer']
        time.sleep(settings['image_ref_rate'])

def t_check_neutrals(settings):
    is_alarmed = False
    while True:
        settings['global_lock'].acquire()
        pos = settings['bmp_image_buffer'].find(b_pattern)
        settings['global_lock'].release()
        if pos != -1 and settings['alarm_repeat_time'] != 0:
            if is_alarmed == False: #print once per event
                print(time.strftime("[%H:%M:%S]") + "Neut found!")
            settings['sound_lock'].acquire()
            playsound.playsound(settings['alarm_sound'])
            settings['sound_lock'].release()
            is_alarmed = True
            time.sleep(settings['alarm_repeat_time'])
            continue
        elif pos != -1 and pos and settings['alarm_repeat_time'] == 0:
            if is_alarmed == False: # reset when neutral leaves zone
                print(time.strftime("[%H:%M:%S]") + "Neut found!")
                settings['sound_lock'].acquire()
                playsound.playsound(settings['alarm_sound'])
                settings['sound_lock'].release()
                is_alarmed = True
            time.sleep(settings['image_ref_rate'])
            continue
        else:
            is_alarmed = False

        time.sleep(settings['image_ref_rate'])

def t_image_capture(settings):
    while(True):
        settings['bmp_image_buffer'] = b'0x00'
        #check is eve window are active, if not - wait.
        if settings['eve_win_hwnd'] == win32gui.GetForegroundWindow():
            settings['global_lock'].acquire()
            image = ImageGrab.grab(bbox=(\
            screenshot_params['scr_x1'], \
            screenshot_params['scr_y1'], \
            screenshot_params['scr_x2'], \
            screenshot_params['scr_y2']))

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
            #print(time.strftime("[%H:%M:%S]") + "img captured") # Debug line
            settings['global_lock'].release()
        
        time.sleep(settings['image_ref_rate'])

def print_variables(settings, screenshot_params):
    print(f"\
settings[is_running] = {settings['is_running']}\n\
settings[alarm_repeat_time] = {settings['alarm_repeat_time']}\n\
settings[image_ref_rate] = {settings['image_ref_rate']}\n\
settings[save_event_log] = {settings['save_event_log']}\n\
settings[eve_win_hwnd] = {settings['eve_win_hwnd']} : {win32gui.GetWindowText(settings['eve_win_hwnd'])}\n\
Screenshot zone param :\n\
screenshot_params['scr_x1'] = {screenshot_params['scr_x1']}\n\
screenshot_params['scr_y1'] = {screenshot_params['scr_y1']}\n\
screenshot_params['scr_x2'] = {screenshot_params['scr_x2']}\n\
screenshot_params['scr_y2'] = {screenshot_params['scr_y2']}\n\
EVE window param :\n\
settings['x1'] = {settings['x1']}\n\
settings['y1'] = {settings['y1']}\n\
settings['x2'] = {settings['x2']}\n\
settings['y2'] = {settings['y2']}")

def print_usage():
    print("\
s - start\stop script\n\
w - change eve window\n\
u - print usage\n\
p - print settings\n\
n - save settings\n\
R [xx] - set image refresh rate in sec. (can't be zero or negative) \n\
r [xx] - set alarm repeat rate in sec. (0 - repeat off, can't be negative)\n\
t - setup standings segment position\n\
E - exit script\n\
")

def t_command_processing(settings, screenshot_params):
    global threads
    while True:
        cmd = input()
        if len(cmd) == 0:
            print("Empty commandline.")
            continue
        if cmd[0] == 's':
            if settings['is_running'] == True:
                settings['global_lock'].acquire()
                settings['is_running'] = False
                print(time.strftime("[%H:%M:%S]") + "Script suspended")
            else:
                settings['global_lock'].release()
                settings['is_running'] = True
                print(time.strftime("[%H:%M:%S]") + "Script resumed")
        elif cmd[0] == 'u':
            print_usage()
        elif cmd[0] == 'p':
            print_variables(settings, screenshot_params)
        elif cmd[0] == 'n':
            save_settings(settings, screenshot_params)
        elif cmd[0] == 'E':
            os._exit(0)
        elif cmd[0] == 'w':
            select_eve_window(settings)
        elif cmd[0] == 't':
            setup_scr_zone(settings, screenshot_params)
        elif cmd[0] == 'r':
            try:
                cmd_val = cmd.split("r ")[1]
                cmd_val = int(cmd_val)
                assert cmd_val <= 99 and cmd_val >= 0
            except:
                print("wrong alarm repeat value")
            else:
                settings['alarm_repeat_time'] = cmd_val
                print(f"New alarm repeat value is : {settings['alarm_repeat_time']}")
        elif cmd[0] == 'R':
            try:
                cmd_val = cmd.split("R ")[1]
                cmd_val = int(cmd_val)
                assert cmd_val <= 99 and cmd_val > 0
            except:
                print("Wrong image refresh value !")
            else:
                settings['image_ref_rate'] = cmd_val
                print(f"New image refresh value is : {settings['image_ref_rate']}")
        else:
            print("Unknown cmd")

def get_eve_win_list(hwnd, win_list):
    if ('EVE -' in win32gui.GetWindowText(hwnd)) and (hwnd not in win_list):
        win_list.append(hwnd)

def select_eve_window(settings):
    eve_win_list = list()
    while True:
        win32gui.EnumWindows(get_eve_win_list, eve_win_list)
        if len(eve_win_list):
            for i in eve_win_list:
                print(f"[{eve_win_list.index(i)}] : [{win32gui.GetWindowText(i)}]")
        win_num = input("select window or hit Enter to refresh: ")
        if win_num:
            settings['eve_win_hwnd'] = eve_win_list[int(win_num[0])]
            win32gui.ShowWindow(settings['eve_win_hwnd'], 1) #activeate window to get it size
            (settings['x1'],
            settings['y1'],
            settings['x2'],
            settings['y2']) = win32gui.GetWindowRect(settings['eve_win_hwnd']) #get win size
            win32gui.ShowWindow(settings['eve_win_hwnd'], 6) # hide window
            return

def t_highlight_scr_zone(settings, screenshot_params):
    #to work with active windows we also need device context (DC)
    win_dc = win32gui.GetDC(settings['eve_win_hwnd']) 
    blink_val = 1 / settings['scr_rect_blinkrate']
    while True:
        while settings['scr_rect_highlight']:
            #draw rect bit larger than actual size 
            #to prevent highlight frame captured in screen
            win32gui.DrawFocusRect(win_dc,\
            (screenshot_params['scr_x1']-1, \
            screenshot_params['scr_y1']-1, \
            screenshot_params['scr_x2']+1, \
            screenshot_params['scr_y2']+1))
            time.sleep(blink_val)
            continue
        time.sleep(2)

def setup_scr_zone(settings, screenshot_params):
    print('Setup standings zone in eve window.\n\
Use Numpad + and - for zone resize\n\
Use Arrows for zone moving\n\
Press Enter for finish setup')
    settings['global_lock'].acquire()
    settings['scr_rect_highlight'] = True #unblock highlight thread
    while True:
        k = keyboard.read_event(suppress=True) #get two events after one keystroke.(key press\release) 
        if k.name == "up":
            if screenshot_params['scr_y1'] - 1 > settings['y1']:
                screenshot_params['scr_y1'] -= 1
                screenshot_params['scr_y2'] -= 1
        elif k.name == "down":
            if screenshot_params['scr_y2'] + 1 < settings['y2']:
                screenshot_params['scr_y1'] += 1
                screenshot_params['scr_y2'] += 1
        elif k.name == "left":
            if screenshot_params['scr_x1'] - 1 > settings['x1']:
                screenshot_params['scr_x1'] -= 1
                screenshot_params['scr_x2'] -= 1
        elif k.name == "right":
            if screenshot_params['scr_x2'] + 1 < settings['x2']:
                screenshot_params['scr_x1'] += 1
                screenshot_params['scr_x2'] += 1
        elif k.name == "+":
            if screenshot_params['scr_y1'] - 3 > settings['y1']:
                screenshot_params['scr_y1'] -= 3
        elif k.name == "-":
            if screenshot_params['scr_y2'] - screenshot_params['scr_y1'] > 30:
                screenshot_params['scr_y1'] += 3
        elif k.name == "enter" and k.event_type == 'down':
            print('Standings zone setup complete.')
            settings['global_lock'].release()
            settings['scr_rect_highlight'] = False #lock highlight thread
            return

def save_settings(settings, screenshot_params):
    # !!! setting sequence should be the same in write and read functions
    try:
        sav_file = open(settings['s_file'], 'w')
        sav_file.writelines("\n".join((
            str(settings['scr_rect_blinkrate']),    #0
            str(settings['alarm_repeat_time']),     #1
            str(settings['image_ref_rate']),        #2
            str(settings['save_event_log']),        #3
            str(screenshot_params['scr_x1']),       #4
            str(screenshot_params['scr_x2']),       #5
            str(screenshot_params['scr_y1']),       #6
            str(screenshot_params['scr_y2']),       #7
            )))
    except Exception as e:
        print(f"\nCannot write settings. Error occur.\n{e}\n")
    else:
        print("Setting saved successfully")

def read_settings(settings, screenshot_params):
    # !!! setting sequence should be the same in write and read functions 
    try :
        sav_file = open(settings['s_file'], 'r')
        sav_list = sav_file.readlines()
        settings['scr_rect_blinkrate'] = int(sav_list[0])
        settings['alarm_repeat_time'] = int(sav_list[1])
        settings['image_ref_rate'] = int(sav_list[2])
        settings['save_event_log'] = bool(strtobool(sav_list[3].rstrip('\n')))
        screenshot_params['scr_x1'] = int(sav_list[4])
        screenshot_params['scr_x2'] = int(sav_list[5])
        screenshot_params['scr_y1'] = int(sav_list[6])
        screenshot_params['scr_y2'] = int(sav_list[7])
    except Exception as e:
        print("\nCannot read settings. Loading default values.\n")
        print(e)
    else:
        print("\nSetting loaded successfully\n")


##############################-MAIN-##############################

#init threads
threads = {
'cn' : threading.Thread(target=t_check_neutrals, args=(settings, )),
'cb' : threading.Thread(target=t_check_local_boost, args=(settings, )),
'ic' : threading.Thread(target=t_image_capture, args=(settings, )),
'cp' : threading.Thread(target=t_command_processing, args=(settings, screenshot_params)),
'hz' : threading.Thread(target=t_highlight_scr_zone, args=(settings, screenshot_params)),
}

#temp value
screenshot_params['scr_x1'] = 692
screenshot_params['scr_x2'] = 702
screenshot_params['scr_y1'] = 670
screenshot_params['scr_y2'] = 1050

#pre-run functions
select_eve_window(settings)
read_settings(settings, screenshot_params)

#start threads
threads['cn'].start()
threads['cb'].start()
threads['ic'].start()
threads['cp'].start()
threads['hz'].start()

#MOTD
print_usage()
print(time.strftime("[%H:%M:%S]") + "Third eye online.\n")
#do nothing in main cycle, let threads have fun.
while True:
    time.sleep(1)
