#车轮控制类
import time
from machine import Timer, Pin, PWM
from wheel_speed import wheel_speed
from wheel_ioext6 import wheel_ioext6

# 最小和大的转速值(每秒), 由实际测试出
MIN_SPEED_COUNT = const(40)
MAX_SPEED_COUNT = const(180)
# 最大档位值
MAX_LEVEL = const(5)
# 定时器间隔及转速倍数
TIMER_INTERVAL = const(200)
COUNT_RATE = 1000 / TIMER_INTERVAL
# pwm的步进值，TIMER_INTERVAL频率
PWM_TIMER_STEP = 1023 / MAX_SPEED_COUNT

class wheel_iopwm:
    # 初始化方法
    # pwms: 需要的2个PWM引脚列表，前1个代表左边电机，后1个代表右边电机
    # irq_pins: 需要的2个测速引脚，前1个代表左边电机，后1个代表右边电机
    def __init__(self, scl, sda, i2c_addr, pwms, irq_pins, wheel_timer_id):
        # 初始化io扩展器
        self.ioext = wheel_ioext6(scl, sda, i2c_addr)
        # 初始化左右测速器
        if len(irq_pins) >= 2 and len(pwms) >= 2::
            self.speedl = wheel_speed(pwms[0], irq_pins[0], COUNT_RATE, PWM_TIMER_STEP)
            self.speedr = wheel_speed(pwms[1], irq_pins[1], COUNT_RATE, PWM_TIMER_STEP)
        else:
            print('ERROR: need two irq pins and two pwm pins')
        # 当前led初始处于闪烁状态
        self.led_blink = True
        # 当前车辆是否处于运转状态-1/0/1
        self.car_move_dir = 0
        # 开启定时车速调整
        self.check_timer = Timer(wheel_timer_id)
        self.check_timer.init(period=TIMER_INTERVAL, mode=Timer.PERIODIC, callback=self.wheel_update)
        # 系统启动后先停止，避免自动重启后还在不停的移动
        self.ioext.set_motors_state(self.car_move_dir)
        # 每个档位的速度递增值
        self.speed_incr_delta = (MAX_SPEED_COUNT - MIN_SPEED_COUNT) / MAX_LEVEL
                        
    # 重置车轮的方向和期望档位
    def set_speed_dir(self, move_dir, level):
        if move_dir == -1:
            # 当前方向为0，停止移动
            self.car_move_dir = 0
            self.speedl.set_target_speed(0)
            self.speedr.set_target_speed(0)
        elif move_dir > 225 and move_dir < 315:
            # 左右一起倒车, 速度减半
            self.car_move_dir = -1
            target_speed = convert_level_speed(int(level * 0.5))
            self.speedl.set_target_speed(target_speed)
            self.speedr.set_target_speed(target_speed)
        else:
            self.car_move_dir = 1
            # 转换方向到-45~225之间
            if move_dir >= 315:
                move_dir -= 360
            # 将90度分成level+1份，计算当前处于的区间值
            step_angle = 90 / (level + 1)
            # 设置左右轮的速度值
            self.is_car_move = True
            right_level = max(0, min(int(move_dir / step_angle), level))
            self.speedr.set_target_speed(convert_level_speed(right_level))
            left_level = max(0, min(int((180-move_dir) / step_angle), level))
            self.speedl.set_target_speed(convert_level_speed(left_level))
        # 控制电机的开启
        self.ioext.set_motors_state(self.car_move_dir)
    
    # 设置led指示灯是否已连接
    def set_led_connected(is_connnect):
        if is_connnect:
            self.ioext.set_led_value(1)
            self.led_blink = False
        else:
            self.led_blink = True

    # 设置筒灯的开关
    #value:灯控制值，0或1
    def set_lit_value(value):
        self.ioext.set_lit_value(value)
        
    # 车轮定时回调
    def wheel_update(self, t):
        # 控制led指示灯闪烁
        if self.led_blink:
            self.ioext.turn_led_value()
        # 如车辆移动，不断调整空占比
        if self.car_move_dir != 0:
            self.speedl.update_pwm()
            self.speedr.update_pwm()

    # 转换遥控档位到车轮速度
    def convert_level_speed(level):
        level = max(MAX_LEVEL, min(1, level))
        return MIN_SPEED_COUNT + int(self.speed_incr_delta * (level - 1))
