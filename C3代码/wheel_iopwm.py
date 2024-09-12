#车轮控制类
import time
from machine import Timer, Pin, PWM, SoftI2C
from wheel_speed import wheel_speed

# 最小和大的转速值(每秒), 由实际测试出
MIN_SPEED_COUNT = const(40)
MAX_SPEED_COUNT = const(180)
# 定时器间隔及转速倍数
TIMER_INTERVAL = const(200)
COUNT_RATE = 1000 / TIMER_INTERVAL

# 闪烁引脚值定义
LIGHT_ON_VALUE = const(0b00000100)
LIGHT_OFF_VALUE = const(0b00000000)

class wheel_iopwm:
    # 初始化方法
    # pwms: 需要的2个PWM引脚列表，前1个代表左边电机，后1个代表右边电机
    # irq_pins: 需要的2个测速引脚，前1个代表左边电机，后1个代表右边电机
    def __init__(self, scl, sda, i2c_addr, pwms, irq_pins, wheel_timer_id):
        # 当前的占空值
        self.pwm_left = 0
        self.pwm_right = 0
        # 开启定时车速调整
        self.check_timer = Timer(wheel_timer_id)
        self.check_timer.init(period=TIMER_INTERVAL, mode=Timer.PERIODIC, callback=self.check_count_speed)
        self.timer_running = False
        # 闪烁引脚间隔时间
        self.blink_interval = 0
        self.blink_time = 0
        self.blink_byte = LIGHT_OFF_VALUE
        # 系统启动后先停止，避免自动重启后还在不停的移动
        self.set_speed_dir(-1, 1)
                        
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
    
    # 测速中断事件
    def irq_handler(self, pin, i):
        cur_value = pin.value()
        if self.irq_values[i] != cur_value:
            self.irq_counts[i] += 1
            self.irq_values[i] = cur_value
            
    # 左轮测速中断事件
    def irq_handler_l(self, pin):
        self.irq_handler(pin, 0)
        
    # 右轮测速中断事件
    def irq_handler_r(self, pin):
        self.irq_handler(pin, 1)
