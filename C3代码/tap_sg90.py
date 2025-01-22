#舵机控制类
import time
from machine import Pin,PWM

class tap_sg90:
    # 初始化方法
    def __init__(self, pin1, pin2):
        self.sg901_pwm = PWM(Pin(pin1, Pin.OUT))
        self.sg901_pwm.freq(50)
        self.sg902_pwm = PWM(Pin(pin2, Pin.OUT))
        self.sg902_pwm.freq(50)
        # 标记当前舵机是否移动
        self.start_time = 0
        # 当前档位
        self.cur_pos = None
        # 中间舵机角度，将舵机移动范围控制在0-180度之间
        self.center_angle = 90
        # self.change_pos(dpos)

    # 切换对应的档位(1/2)
    def change_pos(self, pos):
        if self.cur_pos != pos:
            self.rotate(pos == 1 and 66 or 0)
            self.cur_pos = pos
        
    # 设置放置角度
    def rotate(self, angle):
        angle = max(0, min(angle + self.center_angle, 180))
        ts = int((angle/180*2+0.5)/20*1023)
        self.sg901_pwm.duty(ts)
        self.sg902_pwm.duty(ts)
        self.start_time = time.time()

    # 释放舵机
    def stop(self):
        if self.start_time > 0 and (time.time() - self.start_time) >= 1:
            self.sg901_pwm.duty(0)
            self.sg902_pwm.duty(0)
            self.start_time = 0
