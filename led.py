# 发光LED类显示类，可控制闪烁或常亮
from machine import Timer,Pin

class blink_led:
    # 初始化方法
    # pin:指定引脚
    # timer_id:指定的定时器Id
    def __init__(self, pin, timer_id):
        self.led_pin = Pin(pin, Pin.OUT)
        self.timer_id = timer_id
        self.led_timer = None
        # 闪烁时当前的值
        self.blink_light = False
    
    # 设置常亮或常灭
    def set_light(self, light):
        self.led_pin.value(light and 1 or 0)
        self.blink_light = light
        if self.led_timer != None:
            self.led_timer.deinit()
            self.led_timer = None
            
    # 设置闪烁
    # interval:设置闪烁间隔时间
    def set_blink(self, interval):
        if interval < 0.1:
            return
        # 闪烁前先熄灭led
        self.set_light(False)
        # 按新间隔重新创建timer
        self.led_timer = Timer(self.timer_id)
        self.led_timer.init(period=int(interval * 1000), mode=Timer.PERIODIC, callback=self.led_blink)
        
    # 闪烁方法
    def led_blink(self, t):
        self.blink_light = not self.blink_light
        self.led_pin.value(self.blink_light and 1 or 0)
        