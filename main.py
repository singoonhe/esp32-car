#入口功能
import time
import camera
import _thread
import cam_config as cc
from machine import Timer
from wifi import wifi_network

# 摄像头截图循环
def camera_loop(wifi, camera):
    while True:
        if wifi.is_ready():
            img=camera.capture()
        else:
            time.sleep_ms(100)

# 初始化摄像头
def init_camera(wifi):
    # set camera configuration
    cc.configure(camera, cc.ai_thinker)
    camera.conf(cc.PIXFORMAT,cc.PIXFORMAT_RGB565) # both pixformat and 
    camera.conf(cc.FRAMESIZE,cc.FRAMESIZE_QQVGA) # framesize MUST before camera.init
    camera.init()
    # other setting after init
    camera.quality(12)
#     _thread.start_new_thread(camera_loop, (wifi, camera))

# 定时调用
def wheel_timer():
    pass

if __name__ == '__main__':
    wifi = wifi_network()
    if wifi.init():
        init_camera(wifi)
        # 电机控制定时器
        while True:
            pass
#         tim = Timer(-1)
#         tim.init(period=2000, mode=Timer.PERIODIC, callback=wheel_timer())
