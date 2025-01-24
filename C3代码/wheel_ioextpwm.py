#车轮控制类
import time
from hcsr04 import HCSR04
from tap_sg90 import tap_sg90
from machine import Timer, Pin, PWM
from wheel_ioext6 import wheel_ioext6

# 障碍停止距离,cm
CAR_STOP_DIS = const(10)
# 速度对应的pwm值
speed_levels_dic = [{'pos':1, 'pwm':205}, {'pos':1, 'pwm':315}, {'pos':1, 'pwm':475},
                    {'pos':1, 'pwm':650}, {'pos':1, 'pwm':825}, {'pos':1, 'pwm':1023},
                    {'pos':2, 'pwm':700}, {'pos':2, 'pwm':800}, {'pos':2, 'pwm':900},
                    {'pos':2, 'pwm':1023}]

class wheel_ioextpwm:
    # 初始化方法
    # scl+sda: io扩展模块需要的i2c接口引脚
    # i2c_addr: io楄模块地址
    # pwm_pin1+pwm_pin2:电机转速控制引脚
    def __init__(self, scl, sda, i2c_addr, pwm_pin1, pwm_pin2):
        # 初始化io扩展器
        self.ioext = wheel_ioext6(scl, sda, i2c_addr)
        # 初始化电机pwm
        self.pwm1 = PWM(Pin(pwm_pin1, Pin.OUT), freq=50)
        self.pwm2 = PWM(Pin(pwm_pin2, Pin.OUT), freq=50)
        # 移动状态
        self.move_state = 0
        # pwm基础值
        self.min_pwm = speed_levels_dic[0]['pwm']

    # 初始化舵机控制对象
    def init_sg90(self, sg_pin1, sg_pin2):
        self.car_sg90 = tap_sg90(sg_pin1, sg_pin2)
        # 标记需要切换到的档位值
        self.sg_to_pos = None
    
    # 初始化超声波测距对象
    def init_sensor(self, trigger_pin, echo_pin, timer_id):
        # 添加超声波测距功能（1cm each 29.1us，5800us表示检测1m的距离）
        self.car_sensor = HCSR04(trigger_pin=trigger_pin, echo_pin=echo_pin, echo_timeout_us=10000)
        self.sensor_timer = Timer(timer_id)
        # 测量间隔及初始时间值
        self.sensor_work_interval = 10
        self.sensor_work_time = 0

    # 重置车轮的方向和期望档位
    def set_speed_dir(self, move_dir, speed_level):
        # 左右转速比值，转弯时需要
        left_pwm_rate = 1
        right_pwm_rate = 1
        
        old_move_state = self.move_state
        if move_dir == -1:
            # 当前方向为0，停止移动
            self.move_state = 0
        elif move_dir > 225 and move_dir < 315:
            # 左右一起倒车, 速度减半
            self.move_state = -1
        else:
            # 转换方向到-45~225之间
            if move_dir >= 315:
                move_dir -= 360
            if move_dir < 10:
                right_pwm_rate = 0
            elif move_dir > 80:
                right_pwm_rate = 1
            else:
                right_pwm_rate = (move_dir - 10) / (80 - 10)
            if move_dir > 170:
                left_pwm_rate = 0
            elif move_dir < 100:
                left_pwm_rate = 1
            else:
                left_pwm_rate = (170 - move_dir) / (170 - 100)
            # 直行
            self.move_state = 1
        # 是否开启定时测距
        if old_move_state != self.move_state:
            if self.move_state == 1:
                # 检测一次距离，查看是否允许直行
                cur_sensor_dis = self.get_front_distance()
                if cur_sensor_dis < CAR_STOP_DIS:
                    self.move_state = 0
                else:
                    self.sensor_timer.init(period=100, mode=Timer.PERIODIC, callback=self.sensor_timer_update)
                    # 计算一次更新频率
                    self.sensor_work_interval = self.calc_sensor_interval(cur_sensor_dis)
                    self.sensor_work_time = 0
            else:
                self.sensor_timer.deinit()
        # 设置电机的旋转状态
        self.ioext.set_motors_state(self.move_state)
        # 控制电机的频率
        if self.move_state != 0:
            speed_pwm = self.convert_level_pwm(speed_level)
            # 减去pwm基础值
            pwm_offset = speed_pwm - self.min_pwm
            if left_pwm_rate <= 0:
                self.pwm1.duty(0)
            else:
                self.pwm1.duty(int(self.min_pwm + pwm_offset * left_pwm_rate))
            if right_pwm_rate <= 0:
                self.pwm2.duty(0)
            else:
                self.pwm2.duty(int(self.min_pwm + pwm_offset * right_pwm_rate))
#             print(f"left_pwm_rate:{left_pwm_rate}, {right_pwm_rate}")
    
    # 获取当前电机是否静止中
    def is_stoping(self):
        return self.move_state == 0
    
    # 设置led指示灯是否已连接
    def set_led_connected(self, is_connnect):
        if is_connnect:
            self.ioext.set_led_value(1)
            self.led_blink = False
        else:
            self.led_blink = True

    # 定时更新
    def update(self):
        # 灯需要闪烁时，切换状态
        if self.led_blink:
            self.ioext.turn_led_value()
        # 检查sg90是否需要停止
        if self.car_sg90 is not None:
            # 运行时延迟换档
            if self.sg_to_pos is not None and self.move_state != 0:
                self.car_sg90.change_pos(self.sg_to_pos)
                self.sg_to_pos = None
            else:
                self.car_sg90.stop()
    
    # 测距定时更新
    def sensor_timer_update(self, t):
        self.sensor_work_time += 1
        if self.sensor_work_time > self.sensor_work_interval:
            cur_sensor_dis = self.get_front_distance()
            # 运行时检测到当前距离过近，则停止运动
            if cur_sensor_dis < CAR_STOP_DIS:
                self.set_speed_dir(-1, 0)
            else:
                self.sensor_work_interval = self.calc_sensor_interval(cur_sensor_dis)
                self.sensor_work_time = 0


    # 根据当前距离计算下次测距间隔
    def calc_sensor_interval(self, car_dis):
        if car_dis <= 20:
            return 1
        elif car_dis >= 180:
            return 10
        else:
            return 0.05625 * car_dis - 0.125

    # 设置led提示灯的状态
    #value:灯控制值，0或1
    def set_led_value(self, value):
        self.ioext.set_led_value(value)

    # 设置筒灯的开关
    #value:灯控制值，0或1
    def set_lit_value(self, value):
        self.ioext.set_lit_value(value)

    # 获取当前障碍物的距离
    def get_front_distance(self):
        distance = 999
        if self.car_sensor is not None:
            try:
                distance = self.car_sensor.distance_cm()
        #         print(f'{num}Distance:', distance, 'cm')
            except OSError as ex:
                print('ERROR getting distance:', ex)
        return distance

    # 速度等级转换为pwm
    def convert_level_pwm(self, speed_level):
        level_info = speed_levels_dic[speed_level - 1]
        self.sg_to_pos = level_info['pos']
        return level_info['pwm']