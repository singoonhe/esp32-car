# ESP32-C3独立控制小车
from wifi import wifi_network
from wheel import wheel_timer

# 网络wifi对象
network_wifi = None
# 车轮控制对象
car_wheel = None

# 接收到自定义命令数据
def ex_command_data(cmd_type, cmd_value):
    if cmd_type == 'Move':
        # 接收到移动事件
        move_info = cmd_value.split('|')
        if len(move_info) >= 2:
            # 移动方向和速度
            car_wheel.set_speed_dir(int(move_info[0]), int(move_info[1]))
        
# 系统中断回调方法():
def sys_interrupt_call():
    # 车轮停止转动
    car_wheel.set_speed_dir(-1, 6)

# 入口方法
def run_main():
    global car_wheel
    global network_wifi
    # 电机控制器, 指定SCL和SDL引脚
    # ESP32-C3不支持虚拟定时器，不能使用默认值-1。必须是0|2|4等偶数
    car_wheel = wheel_timer(5, 4, 0)
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

