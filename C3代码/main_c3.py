# ESP32-C3独立控制小车
from wifi import wifi_network
from battery import adc_battery
from speed_check import speed_check
from wheel_ioextpwm import wheel_ioextpwm

# 网络wifi对象
network_wifi = None
# 车轮控制对象
car_wheel = None
# ADC
car_adc = None
# 更新电量标记
battery_update_mark = False
# 测速对象
car_speed = None
# 标记是否从boot启动的
# start_boot = False

# timer相关const数据定义
NET_TIMERID = const(0)
DIS_TIMERID = const(2)

# 心跳定时回调
def wifi_heart_call():
    global battery_update_mark
    # 检查是否需要回传电压数据
    if battery_update_mark and car_wheel.is_stoping():
        cur_battery = car_adc.update_battery_per()
#         print("cur_battery:" + str(cur_battery))
        network_wifi.send_command_data('Battery', str(cur_battery))
        battery_update_mark = False
        # 电量检查, lowpower时闪烁
        if cur_battery == 0:
            car_wheel.set_led_connected(False)
    # 车轮控制更新
    car_wheel.update()
    # 测速更新
    if car_speed.update():
        network_wifi.send_command_data('Speed', str(car_speed.get_wheel_speed()))

# 接收到自定义命令数据
def ex_command_data(cmd_type, cmd_value):
    global battery_update_mark
    if cmd_type == 'Move' and car_adc.get_battery_per() > 0:
        # 接收到移动事件
        move_info = cmd_value.split('|')
        if len(move_info) >= 2:
            # 移动方向和速度
            move_dir = int(move_info[0])
            move_level = int(move_info[1])
            # 转换当前的level到pwm中
            car_wheel.set_speed_dir(move_dir, move_level)
    elif cmd_type == 'Battery':
        # 标记需要回传电量值
        # 仅电机不转动时才回传电压，避免电量波动
        battery_update_mark = True
    elif cmd_type == 'Light':
        # 开关大灯
        car_wheel.set_lit_value(cmd_value == "On" and 1 or 0)
        
# 网络target变化回调
def wifi_target_link_call(linked):
    if linked:
        # 连接成功常亮
        car_wheel.set_led_connected(True)
    else:
        # 车轮停止转动
        car_wheel.set_speed_dir(-1, 1)
        car_wheel.set_led_connected(False)

# 系统中断回调方法():
def sys_interrupt_call():
    # 车轮停止转动
    car_wheel.set_speed_dir(-1, 1)
    car_wheel.set_led_value(0)

# 入口方法
def run_main():
    global car_adc
    global car_wheel
    global car_speed
    global network_wifi
    # 指定引脚读取ADC
    car_adc = adc_battery(0)
    # 初始化测速
    car_speed = speed_check(2, 3)
    # 使用io扩展模块，传入i2c引脚及地址、pwm的2个引脚
    car_wheel = wheel_ioextpwm(1, 12, 0x20, 10, 6)
    # 初始化舵机操作
    car_wheel.init_sg90(5, 13)
    # 初始化测距操作
    car_wheel.init_sensor(8, 9, DIS_TIMERID)
    # 配置AP时的网络信息
    wifi_info = {}
    wifi_info['ap_state'] = False
    wifi_info['ap_name'] = 'CAR_HYX'
    wifi_info['ap_psd'] = 'HF123456'
    wifi_info['ssid'] = 'HUAWEI-HF'
    wifi_info['psd'] = 'HF123456'
    # 开启心跳功能
    wifi_info['cmd_heart'] = True
    # 120s未连接则自动休眠功能
    wifi_info['sleep_time'] = 120
    # 心跳定时回调
    wifi_info['heart_call'] = wifi_heart_call
    # 连接设备变化回调
    wifi_info['target_link_call'] = wifi_target_link_call
    # 通信事件回调
    wifi_info['ex_cmd_call'] = ex_command_data
    # 程序中断事件
    wifi_info['interrupt_call'] = sys_interrupt_call
    # 初始化网络
    network_wifi = wifi_network(wifi_info)
    # 指定timer_id，并开始循环接收网络数据
    network_wifi.start_socket(NET_TIMERID)

if __name__ == '__main__':
    run_main()

