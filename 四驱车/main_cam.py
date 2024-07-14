# ESP32-CAM控制数据功能
import time
import camera
import _thread
import sg90
from led import blink_led
from wifi import wifi_network
from data import network_data

# 网络wifi对象
network_wifi = None
# led照明灯
car_light = None
# 舵机对象
#cam_sg = None
# timer相关const数据定义
NONE_TIMERID = const(-999)
NET_TIMERID = const(0)

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
            time.sleep_ms(500)

# 初始化摄像头
def init_camera():
    # https://github.com/singoonhe/micropython-camera-driver
    # 15帧左右，报EV-EOF-OVF(可能是内存不足)
    # ESP32-CAM (default configuration) - https://bit.ly/2Ndn8tN
    # xclk_freq:设置20加快内部传输速度，默认为10
    # fb_size：默认为1，设置2后速度双倍
    camera.init(0, format=camera.JPEG, fb_location=camera.PSRAM, xclk_freq=camera.XCLK_20MHz, fb_size = 2)
    camera.framesize(camera.FRAME_VGA)
    _thread.start_new_thread(camera_loop, ())

# 接收到自定义命令数据
def ex_command_data(cmd_type, cmd_value):
    if cmd_type == 'Light':
        # 照明灯亮或灭
        car_light.set_light(cmd_value == 'On')
    elif cmd_type == 'Rotate':
        # 舵机旋转, 最大120度。从-60~60范围
        # 操作台划动方向与舵机方向相反，故添加-号
        cam_sg.rotate(-int(cmd_value))
    else:
        # 其它的命令直接转给C3芯片
        #         print("cmd_type:" + cmd_type)
        pass

# 网络target变化回调
def wifi_target_link_call(linked):
    if linked:
        # 通知C3连接成功
        print("linked:linked")
    else:
        # 通知C3失去连接
        print("linked:unlinked")
        # 照明灯灭掉
        car_light.set_light(False)

# 系统中断回调方法():
def sys_interrupt_call():
    # 释放camera
    camera.deinit()
    # 照明灯灭掉
    car_light.set_light(False)

# 入口方法
def run_main():
    global network_wifi
    global car_light
    global cam_sg
    # 初始化照明灯，不启用闪烁功能
    car_light = blink_led(4, NONE_TIMERID)
    # 配置AP时的网络信息
    wifi_info = {}
    wifi_info['ap_name'] = 'CAR_HGH'
    wifi_info['ap_psd'] = 'HF123456'
    # 初始化网络
    network_wifi = wifi_network(wifi_info)
    # 初始化摄像机
    init_camera()
    # 初始化舵机对象，初始偏移为90度
    cam_sg = sg90.sg90(2, 90)
    # 指定timer_id，并开始循环接收网络数据
    network_wifi.start_socket(NET_TIMERID, wifi_target_link_call, ex_command_data, sys_interrupt_call)

if __name__ == '__main__':
    run_main()
