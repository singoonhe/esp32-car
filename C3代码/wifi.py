# wifi连接类
import os
import time
import _thread
import network
import machine
from socket import *
from machine import Timer,Pin
from data import network_data

# sta_info参数详解:
    # cmd_heart: bool型，是否开启定时心跳功能。默认不启用
    # sleep_time: int型，未连接时自动睡眠秒数。默认为0表示不启用
    # ap_state: bool型，是否开启ap模式。默认开启
    # ap_name: string型，ap模式下wifi名
    # ap_psd: string型，ap模式下wifi密码
    # ssid: string型，非ap模式下连接的wifi名
    # psd: string型，非ap模式下连接的wifi密码
    # heart_call: 心跳回调事件，仅开启心跳功能时有效. void ()
    # target_link_call: 设备连接状态变化回调，void (bool)
    # ex_cmd_call: 车辆控制事件回调，void (string, string)
    # interrupt_call: 程序中断事件回调
class wifi_network:
    # 初始化方法
    # sta_info:连接网络的信息列表
    def __init__(self, sta_info):
        # 初始化网络
        self.ip = '0'
        self.udp_socket = None
        # 网络检查，未收到数据的计数
        self.network_check = 0
        # 指定的数据接收者
        self.command_target = None
        # 自动睡眠倒计时秒数
        self.sleep_time = sta_info.get('sleep_time', 0)
        # 回调事件
        self.target_link_call = sta_info.get('target_link_call', None)
        self.heart_call = sta_info.get('heart_call', None)
        self.ex_cmd_call = sta_info.get('ex_cmd_call', None)
        self.interrupt_call = sta_info.get('interrupt_call', None)
        # 是否需要发送心跳数据
        self.cmd_heart = sta_info.get('cmd_heart') == True
        # 是否支持非AP模式
        if 'ap_state' in sta_info and not sta_info['ap_state']:
            self.init_wifi(sta_info, False)
        else:
            # 默认开启AP模式
            self.init_wifi(sta_info, True)
        
    # 初始化网络
    def init_wifi(self, sta_info, is_ap):
        if not is_ap:
            sta_if = network.WLAN(network.STA_IF)
            # 网络可能已经连接
            if not sta_if.isconnected():
                sta_if.active(True)
                try:
                    sta_if.connect(sta_info['ssid'], sta_info['psd'])
                    while not sta_if.isconnected():
                        time.sleep_ms(100)
                    self.ip = sta_if.ifconfig()[0]
                except:
                    print("Network connect failed, please reset system")
            else:
                self.ip = sta_if.ifconfig()[0]
        else:
            ap_if = network.WLAN(network.AP_IF)
            try:
                ap_if.config(essid=sta_info['ap_name'], password=sta_info['ap_psd'], authmode=3, max_clients=3)
                ap_if.active(True)
                self.ip = ap_if.ifconfig()[0]
            except:
                print("Network start ap failed, please reset system")
            
    # 开始接受网络连接
    # out_timer_id:超时检测的timer_id, ESP32和ESP32-C3存在区别
    def start_socket(self, out_timer_id):
        if len(self.ip) < 8:
            print('network init failed')
            return
        
        print("current ip : " + self.ip)
        # 开启非阻塞UDP
        self.udp_socket = socket(AF_INET, SOCK_DGRAM)
        self.udp_socket.bind((self.ip, 7890))
        self.udp_socket.setblocking(False)
        # 开启网络连接检查
        wifi_timer = Timer(out_timer_id)
        wifi_timer.init(period=500, mode=Timer.PERIODIC, callback=self.check_wifi_target)
        # 循环接收数据
        try:
            # 初始调用target未连接
            if self.target_link_call is not None:
                self.target_link_call(False)
            while True:
                try:
                    data, addr=self.udp_socket.recvfrom(1024)
                    # print('received:',data,'from',addr)
                    self.recv_data(data, addr)
                except OSError:
                    # 没有数据包可用了
                    pass
        except KeyboardInterrupt:
            print('system interrupt')
            if self.interrupt_call is not None:
                self.interrupt_call()

    # 接收到命令数据
    def recv_data(self, data, addr):
#         print('recv dat length: %d' % len(data))
        command_data = network_data.unpack(data)
        if command_data:
            self.network_check = 0
            if command_data['Type'] == 'Login':
                self.command_target = addr
                self.send_command_data('Login', machine.unique_id())
                self.target_link_call(True)
                print('set command target %s' % addr[0])
            elif command_data['Type'] == 'Logout':
                self.command_target = None
                self.target_link_call(False)
                print('clear command target by logout')
            elif self.ex_cmd_call:
                # 调用外部处理方法
                self.ex_cmd_call(command_data['Type'], command_data.get('Value', None))
        
    # 发送命令数据
    def send_command_data(self, cmd_type, cmd_value=None):
        if self.is_target_enabled():
            # 发送json类型类型
            pack_obj = {'Type':cmd_type}
            if cmd_value != None:
                pack_obj['Value'] = cmd_value
            send_value = network_data.pack(True, pack_obj)
            try:
                self.udp_socket.sendto(send_value, self.command_target)
                # print('send message length: %d' % len(send_value))
            except OSError:
                print(b'send message OSError:' + send_value)

    # 发送指定的数据
    def send_data(self, data):
        try:
            if self.is_target_enabled():
                self.udp_socket.sendto(data, self.command_target)
                # print('send message length: %d' % len(data))
        except TypeError:
            pass

    # 返回是否可以发送数据
    def is_target_enabled(self):
        return self.command_target != None and self.udp_socket != None
        
    # wifi网络检查方法
    def check_wifi_target(self, t):
        # 是否发送心跳，避免断开连接
        if self.cmd_heart:
            self.send_command_data('Heart')
        # 定时外部调用
        if self.heart_call:
            self.heart_call()

        self.network_check += 1
        # print('self.network_check: %d' % self.network_check)
        if self.command_target != None and self.network_check >= 4:
            self.command_target = None
            self.target_link_call(False)
            print('clear command target because of time out')
        elif self.command_target == None and self.sleep_time > 0 and self.network_check > self.sleep_time:
            # 超时自动进入深度睡眠
            print('enter deepsleep after %d seconds' % self.sleep_time)
            machine.deepsleep()
    
    ###########################Config#############################
    # # 读取配置文件
    # def read_config(self):
    #     self.sys_config = {}
    #     # 读取配置文件
    #     try:
    #         file = open('config.txt', 'r')
    #         content = file.read()
    #         self.sys_config = json.loads(content)
    #         file.close()
    #     except OSError:  # open failed
    #         self.sys_config['wifi_type'] = WIFI_AP
    #         self.save_config()

    # # 保存配置文件
    # def save_config(self):
    #     try:
    #         file = open('config.txt', 'w')
    #         file.write(json.dumps(self.sys_config))
    #         file.close()
    #     except OSError:  # open failed
    #         print("Save config failed!")