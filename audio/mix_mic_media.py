import numpy as np
from send_audio import *


def mix_audio(media_data, mic_data):
    media_array = np.frombuffer(media_data, dtype=np.int16)
    mic_array = np.frombuffer(mic_data, dtype=np.int16)

    # 混合音频数据：直接求平均？
    mixed_array = (media_array + mic_array) / 2
    mixed_data = mixed_array.astype(np.int16).tobytes()

    return mixed_data


def send_mixed_audio_data(media_data, mic_data):
    mixed_data = mix_audio(media_data, mic_data)
    encoded_data = encode_audio(mixed_data)

    # 创建一个 UDP 套接字
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # 设置服务器地址和端口
    server_address = ('127.0.0.1', 10000)

    # 发送音频数据
    sock.sendto(encoded_data, server_address)
