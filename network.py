# wifi连接类
import os
import time
import json
import _thread
import network
from socket import *
import machine

#-WIFI DEINE---------------
WIFI_AP    = const(0) # 热点
WIFI_STA   = const(1) # 连接到路由

class car_network():
    # 初始化方法
    def __init__(self):
        self.sys_config = {}
        # 读取配置文件
        try:
            file = open('config.txt', 'r')
            content = file.read()
            self.sys_config = json.loads(content)
            file.close()
        except OSError:  # open failed
            self.sys_config['wifi_type'] = WIFI_AP
            self.save_config()
        # 初始化网络
        self.ip = '0'
        self.udp_socket = None
        self.connect_addr = None
        self.init_wifi()
        
    # 初始化网络
    def init_wifi(self):
        if self.sys_config['wifi_type'] == WIFI_STA:
            sta_if = network.WLAN(network.STA_IF)
            # 网络可能已经连接
            if not sta_if.isconnected():
                sta_if.active(True)
                try:
                    sta_if.connect('HUAWEI-HF', 'HF123456')
                    while not sta_if.isconnected():
                        time.sleep_ms(100)
                    self.ip = sta_if.ifconfig()[0]
                except:
                    print("Network connect failed")
        else:
            ap_if = network.WLAN(network.AP_IF)
            try:
                ap_if.config(essid='CAR_HYX', password='HF123456', authmode=3, max_clients=3)
                ap_if.active(True)
                self.ip = ap_if.ifconfig()[0]
            except:
                print("Network ap failed, reset system")
                machine.reset()
        # 添加网络线程
        if len(self.ip) > 1:
            _thread.start_new_thread(self.recv_data, (self))
            
    # 开始接受网络连接
    def recv_data(self):
        try:
            self.udp_socket = socket(AF_INET, SOCK_DGRAM)
            self.udp_socket.bind((self.ip, 7890))
            while True: #接收数据receiving data
                data, addr=self.udp_socket.recvfrom(1024)
                print('received:',data,'from',addr)
                try:
                    command_data = json.dumps(data)
                    if command_data['type']:
                        # 先验证登录，才确定连接对象
                        if command_data['type'] == 'login':
                            self.connect_addr = addr
                            self.send_data('connect over')
                        else:
                            pass
                except:
                    print('invalid command')
        except:
            if self.udp_socket:
                self.udp_socket.close()
            
    # 发送指定的数据
    def send_data(self, data):
        if self.connect_addr and self.udp_socket:
            self.udp_socket.sendto(data)
            
    # 保存配置文件
    def save_config(self):
        try:
            file = open('config.txt', 'w')
            file.write(json.dumps(self.sys_config))
            file.close()
        except OSError:  # open failed
            print("Save config failed!")

car = car_network()