#车轮控制类, pwm方式控制
from machine import Pin, PWM

class wheel_pwm:
    # 初始化方法
    # pins：需要的4个引脚列表，前2个代表左边电机，后2个代表右边电机
    # pwms: 需要的2个PWM引脚列表，前1个代表左边电机，后1个代表右边电机
    def __init__(self, pins, pwms):
        self.nor_pins = []
        self.pwm_pins = []
        # 最低的占空比
        self.low_duty = 423
        # 点空比的步进值
        self.duty_step = 102.3 - self.low_duty * 0.1
        # 初始化控制引脚
        for pin in pins:
            self.nor_pins.append(Pin(pin, Pin.OUT))
        # 初始化PWM引脚
        for pin in pwms:
            pwm_pin = PWM(Pin(pin, Pin.OUT), freq=100)
            self.pwm_pins.append(pwm_pin)
            
    # 重置车轮的速度及方向
    def set_speed_dir(self, move_dir, speed):
        # 两边的速度值
        pwm_left = 0
        pwm_right = 0
        # 车轮的行驶值
        value1 = 0
        value2 = 0
        if move_dir == -1:
            # 当前方向为0，停止移动
            pwm_left = 0
            pwm_right = 0
        elif move_dir > 225 and move_dir < 315:
            # 左右一起倒车
            value1 = 0
            value2 = 1
            pwm_left = speed
            pwm_right = speed
        else:
            value1 = 1
            value2 = 0
            # 转换方向到-45~225之间
            if move_dir >= 315:
                move_dir -= 360
            # 右轮限制方向到0~90之间, 超过90为最大值
            right_angle = max(0, min(move_dir, 90))
            pwm_right = int(max(0, min((right_angle / 90) * speed, speed)))
            # 左轮限制方向到0~90之间, 超过90为最大值
            left_angle = max(0, min(180-move_dir, 90))
            pwm_left = int(max(0, min((left_angle / 90) * speed, speed)))
        # 设置左侧电机
        self.set_pin_values(0, value1, value2, pwm_left)
        # 设置右侧电机
        self.set_pin_values(1, value1, value2, pwm_right)
#         print(self.pwm_pins[0], self.pwm_pins[1])
        
    # 设置车轮的引脚状态
    def set_pin_values(self, index, value1, value2, pwm_v):
        # 设置电机的转动方向
        self.nor_pins[index * 2].value(value1)
        self.nor_pins[index * 2 + 1].value(value2)
        # 设置电机的速度，0的时候特殊处理避免最低pwm值
        if pwm_v == 0:
            self.pwm_pins[index].duty(0)
        else:
            duty = int(pwm_v * self.duty_step + self.low_duty)
            self.pwm_pins[index].duty(duty)
    