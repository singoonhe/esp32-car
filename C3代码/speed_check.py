import time
from machine import Pin

class speed_check:
    # 初始化方法
    def __init__(self, pin1, pin2):
        self.speed_pin1 = Pin(pin1, Pin.IN)
        self.speed_pin2 = Pin(pin2, Pin.IN)
        # 设置中断
        self.speed_pin1.irq(trigger=self.speed_pin1.IRQ_RISING, handler=self.speed_sensor_trigger)
        self.speed_pin2.irq(trigger=self.speed_pin1.IRQ_RISING, handler=self.speed_sensor_trigger)
        # 当前速度
        self.cur_speed = 0
        # 初始化计数
        self.trigger_count1 = 0
        self.trigger_count2 = 0
        # 标记是否需要更新速度
        self.start_time = 0

    # 定义中断回调函数
    def speed_sensor_trigger(self, pin):
        if pin == self.speed_pin1:
            self.trigger_count1 += 1
        elif pin == self.speed_pin2:
            self.trigger_count2 += 1

    # 定时更新测速
    def update(self):
        cur_time = time.time()
        if (cur_time - self.start_time) >= 1:
            self.start_time = cur_time
            self.cur_speed = round((self.trigger_count1 + self.trigger_count2) * 0.5)
            self.trigger_count1 = 0
            self.trigger_count2 = 0

    # 获取当前的运转速度
    def get_wheel_speed(self):
        return self.cur_speed
