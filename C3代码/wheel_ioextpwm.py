#车轮控制类
import time
from machine import Timer, Pin, PWM
from wheel_ioext6 import wheel_ioext6

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

    # 重置车轮的方向和期望档位
    def set_speed_dir(self, move_dir, speed_pwm):
        if move_dir == -1:
            # 当前方向为0，停止移动
            self.ioext.set_motors_state(0)
        elif move_dir > 225 and move_dir < 315:
            # 左右一起倒车, 速度减半
            self.ioext.set_motors_state(-1)
        else:
            # 转换方向到-45~225之间
            if move_dir >= 315:
                move_dir -= 360
            if move_dir >= -45 and move_dir <= 45:
                # 右转
                self.ioext.set_motors_state(-2)
            elif move_dir >= 135 and move_dir <= 225:
                # 左转
                self.ioext.set_motors_state(2)
            else:
                # 直行
                self.ioext.set_motors_state(1)
        # 控制电机的频率
        self.pwm1.duty(speed_pwm)
        self.pwm2.duty(speed_pwm)
    
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

    # 设置led提示灯的状态
    #value:灯控制值，0或1
    def set_led_value(self, value):
        self.ioext.set_led_value(value)

    # 设置筒灯的开关
    #value:灯控制值，0或1
    def set_lit_value(self, value):
        self.ioext.set_lit_value(value)