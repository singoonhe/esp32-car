#入口功能
import time
import camera
import _thread
import cam_config as cc
from machine import Timer,Pin
from wifi import wifi_network
from data import network_data
from wheel import wheel_timer

# 指定的数据接收者
command_target = None
# 网络wifi对象
network_wifi = None
# 网络检查，未收到数据的计数
network_check = 0
# 车轮控制对象
car_wheel = None

# 摄像头截图循环
def camera_loop():
    while True:
        time.sleep(5)
        if command_target != None:
            img=camera.capture()
            print("capture:" + str(len(img)))
            # 分段发送数据
            send_list = network_data.pack(False, img)
            for value in send_list:
                network_wifi.send_data(value, command_target)
        else:
            # 连接未准备好时，减缓更新
            time.sleep_ms(100)

# 初始化摄像头
def init_camera():
    # set camera configuration
    cc.configure(camera, cc.ai_thinker)
    camera.conf(cc.PIXFORMAT,cc.PIXFORMAT_JPEG) # both pixformat and 
    camera.conf(cc.FRAMESIZE,cc.FRAMESIZE_QQVGA) # framesize MUST before camera.init
    camera.init()
    # other setting after init
    camera.quality(12)
    _thread.start_new_thread(camera_loop, ())

# 接收到命令数据
def recv_command_data(data, addr):
    global command_target
    global network_check
    command_data = network_data.unpack(data)
    if command_data:
        network_check = 0
        if command_data['Type'] == 'Login':
            command_target = addr
            send_command_data('Login')
            print('set command target %s' % addr[0])
        elif command_data['Type'] == 'Move':
            # 接收到移动事件
            var move_info = command_data['Value'].split('|')
            if len(move_info) >= 2:
                # 移动方向和速度
                car_wheel.set_speed_dir(int(move_info[0]), int(move_info[1]))
            
# 发送命令数据
def send_command_data(cmd_type, cmd_value=None):
    if command_target == None:
        return
    pack_obj = {'Type':cmd_type}
    if cmd_value:
        pack_obj['Value'] = cmd_value
    send_value = network_data.pack(True, pack_obj)
    network_wifi.send_data(send_value, command_target)
    
# wifi网络检查方法
def check_wifi_target(t):
    global command_target
    network_check += 1
    if command_target != None && network_check > 4:
        command_target = None
        print('clear command target because of time out')

if __name__ == '__main__':
    # 初始化摄像机
    init_camera()
    # 电机控制器, 指定SCL和SDL引脚
    car_wheel = wheel_timer(12, 13)
    # 开启网络超时检查
    wifi_timer = Timer()
    wifi_timer.init(period=500, mode=Timer.PERIODIC, callback=check_wifi_target)
    # 初始化网络, 使用IO2是否接低电平来控制使用AP模式
    wifi_info = {'ap_name' : 'CAR_HGH', 'ap_psd' : 'HF123456', 'ap_pin':2}
    # 默认使用家庭网络
    wifi_info['ssid'] = 'wzry_4_4'
    wifi_info['psd'] = 'xingqiwanWifi'
#     wifi_info['ssid'] = 'HUAWEI-HF'
#     wifi_info['psd'] = 'HF123456'
    network_wifi = wifi_network(wifi_info)
    network_wifi.start_socket(recv_command_data)

