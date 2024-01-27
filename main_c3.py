# ESP32-C3独立控制小车
import time
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

# 接收到命令数据
def recv_command_data(data, addr):
    global command_target
    global network_check
    command_data = network_data.unpack(data)
    if command_data:
        network_check = 0
        if command_data['Type'] == 'Login':
            command_target = addr
            network_wifi.set_enable(True)
            send_command_data('Login')
            print('set command target %s' % addr[0])
        elif command_data['Type'] == 'Logout':
            network_wifi.set_enable(False)
            command_target = None
            print('clear command target by logout')
        elif command_data['Type'] == 'Move':
            # 接收到移动事件
            move_info = command_data['Value'].split('|')
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
    global network_check
    # 发送心跳，避免断开连接
    send_command_data('Heart')
    network_check += 1
    if command_target != None and network_check > 4:
        network_wifi.set_enable(False)
        command_target = None
        print('clear command target because of time out')
        
# 系统中断回调方法():
def sys_interrupt_call():
    # 车轮停止转动
    car_wheel.set_speed_dir(-1, 6)
    print('system interrupt')

# 入口方法
def run_main():
    global car_wheel
    global network_wifi
    # 电机控制器, 指定SCL和SDL引脚
    # ESP32-C3不支持虚拟定时器，不能使用默认值-1。必须是0|2|4等偶数
    car_wheel = wheel_timer(5, 4, 0)
    # 开启网络超时检查
    wifi_timer = Timer(2)
    wifi_timer.init(period=500, mode=Timer.PERIODIC, callback=check_wifi_target)
    # 初始化网络, 使用IO10是否接低电平来控制使用AP模式
    wifi_info = {'ap_name' : 'CAR_HYX', 'ap_psd' : 'HF123456', 'ap_pin':10}
    # 默认使用家庭网络
    wifi_info['ssid'] = 'HUAWEI-HF'
    wifi_info['psd'] = 'HF123456'
    network_wifi = wifi_network(wifi_info)
    network_wifi.start_socket(recv_command_data, sys_interrupt_call)

if __name__ == '__main__':
    run_main()

