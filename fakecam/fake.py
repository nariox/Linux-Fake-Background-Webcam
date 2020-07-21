#!/usr/bin/env python3
import os
import cv2
import numpy as np
import pyfakewebcam
import curses

# setup access to the *real* webcam
cap = cv2.VideoCapture('/dev/video2')
height, width = 480, 640
#height, width = 720, 1280

cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
cap.set(cv2.CAP_PROP_FPS, 30)

# In case the real webcam does not support the requested mode.
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))

# Background averaging
BACK_AVG = 30; 
BACK_BLUR = 31;

# setup the fake camera
fake = pyfakewebcam.FakeWebcam('/dev/video5', width, height)

# declare global variables
virtual_background = None
foreground = None
f_mask = None
inv_f_mask = None
filt = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(61,61));
filt2 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(31,31));

screen = curses.initscr()
screen.nodelay(1)
curses.noecho()
mask = None
fgbg = cv2.createBackgroundSubtractorMOG2(detectShadows = False)

# Opening/Closing filters
filt = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(5,5));

def load_images():
    global virtual_background
    global foreground
    global f_mask
    global inv_f_mask
    
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
    
def update_real_background():
    # load real background
    frames = []
    for _ in range(BACK_AVG):
        _,frame = cap.read();
        frame = cv2.GaussianBlur(frame,(BACK_BLUR ,BACK_BLUR),0);
        fgbg.apply(frame)

def get_mask(frame):
    mask = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY);
    mask = cv2.GaussianBlur(mask,(BACK_BLUR ,BACK_BLUR),0);
    fgbg.apply(mask, mask, learningRate=0.0)
    mask = cv2.dilate(mask, filt , iterations=8);
    mask = cv2.erode(mask, filt , iterations=9);
    mask = cv2.dilate(mask, filt , iterations=2);
    mask = cv2.normalize(mask.astype('float'), None, 0.0, 1.0, cv2.NORM_MINMAX);
    mask = cv2.GaussianBlur(mask,(BACK_BLUR ,BACK_BLUR),0);
    return mask

def get_frame(cap):
    _,frame = cap.read();

    mask = get_mask(frame);

    # composite the foreground and virtual_background
    for c in range(frame.shape[2]):
        frame[:,:,c] = frame[:,:,c] * mask + virtual_background[:,:,c] * (1 - mask)

    for c in range(frame.shape[2]):
        frame[:,:,c] = frame[:,:,c] * inv_f_mask + foreground[:,:,c] * f_mask

    return frame

if __name__ == '__main__':    
    load_images();
    screen.addstr('Simple fake camera\n')
    screen.addstr('Press any key to capture virtual_background\n');
    cv2.waitKey();
    update_real_background()
    
    screen.addstr('Running...\n')
    screen.addstr('Press Q to quit\n')
    screen.addstr('Press U to update the real background\n')
    screen.addstr('Press V to reload the virtual_background and foreground images\n')

    # frames forever
    while True:
        k = screen.getch()
        if k == ord('q') or k == ord('Q'):
            break
        elif k == ord('u') or k == ord('U'):
            update_real_background();
        elif k == ord('v') or k == ord('V'):
            load_images();
        frame = get_frame(cap)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        fake.schedule_frame(frame)
        
    curses.nocbreak();
    curses.endwin();
    cap.release();
