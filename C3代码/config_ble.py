# BLE通信模块
import bluetooth
import time
import struct
from micropython import const

# BLE设备定义
BLE_DEVICE_CAR = const(0x1011)#玩具车
BLE_DEVICE_CAR_CONTROLLER = const(0x1012)#玩具车遥控器
BLE_DEVICE_INTERPHONE = const(0x1015)#对讲机

# BLE事件定义
_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)
_IRQ_GATTS_WRITE = const(3)
_IRQ_GATTS_READ_REQUEST = const(4)
# 定义支持的服务，0000xxxx-0000-1000-8000-00805f9b34fb为通用字符串
_UART_UUID = bluetooth.UUID("0000ffe0-0000-1000-8000-00805f9b34fb")
_UART_TX = (
    bluetooth.UUID("0000ffe7-0000-1000-8000-00805f9b34fb"),
    bluetooth.FLAG_NOTIFY,
)
_UART_RX = (
    bluetooth.UUID("0000ffe6-0000-1000-8000-00805f9b34fb"),
    bluetooth.FLAG_WRITE,
)
_UART_SERVICE = (
    _UART_UUID,
    (_UART_TX, _UART_RX),
)

# name:仅可以为英文，长度不超过16+4个字符
# device_type:设备类型，见上面的定义
class CONFIG_BLE:
    def __init__(self, name, device_type, connect_call, write_call):
        self._connection = None
        self._connect_callback = connect_call
        self._write_callback = write_call
        # 初始化BLE
        self._ble = bluetooth.BLE()
        self._ble.active(False)
        self._ble.active(True)
        self._ble.irq(self._irq)
        ((self._handle_tx, self._handle_rx),) = self._ble.gatts_register_services((_UART_SERVICE,))
        # 开始广播
        self._advertise_data = self.advertising_content(name, _UART_UUID, device_type)
        self._advertise()
    
    # 获取蓝牙广播内容
    def advertising_content(self, name, service_uuid, appearance):
        payload = bytearray()
        # 添加固定数据头:struct.pack("BB", len(0x02+0x04) + 1, 0x01) + (0x02+0x04), "BB"是指后面参数的类型为二进制
        # 详情参考:https://github.com/micropython/micropython/blob/master/examples/bluetooth/ble_advertising.py
        payload += b'\x02\x01\x06'
        # 添加蓝牙名称，0x09表示_ADV_TYPE_NAME
        payload += struct.pack("BB", len(name) + 1, 0x09) + name
        
        # 注：flutter仅支持128位完整ID识别，使用128太容易导致广播数据超长
        # 添加服务ID, 0x7表示_ADV_TYPE_UUID128_COMPLETE
        #service_bytes = bytes(service_uuid)
        #payload += struct.pack("BB", len(service_bytes) + 1, 0x7) + service_bytes
        
        # 添加类型标识, 0x19表示_ADV_TYPE_APPEARANCE
        appearance_sign = struct.pack("<h", appearance)
        payload += struct.pack("BB", len(appearance_sign) + 1, 0x19) + appearance_sign
        # 判断是否超长
        if len(payload) > 31:
            raise ValueError("advertising payload too large, please cut down device name")
        return payload
    
    # BLE回调事件
    def _irq(self, event, data):
        print("event:RX", event)
        if event == _IRQ_CENTRAL_CONNECT:
            # 开始连接
            self._connection, _, _ = data
            print("BLE New connection", self._connection)
            # 连接回调事件
            if self._connect_callback:
                self._connect_callback()
        elif event == _IRQ_CENTRAL_DISCONNECT:
            # 结束连接
            print("BLE Disconnected", self._connection)
            self._connection = None
            # 继续广播
            self._advertise()
        elif event == _IRQ_GATTS_WRITE:
            # 接收到消息
            conn_handle, value_handle = data
            value = self._ble.gatts_read(value_handle)
            if value_handle == self._handle_rx and self._write_callback:
                self._write_callback(value)
        elif event == _IRQ_GATTS_READ_REQUEST:
            # 接收到读取请求
            print("_IRQ_GATTS_READ_REQUEST")
            ble.send("give you value")
    
    # 发送消息事件
    def send(self, data):
        if self._connection != None:
            self._ble.gatts_write(self._handle_tx, data.encode())

    # 返回当前是否已连接BLE
    def is_connected(self):
        return self._connection != None
    
    # 开始蓝牙广播事件, 每秒广播一次
    def _advertise(self, interval_us=1000000):
        print("BLE Starting advertising")
        self._ble.gap_advertise(interval_us, adv_data=self._advertise_data)

# 测试用例
if __name__ == "__main__":
    def on_msg_callback(v):
        print("RX", v)
        ble.send(b'config right')
    def on_device_connect():
        pass
    ble = CONFIG_BLE('sin-car-4012', BLE_DEVICE_CAR, on_device_connect, on_msg_callback)
    while True:
        time.sleep_ms(100)
