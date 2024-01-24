# 网络数据定义类
# 类型(1字节, 0表示camera或1表示command)|数据(数据块或json字符串)
import json

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
            for i in range(0, len(data), CAMERA_FRAME_LEN):
                chunk = b'0' + struct.pack('>BHH', 0, frame_index, total_len, i) + data[i:i+CAMERA_FRAME_LEN]
                ret_list.append(chunk)
            # FrameIndex自增
            frame_index += 1
            if frame_index > 200:
                frame_index = 0
            return ret_list
        
    # 数据解析，仅有command数据
    @staticmethod
    def unpack(data):
        try:
            command_data = json.loads(data)
            return command_data
        except:
            print('unpack error type data')
