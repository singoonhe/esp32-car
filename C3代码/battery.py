# 测电量类
from machine import Pin, ADC

# 理论与实际的偏移值
ADC_OFFSET = const(50)

class adc_battery:
    # 初始化方法
    # pin:指定引脚
    def __init__(self, pin):
        self.adc_pin = ADC(Pin(pin))
        # 设置测量电压范围到3V
        self.adc_pin.atten(ADC.ATTN_11DB)
        # 理论最大值
        self.adc_max = (4.2 * 2 * 4096) / (5 * 3)
        # 理论最小值
        self.adc_min = (2.75 * 2 * 4096) / (5 * 3)
        # 百分比量程
        self.full_step = self.adc_max - self.adc_min
       
    # 获取当前电量百分比
    def get_battery_per(self):
        ret_value = self.adc_pin.read()
        # 7.88V时读数2100，理论7.88V时应为2150，存在一定偏差
        # 注意：连USB与电池时，读数可能不一致
        ret_per = int((ret_value + ADC_OFFSET - self.adc_min) * 100 / self.full_step)
#         print('adc read:' + str(ret_value) + ' percent:' + str(ret_per))
        return max(0, min(ret_per, 100))