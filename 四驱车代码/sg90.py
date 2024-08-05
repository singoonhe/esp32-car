#舵机控制类
from machine import Pin,PWM

class sg90:
    # 初始化方法
    # c_angle:中间旋转角度
    def __init__(self, pin, c_angle):
        self.sg90_pwm = PWM(Pin(pin, Pin.OUT))
        self.sg90_pwm.freq(50)
        self.center_angle = c_angle
        self.rotate(0)
        
    # 设置放置角度
    def rotate(self, angle):
        angle = max(0, min(angle + self.center_angle, 180))
        ts = int((angle/180*2+0.5)/20*1023)
        self.sg90_pwm.duty(ts)
