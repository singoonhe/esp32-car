# ESP32-C3独立控制小车
from wifi import wifi_network
from wheel_iopwm import wheel_iopwm
from battery import adc_battery
from hcsr04 import HCSR04

# 网络wifi对象
network_wifi = None
# 车轮控制对象
car_wheel = None
# ADC
car_adc = None
# 更新电量标记
battery_update_mark = False
# 超声波测距
car_sensor1 = None
car_sensor2 = None

# timer相关const数据定义
LED_TIMERID = const(0)
NET_TIMERID = const(2)
SPEED_TIMERID = const(4)
# 障碍停止距离,cm
CAR_STOP_DIS = const(15)

# 获取当前障碍物的距离
def get_front_distance(isFront):
    distance = 999
    try:
        car_sensor = car_sensor1 if isFront else car_sensor2
        distance = car_sensor.distance_cm()
#         print(f'{num}Distance:', distance, 'cm')
    except OSError as ex:
        print('ERROR getting distance:', ex)
    return distance

# 接收到自定义命令数据
def ex_command_data(cmd_type, cmd_value):
    global battery_update_mark
    if cmd_type == 'Move':
        # 接收到移动事件
        move_info = cmd_value.split('|')
        if len(move_info) >= 2:
            # 移动方向和速度
            move_dir = int(move_info[0])
            # 当前言有障碍，则停止移动
            if move_dir != -1 and (move_dir >= 315 or move_dir <= 225) and get_front_distance() < CAR_STOP_DIS:
                move_dir = -1
            car_wheel.set_speed_dir(move_dir, int(move_info[1]))
            # 上传一次当前电量
            if battery_update_mark and move_dir == -1:
                # 发送当前电量值
                cur_battery = car_adc.get_battery_per()
                network_wifi.send_command_data('Battery', str(cur_battery))
                battery_update_mark = False
    elif cmd_type == 'Battery':
        # 标记需要回传电量值
        # 仅电机不转动时才回传电压，避免电量波动
        battery_update_mark = True
        
# 网络target变化回调
def wifi_target_link_call(linked):
    if linked:
        # 连接成功常亮
        car_wheel.set_light(True)
    else:
        # 车轮停止转动
        car_wheel.set_speed_dir(-1, 1)
        car_wheel.set_light(False)

# 系统中断回调方法():
def sys_interrupt_call():
    # 车轮停止转动
    car_wheel.set_speed_dir(-1, 1)
    car_wheel.set_light(False)

# 入口方法
def run_main():
    global car_wheel
    global network_wifi
    global car_adc
    global car_sensor1
    global car_sensor2
    # 指定引脚读取ADC
    car_adc = adc_battery(0)
    # 电机控制器, 指定控制电机的4个引脚。先左侧2电机，再右侧2电机
    # L298N使用2个PWM引脚来控制速度
    # 使用2个引脚来检测速度
    car_wheel = wheel_iopwm((8,9, 5,4), (10,6), (2,3), SPEED_TIMERID)
    # 添加超声波测距功能（1cm each 29.1us，仅检测50cm范围内）
    car_sensor1 = HCSR04(trigger_pin=5, echo_pin=4, echo_timeout_us=1500)
    car_sensor2 = HCSR04(trigger_pin=8, echo_pin=9, echo_timeout_us=1500)
    # 配置AP时的网络信息
    wifi_info['ap_name'] = 'CAR_HYX'
    wifi_info['ap_psd'] = 'HF123456'
    # 开启心跳功能
    wifi_info['cmd_heart'] = True
    # 初始化网络
    network_wifi = wifi_network(wifi_info)
    # 指定timer_id，并开始循环接收网络数据
    network_wifi.start_socket(NET_TIMERID, wifi_target_link_call, ex_command_data, sys_interrupt_call)

if __name__ == '__main__':
    run_main()

