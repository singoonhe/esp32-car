# 发光LED类显示类，可控制闪烁或常亮
from machine import Timer,Pin

class blink_led:
    # 初始化方法
    # pin:指定引脚
    # timer_id:指定的定时器Id
    def __init__(self, pin, timer_id):
        self.led_pin = Pin(pin, Pin.OUT, Pin.PULL_DOWN)
        # 闪烁时当前的值
        self.blink_light = False
        # 初始化定时器, 传入非法timer_id表示不启动闪烁功能
        if timer_id >= -1:
            self.led_timer = Timer(timer_id)
    
    # 设置常亮或常灭
    def set_light(self, light):
        self.blink_light = light
        self.led_pin.value(int(self.blink_light))
        # 取消回调
        if self.led_timer:
            self.led_timer.deinit()
            
    # 设置闪烁
    # interval:设置闪烁间隔时间
    def set_blink(self, interval):
        if interval < 0.1 or not self.led_timer:
            return
        # 闪烁前先熄灭led
        self.set_light(False)
        # 重置触发间隔
        self.led_timer.init(period=int(interval * 1000), mode=Timer.PERIODIC, callback=self.led_blink)
        
    # 闪烁方法
    def led_blink(self, t):
        # print('led_blink')
        self.blink_light = not self.blink_light
        self.led_pin.value(int(self.blink_light))
        