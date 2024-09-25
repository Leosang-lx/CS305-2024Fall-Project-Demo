import socket
import cv2
import numpy as np
import pyaudio

def send_large_data(sock, data, address):
   buffer_size = 4096  # 可以根据实际情况调整这个值
   for i in range(0, len(data), buffer_size):
       sock.sendto(data[i:i+buffer_size], address)

# 初始化socket，使用UDP协议
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address = ('127.0.0.1', 9999)

# 初始化摄像头
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# 初始化音频
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

audio = pyaudio.PyAudio()
stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)

print("客户端正在发送数据...")

while True:
    # 捕获视频帧
    ret, frame = cap.read()
    if not ret:
        break

    # 将帧数据转换为字节并发送
    frame_data = frame.flatten().tobytes()
    # client_socket.sendto(frame_data, server_address)
    send_large_data(client_socket, frame_data, server_address)

    # 捕获音频数据并发送
    audio_data = stream.read(CHUNK)
    # client_socket.sendto(audio_data, server_address)
    send_large_data(client_socket, audio_data, server_address)

    # 显示正在发送的视频帧（仅用于客户端调试）
    cv2.imshow('Sending Video', frame)

    # 按下 'q' 键退出
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# 清理
cap.release()
stream.stop_stream()
stream.close()
audio.terminate()
cv2.destroyAllWindows()
client_socket.close()
