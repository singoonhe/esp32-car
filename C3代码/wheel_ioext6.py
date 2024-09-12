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
    # state_l:旋转状态，0(停止)、1(正转)、-1(反转)
    def set_motors_state(state_l, state_r):
        cur_byte = self.last_byte
        # 先清除对应位的值
        cur_byte = cur_byte & 0b00001111
        # 设置左电机的状态
        if state_l == 1:
            cur_byte = cur_byte|0b01000000
        elif state_l == -1:
            cur_byte = cur_byte|0b10000000
        # 设置右电机的状态
        if state_r == 1:
            cur_byte = cur_byte|0b00010000
        elif state_r == -1:
            cur_byte = cur_byte|0b00100000
        # 设置当前byte值
        self.send_byte_i2c(cur_byte)

    # 设置指示灯的状态
    #value:灯控制值，0或1
    def set_led_value(value):
        cur_byte = self.last_byte
        if value == 0:
            cur_byte &= ~(1 << 4)
        elif value == 1:
            cur_byte |= (1 << 4)
        # 设置当前byte值
        self.send_byte_i2c(cur_byte)
    
    # 发送当前的i2c数据
    def send_byte_i2c(cur_byte):
        if self.last_byte != cur_byte:
            self.write_buff[0] = cur_byte
            self.i2c.writeto(self.i2c_addr, self.write_buff)
            self.last_byte = cur_byte
            # print('wheel_timer: %d' % i2c_byte)

    # 设置某位的状态
    def set_byte():
        pass