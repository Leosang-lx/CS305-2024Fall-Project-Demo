import socket
import time
import threading

import numpy as np
from util_test import *

# 创建一个TCP socket
server_socket_video = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket_video.bind((SERVER_IP, SERVER_PORT_main))
server_socket_video.listen(1)

if seperate_transmission:
    # todo: 尝试隔离发送
    # 一个连接发送屏幕，一个连接发送摄像头
    camera_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    camera_socket.bind((SERVER_IP, server_port_camera))
    camera_socket.listen(1)
    # todo: 尝试声音发送，先实现直接统一按帧发送
    # voice_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # voice_socket.bind((SERVER_IP, SERVER_PORT_main))
    # voice_socket.listen(1)


def recv_bytes_tcp(sock: socket.socket):
    header = struct.unpack(data_header_format, sock.recv(data_header_size))
    data_size = header[0]
    data = bytearray(data_size)
    ptr = memoryview(data)
    while data_size:
        nrecv = sock.recv_into(buffer=ptr, nbytes=min(4096, data_size))
        ptr = ptr[nrecv:]
        data_size -= nrecv
    return data


def decompress_image(data):
    # 解压JPEG图像数据
    nparr = np.frombuffer(data, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if frame is None:
        raise ValueError("解压缩图像失败")
    return frame


# tuple(latest_tag, latest_recv_img)
recv_screen_tag = None
recv_screen = None
recv_camera_tag = None
recv_camera = None


def keep_recv_screen(recv_socket, running):
    global recv_screen, recv_screen_tag
    while running:
        frame = decompress_image(recv_bytes_tcp(recv_socket))
        if frame.shape[0] > 0 and frame.shape[1] > 0:
            recv_screen_tag, recv_screen = time.perf_counter(), frame
        else:
            raise ValueError("解压缩后的图像尺寸无效")


def keep_recv_camera(recv_socket, running):
    global recv_camera, recv_camera_tag
    while running:
        frame = decompress_image(recv_bytes_tcp(recv_socket))
        if frame.shape[0] > 0 and frame.shape[1] > 0:
            recv_camera_tag, recv_camera = time.perf_counter(), frame
        else:
            raise ValueError("解压缩后的图像尺寸无效")


def display_recv_frames(screen_socket, camera_socket):
    global recv_screen, recv_camera
    last_screen_tag = None
    last_camera_tag = None
    while True:
        if recv_screen is None and recv_camera is None:
            time.sleep(0.01)
        else:
            update_screen = False
            update_camera = False
            if recv_screen is not None:
                # screen_tag, screen_frame = recv_screen
                if last_screen_tag is None or recv_screen_tag != last_screen_tag:
                    last_screen_tag = recv_screen_tag
                    update_screen = True
            if recv_camera is not None:
                # camera_tag, camera_frame = recv_camera
                if last_camera_tag is None or recv_camera_tag != last_camera_tag:
                    last_camera_tag = recv_camera_tag
                    update_camera = True
            if update_screen or update_camera:
                display_frame = overlay_camera_on_screen(recv_screen, recv_camera)
                cv2.imshow('Recv Frames', display_frame)

        # 按'q'键退出
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    screen_socket.close()
    camera_socket.close()


if __name__ == "__main__":
    screen_conn, addr = server_socket_video.accept()
    print(f"Connected by {addr}")
    camera_conn, addr = camera_socket.accept()
    print(f"Connected by {addr}")

    running = True
    recv_screen_thread = threading.Thread(target=keep_recv_screen, args=(screen_conn, lambda: running))
    recv_camera_thread = threading.Thread(target=keep_recv_camera, args=(camera_conn, lambda: running))
    recv_screen_thread.start()
    recv_camera_thread.start()

    display_recv_frames(screen_conn, camera_conn)

    time.sleep(10)
    running = False

    screen_conn.close()
    camera_conn.close()
    server_socket_video.close()
    camera_socket.close()
    cv2.destroyAllWindows()
