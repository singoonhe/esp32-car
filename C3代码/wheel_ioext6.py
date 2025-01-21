#车轮控制IO扩展数据类
from machine import Pin,SoftI2C

class wheel_ioext6:
    # 初始化方法
    def __init__(self, scl, sda, i2c_addr):
        # 初始化i2c
        self.i2c_addr = i2c_addr
        self.i2c = SoftI2C(scl=Pin(scl), sda=Pin(sda), freq=10000)
        # 上一次发送的i2c值，避免重复发送
        self.last_byte = 0x00
        # 最终输出值
        self.write_buff = bytearray(1)

    # 设置双电机的状态
    # state:旋转状态，0(停止)、1(正转)、2(左转圈)、-1(反转)、-2(右转圈)
    def set_motors_state(self, state):
        cur_byte = self.last_byte
        # 先清除对应位的值
        cur_byte = cur_byte & 0b00001111
        # 设置左电机、右电机的状态
        if state == 1:
            cur_byte = cur_byte|0b01010000
        elif state == 2:
            cur_byte = cur_byte|0b01100000
        elif state == -1:
            cur_byte = cur_byte|0b10100000
        elif state == -2:
            cur_byte = cur_byte|0b10010000
        # 设置当前byte值
        self.send_byte_i2c(cur_byte)

    # 设置指示灯的状态
    #value:灯控制值，0或1
    def set_led_value(self, value):
        # 控制第5位bit的值
        self.set_bit_value(4, value)

    # 控制指示灯改变状态
    def turn_led_value(self):
        # 读取第5位bit的值
        cur_value = (self.last_byte >> 4) & 1
        self.set_led_value(cur_value == 0 and 1 or 0)

    # 设置筒灯的状态
    #value:灯控制值，0或1
    def set_lit_value(self, value):
        # 控制第6位bit的值
        self.set_bit_value(5, value)
    
    # 发送当前的i2c数据
    def send_byte_i2c(self, cur_byte):
        if self.last_byte != cur_byte:
            self.write_buff[0] = cur_byte
            self.i2c.writeto(self.i2c_addr, self.write_buff)
            self.last_byte = cur_byte
            # print('wheel_timer: %d' % i2c_byte)

    # 设置某位的状态
    def set_bit_value(self, bit, value):
        cur_byte = self.last_byte
        if value == 0:
            cur_byte &= ~(1 << bit)
        elif value == 1:
            cur_byte |= (1 << bit)
        # 设置当前byte值
        self.send_byte_i2c(cur_byte)