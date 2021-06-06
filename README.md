# Third eye script v0.4

This script is used to check standings segment from local chat in EVE Online for presence of neutral players and sound alarm if they found. Also it notifies about "boost local" events.
Relevant for null-sec caribers and others.

Main work principle based on capturing(via screenshot) small screen fragments and processing it with openCV library.

**Python libraries required :**
***
>pip3 install pillow  
>pip3 install opencv-python  
>pip3 install playsound  
>pip3 install win32gui  
>pip3 install keyboard  
***
## How to :
- install [python3 interpreter](https://www.python.org/downloads/).
- install libraries above. Just copy\paste it in terminal line by line after you install python.
- Run EvE. Log in into your account.
- Run script and select active window
- press "t" then "enter" to select position of standing segment in local chat. You can resize it within Y axis only. When desired position is set - press enter to finalize settings.

![window_select](/img/1.jpg)

- now you can select alarm repeat time and store setting in file.

Script is ready to work. It sometimes give false positive notification regarding local boost becaue of poor application architecture. It would be nice to remake this script to use EvE memory directly instead of making screenshot but it's hell a lot of work.
