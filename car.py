#入口功能
import time
import camera
import _thread
import cam_config as cc
from machine import Timer,Pin
from wifi import wifi_network
from data import network_data

# 指定的数据接收者
command_target = None
# 网络wifi对象
network_wifi = None

# 摄像头截图循环
def camera_loop():
    while True:
#         time.sleep(5)
        if command_target != None:
            img=camera.capture()
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
    camera.conf(cc.FRAMESIZE,cc.FRAMESIZE_SVGA) # framesize MUST before camera.init
    camera.init()
    # other setting after init
    camera.quality(12)
    _thread.start_new_thread(camera_loop, ())

# 接收到命令数据
def recv_command_data(data, addr):
    global command_target
    command_data = network_data.unpack(data)
    if command_data:
        if command_data['Type'] == 'Login':
            command_target = addr
            send_command_data('Login')
            print('set command target %s' % addr[0])
        elif command_data['Type'] == 'Logout':
            command_target = None
            print('clear command target')
            
# 发送命令数据
def send_command_data(cmd_type, cmd_value=None):
    if command_target == None:
        return
    pack_obj = {'Type':cmd_type}
    if cmd_value:
        pack_obj['Value'] = cmd_value
    send_value = network_data.pack(True, pack_obj)
    network_wifi.send_data(send_value, command_target)

# 定时调用
def wheel_timer():
    tim = Timer(-1)
    tim.init(period=2000, mode=Timer.PERIODIC, callback=lambda t:print(2))

if __name__ == '__main__':
    # 初始化摄像机
#     init_camera()
    # 电机控制定时器
#     wheel_timer()
    # 初始化网络, 使用IO2是否接低电平来控制。
    # 默认使用家庭网络
    p2 = Pin(2, Pin.IN, Pin.PULL_UP)
    if p2.value() == 0:
        wifi_info = [] # AP模式
    else:
#       wifi_info = ['xingqiwan', 'xingqiwanWifi'] # 公司网络
        wifi_info = ['HUAWEI-HF', 'HF123456'] # 家庭网络
    network_wifi = wifi_network(wifi_info)
    network_wifi.start_socket(recv_command_data)

