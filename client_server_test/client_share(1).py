import threading

import pyautogui
import numpy as np
import socket
import time
from util_test import *
from udp_comm import *


if seperate_transmission:
    # 隔离发送
    # 创建一个TCP socket
    if share_screen:
        client_socket_video = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket_video.connect((SERVER_IP, SERVER_PORT_main))
    # 一个连接发送屏幕，一个连接发送摄像头
    if share_camera:
        camera_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        camera_socket.connect((SERVER_IP, server_port_camera))
    # 声音发送，先实现直接统一按帧发送
    voice_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # use UDP to transmit voice
    # voice_socket.connect((SERVER_IP, server_port_voice))
else:
    send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

audio = pyaudio.PyAudio()
streamin = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
# streamout = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, output=True, frames_per_buffer=CHUNK)


def capture_screen():
    # 按照当前显示器的分辨率捕获整个屏幕
    img = pyautogui.screenshot()
    return img


def capture_voice():
    return streamin.read(CHUNK)


# 初始化摄像头
if share_camera:
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
                if share_screen:
                    compressed_screen = compress_image(screen_frame)
                    send_large_data((SERVER_IP, SERVER_PORT_main), compressed_screen)
                frame_to_send = overlay_camera_on_screen(screen_frame, camera_frame)
                # 压缩图像
                compressed_img = compress_image(frame_to_send)
                print(len(compressed_img), 'bytes')
                send_bytes_tcp(client_socket_video, compressed_img)

            # 更新上一帧的时间
            last_frame_time = current_time


def send_voice(send_socket: socket.socket, frequency=60):
    frame_interval = 1 / frequency  # 计算每帧之间的间隔时间
    last_frame_time = time.time()
    while True:
        current_time = time.time()
        elapsed_time = current_time - last_frame_time
        if elapsed_time >= frame_interval:
            audio_data = capture_voice()
            send_socket.sendto(audio_data, (SERVER_IP, server_port_voice))

            # 更新上一帧的时间
            last_frame_time = current_time


def keep_recv_screen(recv_socket, running):
    global recv_screen, recv_screen_tag
    while running:
        frame = decompress_image(recv_bytes_tcp(recv_socket))
        if frame.shape[0] > 0 and frame.shape[1] > 0:
            recv_screen_tag, recv_screen = time.perf_counter(), frame
        else:
            raise ValueError("解压缩后的图像尺寸无效")

recv_screen_tag = None
recv_screen = None
recv_camera_tag = None
recv_camera = None
def display_recv_frames(screen_socket, running):
    global recv_screen
    # global recv_camera
    last_screen_tag = None
    # last_camera_tag = None
    while running:
        # if recv_screen is None and recv_camera is None:
        if recv_screen is None:
            time.sleep(0.01)
        else:
            update_screen = False
            update_camera = False
            if recv_screen is not None:
                # screen_tag, screen_frame = recv_screen
                if last_screen_tag is None or recv_screen_tag != last_screen_tag:
                    last_screen_tag = recv_screen_tag
                    update_screen = True
            # if recv_camera is not None:
            #     # camera_tag, camera_frames = recv_camera
            #     if last_camera_tag is None or recv_camera_tag != last_camera_tag:
            #         last_camera_tag = recv_camera_tag
            #         update_camera = True
            if update_screen or update_camera:
                display_frame = overlay_camera_on_screen(recv_screen, recv_camera)
                cv2.imshow('Recv Frames', display_frame)

        # 按'q'键退出
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    screen_socket.close()
    camera_socket.close()


if __name__ == "__main__":
    # send_frames(share_screen, share_camera, share_audio, fps=30)
    running = True
    send_thread = threading.Thread(target=send_frames, args=(share_screen, share_camera, share_audio, 30))
    recv_thread = threading.Thread(target=keep_recv_screen, args=(client_socket_video, lambda: running))
    send_thread.start()
    recv_thread.start()

    display_recv_frames(client_socket_video, lambda: running)
