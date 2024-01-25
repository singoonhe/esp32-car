#车轮控制类
from machine import Timer,Pin

# 模拟当前的总频值
PWM_FRAME_COUNT = 10

class wheel_timer:
    # 初始化方法
    def __init__(self, scl, sda):
        # 初始化i2c
        self.i2c = I2C(scl=Pin(scl), sda=Pin(sda), freq=100000)
        i2c_devices = self.i2c.scan()
        # 最终输出值
        self.write_value = 0
        # 当前的占空值
        self.pwm_left = 0
        self.pwm_right = 0
        # pwm当前值
        self.cur_pwm_cnt = 0
        # 车轮是否向前
        self.move_front = True
        # 开启车轮改变定时器
        if len(i2c_devices) > 0:
            self.i2c_addr = i2c_devices[0]
            wheel_timer = Timer()
            # 1ms定时器，方便模拟PWM
            wheel_timer.init(period=1, mode=Timer.PERIODIC, callback=self.wheel_timer_callback)
        else:
            print('cannot find i2c device')
            
    # 重置车轮的速度及方向
    def set_speed_dir(self, move_dir, speed):
        if move_dir == -1:
            # 当前方向为0，停止移动
            self.pwm_left = 0
            self.pwm_right = 0
        elif move_dir > 225 && move_dir < 315:
            # 左右一起倒车
            self.move_front = False
            self.pwm_left = speed
            self.pwm_right = speed
        else:
            # 转换方向到-45~225之间
            if move_dir >= 315:
                move_dir -= 360
            # 右轮限制方向到0~90之间, 超过90为最大值
            right_angle = max(0, min(move_dir, 90))
            self.pwm_right = int(max(1, min((right_angle / 90) * speed, speed)))
            # 左轮限制方向到0~90之间, 超过90为最大值
            left_angle = max(0, min(180-move_dir, 90))
            self.pwm_left = int(max(1, min((left_angle / 90) * speed, speed)))
            
        
    # 车轮定时回调
    def wheel_timer_callback(self, t):
        i2c_byte = 0b00000000
        # 记录左轮的控制位数据
        if self.pwm_left > self.cur_pwm_cnt:
            i2c_byte |= self.move_front and 0b10001000 or 0b01000100
        # 记录右轮的控制位数据
        if self.pwm_right > self.cur_pwm_cnt:
            i2c_byte |= self.move_front and 0b00100010 or 0b00010001
        # 发送当前的i2c数据
        self.i2c.writeto(self.i2c_addr, bytes([i2c_byte]))
        # 模拟PWM占空比
        self.cur_pwm_cnt += 1
        if self.cur_pwm_cnt >= PWM_FRAME_COUNT:
            self.cur_pwm_cnt = 0
    
