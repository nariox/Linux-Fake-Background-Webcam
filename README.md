# Linux-Simple-Fake-Background-Webcam

## Background
Video conferencing software support under Linux is relatively poor. The Linux
version of Zoom only supports background replacement via chroma key. The Linux
version of Microsoft Team does not support background blur.

Benjamen Elder wrote a
[blog post](https://elder.dev/posts/open-source-virtual-background/), describing
a background replacement solution using Python, OpenCV, Tensorflow and Node.js.
The scripts in Elder's blogpost do not work out of box. Better and smarter devs have made his approach work (e.g. allo-'s https://github.com/allo-/simple_bodypix_python and fangfufu's https://github.com/fangfufu/Linux-Fake-Background-Webcam). While their approach is technically superior, I wanted to implement a simplistic approach that (hopefully) is a bit less CPU intensive. The results are what you expect, worse.

## Prerequisite
You need to install v4l2loopback. If you are on Debian Buster, you can do the
following:
    
    sudo apt install v4l2loopback-dkms
    
It is also available in AUR at https://aur.archlinux.org/packages/v4l2loopback-dkms/

I added module options for v4l2loopback by creating
``/etc/modprobe.d/v4l2loopback.conf`` with the following content:

    options v4l2loopback devices=1  exclusive_caps=1 video_nr=5 card_label="v4l2loopback"
    
``exclusive_caps`` is required by some programs, e.g. Zoom and Chrome.
``video_nr`` specifies which ``/dev/video*`` file is the v4l2loopback device.
In this repository, I assume that ``/dev/video2`` is the virtual webcam, and
``/dev/video0`` is the physical webcam.

I also created ``/etc/modules-load.d/v4l2loopback`` with the following content:
    
    v4l2loopback
    
This automatically loads v4l2loopback module at boot, with the specified module
options.

### Usage
On a open terminal window, do

    cd fakecam
    python3 fake.py

While the program is running, you may press (case-insensitive):

  - 'u' to refresh background
  - 'v' to reload your virtual background
  - 'q' to quit.

The files that you might want to replace are the followings:

  - ``fakecam/background.jpg`` - the background image
  - ``fakecam/foreground.jpg`` - the foreground image
  - ``fakecam/foreground-mask.jpg`` - the foreground image mask

If you want to change the files above in the middle of streaming, replace them
and press ``CTRL-C``
