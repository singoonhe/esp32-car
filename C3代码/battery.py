# 测电量类
from machine import Pin, ADC

class adc_battery:
    # 初始化方法
    # pin:指定引脚
    def __init__(self, pin):
        self.adc_pin = ADC(Pin(pin))
        # 设置测量电压范围到3V
        self.adc_pin.atten(ADC.ATTN_11DB)
        # 7.2V时读数3327，8V时为3758
        # 理论最大值
        self.adc_max = 3800
        # 读数偏差值
        self.voffset_rate = 1.1
        # 理论最小值(1V对应计数*偏差*最低电压)
        self.adc_min = int(((3758 - 3327) / 0.8) * self.voffset_rate * 5.2)
        # 百分比量程
        self.full_step = self.adc_max - self.adc_min
        # 初始电量为100
        self.battery_percent = 100
       
    # 更新并返回当前电量百分比
    def update_battery_per(self):
        ret_value = self.adc_pin.read()
        ret_per = int((ret_value - self.adc_min) * 100 / self.full_step)
#         print('adc read:' + str(ret_value) + ' p#ercent:' + str(ret_per))
        self.battery_percent = max(0, min(ret_per, 100))
        return self.battery_percent
    
    # 获取历史电量百分比
    def get_battery_per(self):
        return self.battery_percent