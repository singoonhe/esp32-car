#车轮控制类, 不使用io扩展器
from machine import Timer, Pin

# 模拟当前的总频值
PWM_FRAME_COUNT = 10

class wheel_timer:
    # 初始化方法
    # pins:控制的4个引脚数组, 先左轮后右轮
    def __init__(self, time_id, pins):
        self.io_pins = []
        for pin in pins:
            self.io_pins.append(Pin(pin, Pin.OUT, Pin.PULL_DOWN))
        # 当前的占空值
        self.pwm_left = 0
        self.pwm_right = 0
        # pwm当前值
        self.cur_pwm_cnt = 0
        # 引脚值缓存，避免重复设置
        self.pin_values = 0
        # 车轮是否向前
        self.move_front = True
        # 很小的定时器，方便模拟PWM
        wheel_timer = Timer(time_id)
        wheel_timer.init(period=5, mode=Timer.PERIODIC, callback=self.wheel_timer_callback)
            
    # 重置车轮的速度及方向
    def set_speed_dir(self, move_dir, speed):
        if move_dir == -1:
            # 当前方向为0，停止移动
            self.pwm_left = 0
            self.pwm_right = 0
        elif move_dir > 225 and move_dir < 315:
            # 左右一起倒车
            self.move_front = False
            self.pwm_left = speed
            self.pwm_right = speed
        else:
            self.move_front = True
            # 转换方向到-45~225之间
            if move_dir >= 315:
                move_dir -= 360
            # 将90度分成speed+1份，计算当前处于的区间值
            step_angle = 90 / (speed + 1)
            # 设置左右轮的速度值
            self.pwm_right = max(0, min(int(move_dir / step_angle), speed))
            self.pwm_left = max(0, min(int((180-move_dir) / step_angle), speed))
#             print(self.pwm_right, self.pwm_left)
        
    # 车轮定时回调
    def wheel_timer_callback(self, t):
        cur_values = 0b00000000
        # 记录左轮的控制位数据
        if self.pwm_left > self.cur_pwm_cnt:
            cur_values |= 0b00000010 if self.move_front else 0b00000001
            cur_values = cur_values << 2
        # 记录右轮的控制位数据
        if self.pwm_right > self.cur_pwm_cnt:
            cur_values |= 0b00000010 if self.move_front else 0b00000001
        # 重置各引脚的状态
        if self.pin_values != cur_values:
            self.pin_values = cur_values
            for i in range(4):
                self.io_pins[3-i].value(cur_values & 0b00000001)
                cur_values = cur_values >> 1
        # 模拟PWM占空比
        self.cur_pwm_cnt += 1
        if self.cur_pwm_cnt >= PWM_FRAME_COUNT:
            self.cur_pwm_cnt = 0
    

