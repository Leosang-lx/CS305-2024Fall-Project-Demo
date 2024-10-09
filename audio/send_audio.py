import pyogg

RATE = 0.8
# 创建 Opus 编码器
encoder = pyogg.OpusEncoder(rate=RATE, channels=1)


def encode_audio(data):
    return encoder.encode(data, len(data))


import socket


def send_audio_data(data, audio_type):
    encoded_data = encode_audio(data)

    # 创建一个 UDP 套接字
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # 设置服务器地址和端口
    server_address = ('127.0.0.1', 10000)

    # 发送音频数据
    sock.sendto(encoded_data, server_address)
