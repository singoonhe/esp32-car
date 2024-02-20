# 测电量类
from machine import Pin, ADC

class adc_battery:
    # 初始化方法
    # pin:指定引脚
    def __init__(self, pin):
        self.adc_pin = ADC(Pin(pin))
        # 设置测量电压范围到3.3V
        self.adc_pin.atten(ADC.ATTN_11DB)
        # 理论最大值，加上偏移校正
        self.adc_max = (4.2 * 2 * 4096) / (5 * 3.3) + 200
        # 理论最小值，加上偏移校正
        self.adc_min = (2.75 * 2 * 4096) / (5 * 3.3) + 200
        # 百分比量程
        self.full_step = self.adc_max - self.adc_min
       
    # 获取当前电量百分比
    def get_battery_per(self):
        ret_value = self.adc_pin.read()
        ret_per = int((ret_value - self.adc_min) / self.full_step * 100)
        return max(0, min(ret_per, 100))