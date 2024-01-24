# 网络数据定义类
# 类型(1字节, 0表示camera或1表示command)|数据(数据块或json字符串)
import json
import math
import struct

# 数据块长度定义(0(帧ID)(总帧2字节)(当前帧2字节))
CAMERA_FRAME_LEN = 1024 - 1 - 1 - 2 - 2

class network_data:
    # 静态变量
    frame_index = 0
    # 数据Camera组装
    @staticmethod
    def pack(is_command, data):
        if is_command:
            return ('1' + json.dumps(data)).encode('utf-8')
        else:
            ret_list = []
            total_len = math.ceil(len(data) / CAMERA_FRAME_LEN)
            step_count = 0
            for i in range(0, len(data), CAMERA_FRAME_LEN):
                chunk = b'0' + struct.pack('>BHH', network_data.frame_index, total_len, step_count) + data[i:i+CAMERA_FRAME_LEN]
                ret_list.append(chunk)
                step_count += 1
            # FrameIndex自增
            network_data.frame_index += 1
            if network_data.frame_index > 200:
                network_data.frame_index = 0
            return ret_list
        
    # 数据解析，仅有command数据
    @staticmethod
    def unpack(data):
        try:
            command_data = json.loads(data)
            return command_data
        except:
            print('unpack error type data')
