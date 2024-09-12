#车轮测速类
from machine import Pin

class wheel_speed:
    # 初始化方法
    # pwm_pin: PWM引脚
    # irq_pin:测速引脚
    # time_rate:每秒的更新频率
    # pwm_rate:pwm的速度增长倍数，假定1023达到最大速度
    def __init__(self, pwm_pin, irq_pin, time_rate, pwm_rate):
        self.time_rate = time_rate
        self.pwm_rate = pwm_rate
        # 添加中断事件
        irp_pin = Pin(irq_pin, Pin.IN)
        irp_pin.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=self.irq_handler)
        # 中断事件计数及Value值
        self.irq_count = 0
        self.irq_value = irp_pin.value()
        # 初始化pwm
        self.pwm = PWM(Pin(pwms[0], Pin.OUT), freq=50)
        # 当前车轮的期望速度
        self.target_speed = 0
        # 当前车轮的速度
        self.cur_speed = 0
        # 当前的空占比值
        self.cur_pwm = 0
        self.pwm.duty(self.cur_pwm)

    # 重置当前车轮的期望速度
    def set_target_speed(speed):
        self.target_speed = speed

    # 返回当前的pwm空占比值并重新开始测速
    def update_pwm():
        # 空占比为0时不启动计算
        if self.target_speed == 0:
            # 不转动时将空占比归0
            if self.cur_pwm > 0:
                self.cur_pwm = 0
                self.pwm.duty(self.cur_pwm)
            return
            
        # 获取当前的速度反馈
        ret_speed = self.time_rate * self.irq_count
        self.irq_count = 0
        # 计算期望的空占比
        diff = abs(self.target_speed - ret_speed) * self.pwm_rate
        if self.target_speed > ret_speed:
            self.cur_pwm = self.cur_pwm + diff
        elif self.target_speed < ret_speed:
            self.cur_pwm = self.cur_pwm - diff
        self.cur_pwm = max(0, min(int(self.cur_pwm), 1023))
        # 重置空占比值
        self.pwm.duty(self.cur_pwm)
    
    # 测速中断事件
    def irq_handler(self, pin):
        cur_value = pin.value()
        if self.irq_value != cur_value:
            self.irq_count += 1
            self.irq_value = cur_value
