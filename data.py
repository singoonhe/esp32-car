# 网络数据定义类
# 类型(1字节, 0表示camera或1表示command)|数据(数据块或json字符串)
import json

# 数据块长度定义
CAMERA_FRAME_LEN = 1023

class network_data:
    # 数据Camera组装
    @staticmethod
    def pack(is_command, data):
        if is_command:
            return ('1' + json.dumps(data)).encode('utf-8')
        else:
            ret_list = []
            for i in range(0, len(data), CAMERA_FRAME_LEN):
                chunk = b'0' + data[i:i+CAMERA_FRAME_LEN]
                ret_list.append(chunk)
            return ret_list
        
    # 数据解析，仅有command数据
    @staticmethod
    def unpack(data):
        try:
            command_data = json.loads(data)
            return command_data
        except:
            print('unpack error type data')
