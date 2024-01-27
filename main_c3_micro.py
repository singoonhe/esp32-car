# ESP32-C3通过microbit通信
import time
from machine import Timer,Pin,UART
from wifi import wifi_network
from data import network_data

# 指定的数据接收者
command_target = None
# 网络wifi对象
network_wifi = None
# 网络检查，未收到数据的计数
network_check = 0
# uart通信对象
micro_uart = None

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
            move_info = command_data['Value'].split('|')
            if len(move_info) >= 2:
                # 发送移动方向
                move_dir = int(move_info[0])
                if move_dir > 315 and move_dir <= 45:
                    send_micro_byte(11)
                elif move_dir > 45 and move_dir <= 135:
                    send_micro_byte(12)
                elif move_dir > 135 and move_dir <= 225:
                    send_micro_byte(13)
                elif move_dir > 225 and move_dir <= 315:
                    send_micro_byte(14)
                else: # move_dir == -1
                    send_micro_byte(0)
                # 发送速度
                send_micro_byte(int(move_info[1]))

# 发送uart数据
def send_micro_byte(s_byte):
    if micro_uart != None:
        micro_uart.write(bytes([s_byte]))
    
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
    if command_target != None and network_check > 4:
        command_target = None
        print('clear command target because of time out')

if __name__ == '__main__':
    # 初始化通信uart
    micro_uart = UART(0, 115200)
    # 开启网络超时检查
    wifi_timer = Timer(-1)
    wifi_timer.init(period=500, mode=Timer.PERIODIC, callback=check_wifi_target)
    # 初始化网络, 使用IO2是否接低电平来控制使用AP模式
    wifi_info = {'ap_name' : 'CAR_HGH', 'ap_psd' : 'HF123456', 'ap_pin':2}
    # 默认使用家庭网络
    wifi_info['ssid'] = 'HUAWEI-HF'
    wifi_info['psd'] = 'HF123456'
    network_wifi = wifi_network(wifi_info)
    network_wifi.start_socket(recv_command_data)



