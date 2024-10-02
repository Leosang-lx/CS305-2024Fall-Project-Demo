import struct

import pyautogui
import numpy as np
import cv2
import socket
from PIL import Image
from io import BytesIO
import time

# 设置服务器地址和端口
SERVER_IP = "127.0.0.1"
SERVER_PORT = 5005

# 创建一个TCP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((SERVER_IP, SERVER_PORT))

data_header_format = 'I'
data_header_size = struct.calcsize(data_header_format)


def capture_screen():
    # 捕获整个屏幕
    img = pyautogui.screenshot()
    return img


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


def send_screen(fps=10):
    frame_interval = 1 / fps  # 计算每帧之间的间隔时间
    last_frame_time = time.time()
    while True:
        current_time = time.time()
        elapsed_time = current_time - last_frame_time

        if elapsed_time >= frame_interval:
            # 捕获屏幕
            img = capture_screen()
            # 压缩图像
            compressed_img = compress_image(img)
            print(len(compressed_img), 'bytes')
            send_bytes_tcp(sock, compressed_img)
            # 发送数据长度
            # sock.sendall(len(compressed_img).to_bytes(4, byteorder='big'))
            # 发送数据
            # sock.sendall(compressed_img)

            # 更新上一帧的时间
            last_frame_time = current_time


if __name__ == "__main__":
    send_screen(fps=30)  # 限制帧率为10 FPS