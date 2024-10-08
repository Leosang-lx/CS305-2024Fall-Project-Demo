import pyautogui
import numpy as np
import socket
from util_test import *
import time

# 创建一个TCP socket
client_socket_video = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket_video.connect((SERVER_IP, SERVER_PORT_main))


audio = pyaudio.PyAudio()
streamin = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
# streamout = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, output=True, frames_per_buffer=CHUNK)

# 隔离发送
# 一个连接发送屏幕，一个连接发送摄像头
camera_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
camera_socket.connect((SERVER_IP, server_port_camera))
# 声音发送，先实现直接统一按帧发送
voice_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # use UDP to transmit voice
# voice_socket.connect((SERVER_IP, server_port_voice))


def capture_screen():
    # 按照当前显示器的分辨率捕获整个屏幕
    img = pyautogui.screenshot()
    return img


def capture_voice():
    return streamin.read(CHUNK)


camera_width, camera_height = 640, 480

# 初始化摄像头
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, camera_width)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, camera_height)


def capture_camera():
    # 捕获视频帧
    ret, frame = cap.read()
    if not ret:
        raise Exception('Fail to capture frame from camera')
    return frame


def compress_image(img):
    # 转换为numpy数组
    img_np = np.array(img)
    # 转换为BGR（OpenCV默认格式）
    frame = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)

    # 使用OpenCV进行JPEG压缩
    result, encoded_image = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
    if not result:
        raise ValueError("图像压缩失败")
    return encoded_image.tobytes()


def send_bytes_tcp(sock: socket.socket, bytes_data):
    header = struct.pack(data_header_format, len(bytes_data))
    res = sock.sendall(header + bytes_data)
    return res


def send_frames(share_screen, share_camera, share_audio, fps=10):
    frame_interval = 1 / fps  # 计算每帧之间的间隔时间
    last_frame_time = time.time()
    while True:
        current_time = time.time()
        elapsed_time = current_time - last_frame_time

        if elapsed_time >= frame_interval:
            # 捕获屏幕
            if share_screen:
                screen_frame = np.array(capture_screen())
            else:
                screen_frame = None
            if share_camera:
                camera_frame = capture_camera()
            else:
                camera_frame = None
            # 屏幕图像与摄像头图像混合之后再发送
            if seperate_transmission:
                if share_screen:
                    compressed_screen = compress_image(screen_frame)
                    send_bytes_tcp(client_socket_video, compressed_screen)
                if share_camera:
                    compressed_camera = compress_image(camera_frame)
                    send_bytes_tcp(camera_socket, compressed_camera)
                if share_audio:
                    # todo: 单独发送音频，频率至少要高于rate/chunk
                    audio_data = capture_voice()
                    voice_socket.sendto(audio_data, (SERVER_IP, server_port_voice))
            else:
                frame_to_send = overlay_camera_on_screen(screen_frame, camera_frame)
                # 压缩图像
                compressed_img = compress_image(frame_to_send)
                print(len(compressed_img), 'bytes')
                send_bytes_tcp(client_socket_video, compressed_img)

            # 更新上一帧的时间
            last_frame_time = current_time


def send_voice(send_socket: socket.socket, fps=60):
    frame_interval = 1 / fps  # 计算每帧之间的间隔时间
    last_frame_time = time.time()
    while True:
        current_time = time.time()
        elapsed_time = current_time - last_frame_time
        if elapsed_time >= frame_interval:
            audio_data = capture_voice()
            send_socket.sendto(audio_data, (SERVER_IP, server_port_voice))

            # 更新上一帧的时间
            last_frame_time = current_time


if __name__ == "__main__":
    send_frames(share_screen, share_camera, share_audio, fps=30)  # 限制帧率为10 FPS
