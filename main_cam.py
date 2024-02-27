# ESP32-CAM直接控制小车功能
import time
import camera
import _thread
from led import blink_led
from wifi import wifi_network
from data import network_data
from wheel_io import wheel_timer
import cam_config as cc

# 网络wifi对象
network_wifi = None
# 车轮控制对象
car_wheel = None
# led照明灯
car_light = None

# timer相关const数据定义
NONE_TIMERID = const(-999)
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
    # 10帧左右，不报内存问题
    # set camera configuration
    cc.configure(camera, cc.ai_thinker)
    camera.conf(cc.PIXFORMAT,cc.PIXFORMAT_JPEG) # both pixformat and 
    camera.conf(cc.FRAMESIZE,cc.FRAMESIZE_SVGA) # framesize MUST before camera.init
    camera.init()
    # other setting after init
    camera.quality(12)
    
    # https://github.com/singoonhe/micropython-camera-driver
    # 15帧左右，报EV-EOF-OVF(可能是内存不足)
    # ESP32-CAM (default configuration) - https://bit.ly/2Ndn8tN
    # xclk_freq:设置20加快内部传输速度，默认为10
    # fb_size：默认为1，设置2后速度双倍
    # camera.init(0, format=camera.JPEG, fb_location=camera.PSRAM, xclk_freq=camera.XCLK_20MHz, fb_size = 2)
    # camera.framesize(camera.FRAME_SVGA)
    # camera.quality = 20
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
    elif cmd_type == 'Light':
        # 照明灯亮或灭
        car_light.set_light(cmd_value == 'On')
    
# 网络target变化回调
def wifi_target_link_call(linked):
    if linked:
        # 连接成功常亮
        car_wheel.set_pin_blink(0, 1)
    else:
        # 断开连接或等待连接，闪烁效果
        car_wheel.set_pin_blink(500, 0)
        # 车轮停止转动
        car_wheel.set_speed_dir(-1, 1)
        # 照明灯灭掉
        car_light.set_light(False)

# 系统中断回调方法():
def sys_interrupt_call():
    # 释放camera
    camera.deinit()
    # 车轮停止转动
    car_wheel.set_speed_dir(-1, 1)
    # 照明灯灭掉
    car_light.set_light(False)

# 入口方法
def run_main():
    global car_wheel
    global network_wifi
    global car_light
    # 初始化照明灯，不启用闪烁功能
    car_light = blink_led(4, NONE_TIMERID)
    # 电机控制器, 指定SCL和SDA引脚
    car_wheel = wheel_timer(15, 14, PWM_TIMERID)
    # 开启blink位快速闪烁
    car_wheel.set_pin_blink(100, 1)
    # 使用指定IO是否接低电平来控制使用非AP模式
    wifi_info = {'ap_pin':13}
    # 配置AP时的网络信息
    wifi_info['ap_name'] = 'CAR_HGH'
    wifi_info['ap_psd'] = 'HF123456'
    # 配置局域网下的网络信息
    wifi_info['ssid'] = 'HUAWEI-HF'
    wifi_info['psd'] = 'HF123456'
#     wifi_info['ssid'] = 'wzry_4_4'
#     wifi_info['psd'] = 'xingqiwanWifi'
    # 初始化网络
    network_wifi = wifi_network(wifi_info)
    # 初始化摄像机
    init_camera()
    # 指定timer_id，并开始循环接收网络数据
    network_wifi.start_socket(NET_TIMERID, wifi_target_link_call, ex_command_data, sys_interrupt_call)

if __name__ == '__main__':
    run_main()
