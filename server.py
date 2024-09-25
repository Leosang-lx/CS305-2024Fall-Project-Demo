import socket
import cv2
import numpy as np
import pyaudio

# 初始化socket，使用UDP协议
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind(('0.0.0.0', 9999))

# 视频帧大小
FRAME_WIDTH = 640
FRAME_HEIGHT = 480

# 初始化音频
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

audio = pyaudio.PyAudio()
stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, output=True, frames_per_buffer=CHUNK)

print("服务器正在接收数据...")

# 接收并显示视频和音频数据
while True:
    # 接收视频帧数据
    frame_data, addr = server_socket.recvfrom(65535)
    npdata = np.frombuffer(frame_data, dtype=np.uint8)
    frame = np.reshape(npdata, (FRAME_HEIGHT, FRAME_WIDTH, 3))

    # 显示接收的视频帧
    cv2.imshow('Received Video', frame)

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
