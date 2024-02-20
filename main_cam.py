# ESP32-CAM直接控制小车功能
import time
import gc
import camera
import _thread
from machine import Pin
from wifi import wifi_network
from data import network_data
from wheel_io import wheel_timer
from led import blink_led
# import cam_config as cc

# 网络wifi对象
network_wifi = None
# 车轮控制对象
car_wheel = None
# led提示灯
car_led = None

# timer相关const数据定义
LED_TIMERID = const(0)
PWM_TIMERID = const(1)
NET_TIMERID = const(2)

# 摄像头截图循环
def camera_loop():
    while True:
        # time.sleep(5)
        if network_wifi.is_target_enabled():
            img = camera.capture()
            # 有可能img返回为bool类型
            if isinstance(img, bytes):
                # print("capture:" + str(len(img)))
                # 分段发送数据
                send_list = network_data.pack(False, img)
                for value in send_list:
                    network_wifi.send_data(value)
        else:
            # 连接未准备好时，减缓更新
            time.sleep_ms(100)

# 初始化摄像头
def init_camera():
    # https://github.com/singoonhe/esp32-cam-micropython-2022
    # set camera configuration
    # cc.configure(camera, cc.ai_thinker)
    # camera.conf(cc.PIXFORMAT,cc.PIXFORMAT_JPEG) # both pixformat and 
    # camera.conf(cc.FRAMESIZE,cc.FRAMESIZE_QQVGA) # framesize MUST before camera.init
    # camera.init()
    # # other setting after init
    # camera.quality(12)
    
    # https://github.com/singoonhe/micropython-camera-driver
    # ESP32-CAM (default configuration) - https://bit.ly/2Ndn8tN
    camera.init(0, format=camera.JPEG, fb_location=camera.PSRAM)
    camera.framesize(camera.FRAME_XGA)
    # The options are the following:
    # FRAME_96X96 FRAME_QQVGA FRAME_QCIF FRAME_HQVGA FRAME_240X240
    # FRAME_QVGA FRAME_CIF FRAME_HVGA FRAME_VGA FRAME_SVGA
    # FRAME_XGA FRAME_HD FRAME_SXGA FRAME_UXGA FRAME_FHD
    # FRAME_P_HD FRAME_P_3MP FRAME_QXGA FRAME_QHD FRAME_WQXGA
    # FRAME_P_FHD FRAME_QSXGA
    # Check this link for more information: https://bit.ly/2YOzizz
    _thread.start_new_thread(camera_loop, ())

# 接收到自定义命令数据
def ex_command_data(cmd_type, cmd_value):
    if cmd_type == 'Move':
        # 接收到移动事件
        move_info = cmd_value.split('|')
        if len(move_info) >= 2:
            # 移动方向和速度
            car_wheel.set_speed_dir(int(move_info[0]), int(move_info[1]))
    elif cmd_type == 'Battery':
        # 发送当前电量值
        network_wifi.send_command_data('Battery', '50')
    # 释放内存
    gc.collect()
    
# 网络target变化回调
def wifi_target_link_call(linked):
    if linked:
        # 连接成功常亮
        car_led.set_light(True)
    else:
        # 断开连接或等待连接，闪烁效果
        car_led.set_blink(1)
        
# 系统中断回调方法():
def sys_interrupt_call():
    # 释放camera
    camera.deinit()
    # 车轮停止转动
    car_wheel.set_speed_dir(-1, 6)
    # 常灭
    car_led.set_light(False)

# 入口方法
def run_main():
    global car_wheel
    global network_wifi
    global car_led
    # 添加led指示引脚, 并传入timer_id
    car_led = blink_led(13, LED_TIMERID)
    # 初始化过程中急闪
    car_led.set_blink(0.5)
    # 使用IO2是否接低电平来控制使用非AP模式
    wifi_info = {'ap_pin':2}
    # 配置AP时的网络信息
    wifi_info['ap_name'] = 'CAR_HGH'
    wifi_info['ap_psd'] = 'HF123456'
    # 配置局域网下的网络信息
#     wifi_info['ssid'] = 'HUAWEI-HF'
#     wifi_info['psd'] = 'HF123456'
    wifi_info['ssid'] = 'wzry_4_4'
    wifi_info['psd'] = 'xingqiwanWifi'
    # 初始化网络
    network_wifi = wifi_network(wifi_info)
    # 初始化摄像机
    init_camera()
    # 电机控制器, 指定SCL和SDL引脚
    car_wheel = wheel_timer(15, 14, PWM_TIMERID)
    # 指定timer_id，并开始循环接收网络数据
    network_wifi.start_socket(NET_TIMERID, wifi_target_link_call, ex_command_data, sys_interrupt_call)

if __name__ == '__main__':
    run_main()
