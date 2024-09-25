import socket
import pyogg
from media_capture import *

RATE = 0.8
# 创建 Opus 解码器
decoder = pyogg.OpusDecoder(rate=RATE, channels=1)

# 创建 Socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# 绑定端口
server_address = ('127.0.0.1', 10000)
sock.bind(server_address)

# 初始化 PyAudio
p = pyaudio.PyAudio()

stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                output=True)

while True:
    data, _ = sock.recvfrom(CHUNK)
    decoded_data = decoder.decode(data)
    stream.write(decoded_data)