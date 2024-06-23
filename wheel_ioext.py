#车轮控制类
import time
from machine import Timer, Pin, SoftI2C

# 模拟当前的总频值
PWM_FRAME_COUNT = 10
# 闪烁引脚值定义
LIGHT_ON_VALUE = const(0b00000100)
LIGHT_OFF_VALUE = const(0b00000000)

class wheel_timer:
    # 初始化方法
    def __init__(self, scl, sda, time_id):
        # 初始化i2c
        self.i2c = SoftI2C(scl=Pin(scl), sda=Pin(sda), freq=10000)
        i2c_devices = self.i2c.scan()
        # 最终输出值
        self.write_value = 0
        self.write_buff = bytearray(1)
        # 当前的占空值
        self.pwm_left = 0
        self.pwm_right = 0
        # pwm当前值
        self.cur_pwm_cnt = 0
        # 车轮是否向前
        self.move_front = True
        # 上一次发送的i2c值，避免重复发送
        self.last_byte = 0x00
        # 开启车轮改变定时器
        self.i2c_addr = None
        if len(i2c_devices) > 0:
            self.i2c_addr = i2c_devices[0]
            print('use i2c addr ' + hex(self.i2c_addr))
            wheel_timer = Timer(time_id)
            # 很小的定时器，方便模拟PWM
            wheel_timer.init(period=5, mode=Timer.PERIODIC, callback=self.wheel_timer_callback)
        else:
            print('cannot find i2c device')
        # 闪烁引脚间隔时间
        self.blink_interval = 0
        self.blink_time = 0
        self.blink_byte = LIGHT_OFF_VALUE
        # 系统启动后先停止，避免自动重启后还在不停的移动
        self.set_speed_dir(-1, 1)
            
    # 控制器是否准备好
    def is_ready(self):
        return self.i2c_addr != None
            
    # 重置车轮的速度及方向
    def set_speed_dir(self, move_dir, speed):
        if move_dir == -1:
            # 当前方向为0，停止移动
            self.pwm_left = 0
            self.pwm_right = 0
        elif move_dir > 225 and move_dir < 315:
            # 左右一起倒车
            self.move_front = False
            self.pwm_left = speed
            self.pwm_right = speed
        else:
            self.move_front = True
            # 转换方向到-45~225之间
            if move_dir >= 315:
                move_dir -= 360
            # 将90度分成speed+1份，计算当前处于的区间值
            step_angle = 90 / (speed + 1)
            # 设置左右轮的速度值
            self.pwm_right = max(0, min(int(move_dir / step_angle), speed))
            self.pwm_left = max(0, min(int((180-move_dir) / step_angle), speed))
#             print(self.pwm_right, self.pwm_left)
        
    # 设置引脚闪烁
    # interval:闪烁间隔时间，毫秒单位。0时表示不闪烁
    # init_value:闪烁初始值, 1或0
    def set_pin_blink(self, interval_ms, init_value):
        self.blink_interval = interval_ms
        self.blink_time = time.ticks_ms()
        self.blink_byte = init_value == 1 and LIGHT_ON_VALUE or LIGHT_OFF_VALUE
        
    # 车轮定时回调
    def wheel_timer_callback(self, t):
        try:
            i2c_byte = 0b00000000
            # 记录左轮的控制位数据
            if self.pwm_left > self.cur_pwm_cnt:
                i2c_byte |= self.move_front and 0b01010000 or 0b10100000
            # 记录右轮的控制位数据
            if self.pwm_right > self.cur_pwm_cnt:
                i2c_byte |= self.move_front and 0b00000001 or 0b00000010
            # 检查blink是否需要变化
            if self.blink_interval > 0:
                cur_time = time.ticks_ms()
                if (cur_time - self.blink_time) >= self.blink_interval:
                    self.blink_byte = (self.blink_byte == LIGHT_OFF_VALUE) and LIGHT_ON_VALUE or LIGHT_OFF_VALUE
                    self.blink_time = cur_time
            # 发送当前的i2c数据
            self.write_buff[0] = i2c_byte | self.blink_byte
            if self.last_byte != self.write_buff[0]:
                self.i2c.writeto(self.i2c_addr, self.write_buff)
                self.last_byte = self.write_buff[0]
#                 print('wheel_timer: %d' % i2c_byte)
            # 模拟PWM占空比
            self.cur_pwm_cnt += 1
            if self.cur_pwm_cnt >= PWM_FRAME_COUNT:
                self.cur_pwm_cnt = 0
        except KeyboardInterrupt:
            pass
    
