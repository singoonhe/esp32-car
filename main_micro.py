# ESP32-C3通过microbit通信
import time
from machine import Timer,Pin
from wifi import wifi_network
from data import network_data

# 指定的数据接收者
command_target = None
# 网络wifi对象
network_wifi = None
# 网络检查，未收到数据的计数
network_check = 0
# i2c通信对象
micro_i2c = None
# i2c通信地址
micro_addr = None

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
                # 发送移动方向
                move_dir = int(move_info[0])
                if move_dir > 315 && move_dir <= 45:
                    send_i2c_byte(11)
                elif move_dir > 45 && move_dir <= 135:
                    send_i2c_byte(12)
                elif move_dir > 135 && move_dir <= 225:
                    send_i2c_byte(13)
                elif move_dir > 225 && move_dir <= 315:
                    send_i2c_byte(14)
                else: # move_dir == -1
                    send_i2c_byte(0)
                # 发送速度
                send_i2c_byte(int(move_info[1]))

# 发送i2c数据
def send_i2c_byte(i2c_byte):
    if micro_addr != None:
        micro_i2c.writeto(micro_addr, bytes([i2c_byte]))
    
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
    # 初始化通信i2c
    micro_i2c = I2C(scl=Pin(12), sda=Pin(12), freq=100000)
    i2c_devices = micro_i2c.scan()
    if len(i2c_devices) > 0:
        micro_addr = i2c_devices[0]
    else:
        print('cannot find i2c device')
        return 0
    # 开启网络超时检查
    wifi_timer = Timer()
    wifi_timer.init(period=500, mode=Timer.PERIODIC, callback=check_wifi_target)
    # 初始化网络, 使用IO2是否接低电平来控制使用AP模式
    wifi_info = {'ap_name' : 'CAR_HGH', 'ap_psd' : 'HF123456', 'ap_pin':2}
    # 默认使用家庭网络
    wifi_info['ssid'] = 'HUAWEI-HF'
    wifi_info['psd'] = 'HF123456'
    network_wifi = wifi_network(wifi_info)
    network_wifi.start_socket(recv_command_data)



