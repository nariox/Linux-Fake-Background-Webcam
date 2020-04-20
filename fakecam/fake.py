import os
import cv2
import numpy as np
import requests
import pyfakewebcam
from signal import signal, SIGINT
from sys import exit

import curses



# setup access to the *real* webcam
cap = cv2.VideoCapture('/dev/video0')
height, width = 720, 1280
cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
cap.set(cv2.CAP_PROP_FPS, 30)

# The scale factor for image sent to bodypix
sf = 0.5
# Threshold value
DELTA_THRESHOLD = 30;
# Background averaging
BACK_AVG = 30; 

# setup the fake camera
fake = pyfakewebcam.FakeWebcam('/dev/video5', width, height)

# declare global variables
real_background = None
virtual_background = None
foreground = None
f_mask = None
inv_f_mask = None

def load_images():
    global virtual_background
    global real_background
    global foreground
    global f_mask
    global inv_f_mask

    # load real background
    frames = []
    for _ in range(BACK_AVG):
        _,frame = cap.read();
        frames.append(frame);
    real_background=np.median(frames, axis=0).astype(dtype=np.uint8);
    
    # load the virtual background
    virtual_background = cv2.imread("background.jpg")
    virtual_background = cv2.resize(virtual_background, (width, height))

    foreground = cv2.imread("foreground.jpg")
    foreground = cv2.resize(foreground, (width, height))

    f_mask = cv2.imread("foreground-mask.png")
    f_mask = cv2.normalize(f_mask, None, alpha=0, beta=1,
                        norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_32F)
    f_mask = cv2.resize(f_mask, (width, height))
    f_mask = cv2.cvtColor(f_mask, cv2.COLOR_BGR2GRAY)
    inv_f_mask = 1 - f_mask

def handler(signal_received, frame):
    load_images();
    print('Reloaded the virtual_background and foreground images')

def get_mask(frame, real_background):
    mask = cv2.absdiff(frame, real_background);
    mask = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY);
    mask = cv2.threshold(mask, DELTA_THRESHOLD, 1, cv2.THRESH_BINARY)[1];
    mask = cv2.dilate(mask, np.ones((15,15), np.uint8) , iterations=1);
    mask = cv2.blur(mask.astype(float), (30,30));
    return mask

def get_frame(cap, real_background, virtual_background):
    _,frame = cap.read();
    # fetch the mask with retries (the app needs to warmup and we're lazy)
    # e v e n t u a l l y c o n s i s t e n t
    mask = None
    while mask is None:
        try:
            mask = get_mask(frame, real_background);
        except:
            print("mask request failed, retrying")

    # composite the foreground and virtual_background
    for c in range(frame.shape[2]):
        frame[:,:,c] = frame[:,:,c] * mask + virtual_background[:,:,c] * (1 - mask)

    for c in range(frame.shape[2]):
        frame[:,:,c] = frame[:,:,c] * inv_f_mask + foreground[:,:,c] * f_mask

    return frame

if __name__ == '__main__':
#    signal(SIGINT, handler)
    stdscr = curses.initscr()
#    height, width = stdscr.getmaxyx()
    
    stdscr.addstr('Simple fake camera\n')
    stdscr.addstr('Press any key to capture virtual_background\n');
    curses.noecho();
    stdscr.getch();
    stdscr.nodelay(1);
    
    load_images();
    stdscr.addstr('Running...\n')
    stdscr.addstr('Please press CTRL-\ to exit.\n')
    stdscr.addstr('Please CTRL-C to reload the virtual_background and foreground images\n')
    stdscr.refresh()

#    curses.noecho() # Dont show inputs
    # frames forever
    while True:
#        curses.cbreak()
#        signal(SIGINT, handler)
        frame = get_frame(cap, real_background, virtual_background)
#        _,frame = cap.read()
        # fake webcam expects RGB
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        fake.schedule_frame(frame)
