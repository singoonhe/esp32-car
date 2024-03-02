#车轮控制类, pwm方式控制
from machine import Pin, PWM, Timer

# 最小和大的转速值(每秒), 由实际测试出
MIN_SPEED_COUNT = const(80)
MAX_SPEED_COUNT = const(200)
# 空占值步进调节(每秒), 与定时器也有关
DUTY_DIFF_STEP = const(100)
# 最小的空占比及默认步进. (min + step * 9) < 1023
DEFAULT_MIN_DUTY = const(258)
DEFAULT_DUTY_STEP = const(85)
# 定时器间隔及转速倍数
TIMER_INTERVAL = const(200)
COUNT_RATE = 1000 / TIMER_INTERVAL

class wheel_pwm:
    # 初始化方法
    # pins：需要的4个引脚列表，前2个代表左边电机，后2个代表右边电机
    # pwms: 需要的2个PWM引脚列表，前1个代表左边电机，后1个代表右边电机
    # irq_pins: 需要的2个测速引脚，前1个代表左边电机，后1个代表右边电机
    def __init__(self, pins, pwms, irq_pins, wheel_timer_id):
        self.nor_pins = []
        self.pwm_pins = []
        # 初始化各速度下的空占比
        self.speed_dutys = [0]
        for i in range(10):
            self.speed_dutys.append(min(1023, DEFAULT_MIN_DUTY + DEFAULT_DUTY_STEP * i))
        # 初始化各速度下的期望转速值
        self.speed_counts = [0]
        speed_count_step = (MAX_SPEED_COUNT - MIN_SPEED_COUNT) * 0.1
        for i in range(10):
            self.speed_counts.append(int(i * speed_count_step) + MIN_SPEED_COUNT)
        # 当前遥控器设置的速度值
        self.remote_speed = [0, 0]
        # 初始化控制引脚
        for pin in pins:
            self.nor_pins.append(Pin(pin, Pin.OUT))
        # 初始化PWM引脚
        for pin in pwms:
            pwm_pin = PWM(Pin(pin, Pin.OUT), freq=50)
            self.pwm_pins.append(pwm_pin)
        # 添加中断事件
        irq_handlers = (self.irq_handler_l, self.irq_handler_r)
        for i in range(2):
            irp_pin = Pin(irq_pins[i], Pin.IN)
            irp_pin.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=irq_handlers[i])
        # 中断事件计数及Value值
        self.irq_counts = [0, 0]
        self.irq_values = [0, 0]
        # 开启定时车速调整
        self.check_timer = Timer(wheel_timer_id)
        self.timer_running = False
        
            
    # 重置车轮的速度及方向
    def set_speed_dir(self, move_dir, speed):
        # 速度检测功能开关
        if move_dir == -1 and self.timer_running:
            # 停止测速功能
            self.check_timer.deinit()
            self.timer_running = False
        elif move_dir != -1 and not self.timer_running:
            # 开启测速功能
            self.check_timer.init(period=TIMER_INTERVAL, mode=Timer.PERIODIC, callback=self.check_count_speed)
            self.timer_running = True
            # 清空上次的测速值
            for i in range(2):
                self.irq_counts[i] = 0
        # 两边的速度值
        self.remote_speed[0] = 0
        self.remote_speed[1] = 0
        # 车轮的行驶值
        value1 = 0
        value2 = 0
        if move_dir == -1:
            # 当前方向为0，停止移动
            self.remote_speed[0] = 0
            self.remote_speed[1] = 0
        elif move_dir > 225 and move_dir < 315:
            # 左右一起倒车
            value1 = 0
            value2 = 1
            self.remote_speed[0] = speed
            self.remote_speed[1] = speed
        else:
            value1 = 1
            value2 = 0
            # 转换方向到-45~225之间
            if move_dir >= 315:
                move_dir -= 360
            # 将90度分成speed+1份，计算当前处于的区间值
            step_angle = 90 / (speed + 1)
            # 设置左右轮的速度值(0~10)
            self.remote_speed[0] = max(0, min(int((180-move_dir) / step_angle), speed))
            self.remote_speed[1] = max(0, min(int(move_dir / step_angle), speed))
        # 设置双侧电机初始值
        for i in range(2):
            self.set_pin_values(i, value1, value2, self.remote_speed[i])
        
    # 设置车轮的引脚状态
    def set_pin_values(self, index, value1, value2, pwm_v):
        # 设置电机的转动方向
        self.nor_pins[index * 2].value(value1)
        self.nor_pins[index * 2 + 1].value(value2)
        # 设置电机的速度
        self.pwm_pins[index].duty(self.speed_dutys[pwm_v])
            
    # 定时检测当前速度值是否合理，并修正
    def check_count_speed(self, t):
        for i in range(2):
            remote_speed = self.remote_speed[i]
            # 每秒转速
            count_s = COUNT_RATE * self.irq_counts[i]
            # 与期望的差值
            count_diff = self.speed_counts[remote_speed] - count_s
            # 电机空占比修正
            fix_ratio = max(-1, min(1, count_diff / DUTY_DIFF_STEP))
            fix_duty = self.speed_dutys[remote_speed] + int(fix_ratio * 50)
            fix_duty = max(0, min(fix_duty, 1023))
            self.pwm_pins[i].duty(fix_duty)
            # 修正值存储起来下次继续使用
            self.speed_dutys[remote_speed] = fix_duty
            self.irq_counts[i] = 0
#             print(count_s, count_diff, fix_duty)
        
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
        
        
    

