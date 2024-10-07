import socket
import cv2
import numpy as np
import pyaudio
import struct

data_header_format = 'I'
data_header_size = struct.calcsize(data_header_format)

buffer_size = 4096  # 可以根据实际情况调整这个值

send_video = False
send_voice = True


def send_large_data(sock, data, address):
    header = struct.pack(data_header_format, len(data))
    sock.sendto(header, address)
    for i in range(0, len(data), buffer_size):
        sock.sendto(data[i:i + buffer_size], address)


# 初始化socket，使用UDP协议
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address = ('127.0.0.1', 9999)


if send_video:
    # 初始化摄像头
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# 初始化音频
CHUNK = 1024
FORMAT = pyaudio.paInt16  # 采样位宽16bit
CHANNELS = 1  # 声道数
RATE = 44100  # 采样率
if send_voice:
    audio = pyaudio.PyAudio()
    streamin = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
    streamout = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, output=True, frames_per_buffer=CHUNK)

print("Start sending data...")

while True:
    # 捕获视频帧
    if send_video:
        ret, frame = cap.read()
        if not ret:
            break

        # 将帧数据转换为字节并发送
        frame_data = frame.flatten().tobytes()
        # client_socket.sendto(frame_data, server_address)
        send_large_data(client_socket, frame_data, server_address)
        # 显示正在发送的视频帧（仅用于客户端调试）
        cv2.imshow('Sending Video', frame)

    if send_voice:
        # 捕获音频数据并发送
        audio_data = streamin.read(CHUNK)
        # streamout.write(audio_data)
        # client_socket.sendto(audio_data, server_address)
        # send_large_data(client_socket, audio_data, server_address)
        client_socket.sendto(audio_data, server_address)

    # 按下 'q' 键退出
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# 清理
cap.release()
streamin.stop_stream()
streamin.close()
streamout.stop_stream()
streamout.close()
audio.terminate()
cv2.destroyAllWindows()
client_socket.close()
