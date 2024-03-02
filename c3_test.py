from machine import Pin, SoftI2C, PWM
import time


pwm_pin1 = PWM(Pin(12, Pin.OUT), freq=50)
pwm_pin1.duty(200)
pwm_pin2 = PWM(Pin(13, Pin.OUT), freq=50)
pwm_pin2.duty(200)

edge_value1 = 0
edge_count1 = 0
# 定义中断处理函数
def edge1_handler(pin):
    global edge_value1
    global edge_count1
    if edge_value1 != pin.value():
        edge_count1 += 1
        edge_value1 = pin.value()
edge1_pin = Pin(2, Pin.IN, edge_value1)
edge1_pin.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=edge1_handler)

edge_value2 = 0
edge_count2 = 0
def edge2_handler(pin):
    global edge_value2
    global edge_count2
    if edge_value2 != pin.value():
        edge_count2 += 1
        edge_value2 = pin.value()
edge2_pin = Pin(3, Pin.IN, edge_value2)
edge2_pin.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=edge2_handler)

i2c = SoftI2C(scl=Pin(0), sda=Pin(1), freq=10000)
i2c_addr = i2c.scan()[0]
write_buff = bytearray(1)
write_buff[0] = 0b01000100
i2c.writeto(i2c_addr, write_buff)
time.sleep_ms(2000)
write_buff[0] = 0b00000000
i2c.writeto(i2c_addr, write_buff)

print("edge_count1:" + str(edge_count1) + " edge_count2:" + str(edge_count2))
