from ufont import BMFont
from dht import DHT11
from machine import I2C, Pin
from ssd1306 import SSD1306_I2C

class SCREEN96:
    # 初始化方法
    def __init__(self, scl_pin, sda_pin, dh11_pin):
        # 初始化屏幕
        i2c = I2C(scl=Pin(scl_pin), sda=Pin(sda_pin))
        self.isplay = SSD1306_I2C(128, 64, i2c)
        # 设置字体
        self.font = BMFont("used_font.bmf")
        # 初始化DH11
        dht_pin = Pin(dh11_pin, Pin.IN)
        self.dht_sensor = DHT11(dht_pin)
        
        
    # 刷新一次设置项
    # 清屏参数：`clear=True`
    # `show=True` 使得屏幕及时更新
    def refresh(self):
        self.font.text(self.display, "你好", 48, 16, show=True)
        
    # 更新一次温湿度
    def refreshDH(self):
        self.dht_sensor.measure()
        temp_str = "温度: {}°C".format(self.dht_sensor.temperature())
        humi_str = "湿度: {}%".format(self.dht_sensor.humidity())
        self.font.text(self.display, temp_str, 48, 16, show=True)
        self.font.text(self.display, humi_str, 48, 16, show=True)

