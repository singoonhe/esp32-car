# ESP32-C3通过microbit通信
from machine import UART
from wifi import wifi_network

# 网络wifi对象
network_wifi = None
# uart通信对象
micro_uart = None

# 发送uart数据
def send_micro_byte(s_byte):
    if micro_uart != None:
        micro_uart.write(bytes([s_byte]))

# 接收到自定义命令数据
def ex_command_data(cmd_type, cmd_value):
    if cmd_type == 'Move':
        # 接收到移动事件
        move_info = cmd_value.split('|')
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

# 系统中断回调方法():
def sys_interrupt_call():
    # 车轮停止转动
    send_micro_byte(0)

# 入口方法
def run_main():
    global network_wifi
    global micro_uart
    # 初始化通信uart
    micro_uart = UART(0, 115200)
    # 使用IO10是否接低电平来控制使用AP模式
    wifi_info = {'ap_pin':10}
    # 配置AP时的网络信息
    wifi_info['ap_name'] = 'CAR_HYX'
    wifi_info['ap_psd'] = 'HF123456'
    # 配置局域网下的网络信息
    wifi_info['ssid'] = 'HUAWEI-HF'
    wifi_info['psd'] = 'HF123456'
    # 开启心跳功能
    wifi_info['cmd_heart'] = True
    # 初始化网络
    network_wifi = wifi_network(wifi_info)
    # 指定timer_id，并开始循环接收网络数据
    network_wifi.start_socket(2, ex_command_data, sys_interrupt_call)

if __name__ == '__main__':
    run_main()


