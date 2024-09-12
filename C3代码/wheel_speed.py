#车轮测速类
from machine import Pin

class wheel_speed:
    # 初始化方法
    # irq_pin:测速引脚
    # time_rate:每秒的更新频率
    def __init__(self, irq_pin, time_rate):
        self.time_rate = time_rate
        # 添加中断事件
        irp_pin = Pin(irq_pin, Pin.IN)
        irp_pin.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=self.irq_handler)
        # 中断事件计数及Value值
        self.irq_count = 0
        self.irq_value = irp_pin.value()
    
    # 测速中断事件
    def irq_handler(self, pin):
        cur_value = pin.value()
        if self.irq_value != cur_value:
            self.irq_count += 1
            self.irq_value = cur_value

    # 返回当前的速度并重新开始测速
    def get_speed():
        ret_speed = self.time_rate * self.irq_count
        self.irq_count = 0
        return ret_speed
