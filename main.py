#入口功能
import machine
import time

print(5+2)
print(machine.freq())

import os
print(os.listdir())

import camera
import cam_config as cc
# set camera configuration
cc.configure(camera, cc.ai_thinker)
camera.conf(cc.PIXFORMAT,cc.PIXFORMAT_RGB565) # both pixformat and 
camera.conf(cc.FRAMESIZE,cc.FRAMESIZE_QQVGA) # framesize MUST before camera.init
camera.init()
# other setting after init
camera.quality(12)
img=camera.capture()
print(len(img))
time.sleep(3)
img=camera.capture()
print(len(img))

