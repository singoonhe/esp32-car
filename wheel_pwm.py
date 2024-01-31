#车轮控制类, pwm方式控制
from machine import Pin

class wheel_pwm:
    # 初始化方法
    # pins：需要的8个引脚列表，前4个代表左边电机，后4个代表右边电机
    def __init__(self, pins):
        self.pwm_pins = []
        # 初始化PWM引脚
        for x in range(len(pins)):
            self.pwm_pins[x] = machine.PWM(Pin(pins[x], Pin.OUT), freq=1000)
            
    # 重置车轮的速度及方向
    def set_speed_dir(self, move_dir, speed):
        # 两边的速度值
        pwm_left = 0
        pwm_right = 0
        # 车轮是否向前
        move_front = True
        if move_dir == -1:
            # 当前方向为0，停止移动
            pwm_left = 0
            pwm_right = 0
        elif move_dir > 225 and move_dir < 315:
            # 左右一起倒车
            move_front = False
            pwm_left = speed
            pwm_right = speed
        else:
            move_front = True
            # 转换方向到-45~225之间
            if move_dir >= 315:
                move_dir -= 360
            # 右轮限制方向到0~90之间, 超过90为最大值
            right_angle = max(0, min(move_dir, 90))
            pwm_right = int(max(0, min((right_angle / 90) * speed, speed)))
            # 左轮限制方向到0~90之间, 超过90为最大值
            left_angle = max(0, min(180-move_dir, 90))
            pwm_left = int(max(0, min((left_angle / 90) * speed, speed)))
        # 设置左侧电机占空比
        left_duty = int(pwm_left * 102.3)
        for x in range(2):
            self.pwm_pins[x * 2].duty(move_front and left_duty or 0)
            self.pwm_pins[x * 2 + 1].duty(move_front and 0 or left_duty)
        # 设置右侧电机占空比
        right_duty = int(pwm_right * 102.3)
        for x in range(2):
            self.pwm_pins[x * 2].duty(move_front and right_duty or 0)
            self.pwm_pins[x * 2 + 1].duty(move_front and 0 or right_duty)
    
