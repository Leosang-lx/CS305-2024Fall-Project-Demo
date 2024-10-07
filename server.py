import socket
import cv2
import numpy as np
import pyaudio
import struct

# 初始化socket，使用UDP协议
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind(('127.0.0.1', 9999))

recv_video = False
recv_voice = True

# 视频帧大小
FRAME_WIDTH = 640
FRAME_HEIGHT = 480

# 初始化音频
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

buffer_size = 4096  # 可以根据实际情况调整这个值

if recv_voice:
    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, output=True, frames_per_buffer=CHUNK)

data_header_format = 'I'
data_header_size = struct.calcsize(data_header_format)


def recv_large_data(sock: socket.socket):
    header = struct.unpack(data_header_format, sock.recvfrom(data_header_size))
    data_size = header[0]
    data = bytearray(data_size)
    ptr = memoryview(data)
    while data_size:
        nrecv = sock.recv_into(buffer=ptr, nbytes=min(buffer_size, data_size))
        ptr = ptr[nrecv:]
        data_size -= nrecv
        # recv = recv_socket.recv(min(4096, data_size), MSG_WAITALL)  # deprecated
        # data += recv
        # data_size -= len(recv)
    # data = pickle.loads(data)
    return data


print("Start recving data...")

# 接收并显示视频和音频数据
while True:
    # 接收视频帧数据
    # todo: split the data into multiple udp datagrams, merge them when recving

    if recv_video:
        frame_data, addr = server_socket.recvfrom(65535)
        npdata = np.frombuffer(frame_data, dtype=np.uint8)
        frame = np.reshape(npdata, (FRAME_HEIGHT, FRAME_WIDTH, 3))

        # 显示接收的视频帧
        cv2.imshow('Received Video', frame)

    if recv_voice:
        # 接收音频数据
        audio_data, addr = server_socket.recvfrom(CHUNK * 2)
        stream.write(audio_data)

    # 按下 'q' 键退出
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# 清理
stream.stop_stream()
stream.close()
audio.terminate()
cv2.destroyAllWindows()
server_socket.close()
