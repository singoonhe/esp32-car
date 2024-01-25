# wifi连接类
import os
import time
import _thread
import network
from socket import *

class wifi_network:
    # 初始化方法
    # sta_info:连接网络的信息列表
    def __init__(self, sta_info):
#         self.sys_config = {}
#         # 读取配置文件
#         try:
#             file = open('config.txt', 'r')
#             content = file.read()
#             self.sys_config = json.loads(content)
#             file.close()
#         except OSError:  # open failed
#             self.sys_config['wifi_type'] = WIFI_AP
#             self.save_config()
        # 初始化网络
        self.ip = '0'
        self.udp_socket = None
        # 使用指定引脚的电平来判断网络模式
        p2 = Pin(sta_info['ap_pin'], Pin.IN, Pin.PULL_UP)
        if p2.value() == 0:
            self.init_wifi(sta_info, True)
        else:
            self.init_wifi(sta_info, False)
        
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
                print("Network ap failed, please reset system")
            
    # 开始接受网络连接
    # recv_call：接收事件的回调
    def start_socket(self, recv_call):
        if len(self.ip) < 8:
            print('network init failed')
            return
        
        print("current ip : " + self.ip)
        # 开启非阻塞UDP
        self.udp_socket = socket(AF_INET, SOCK_DGRAM)
        self.udp_socket.bind((self.ip, 7890))
        self.udp_socket.setblocking(False)
        while True: #接收数据receiving data
            try:
                data, addr=self.udp_socket.recvfrom(1024)
                print('received:',data,'from',addr)
                recv_call(data, addr)
            except OSError:
                # 没有数据包可用了
                pass
            
    # 发送指定的数据
    def send_data(self, data, addr):
        if self.udp_socket != None:
            print('send message length: %d' % len(data))
            self.udp_socket.sendto(data, addr)
            
    # 保存配置文件
#     def save_config(self):
#         try:
#             file = open('config.txt', 'w')
#             file.write(json.dumps(self.sys_config))
#             file.close()
#         except OSError:  # open failed
#             print("Save config failed!")