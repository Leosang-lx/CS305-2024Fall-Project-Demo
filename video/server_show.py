import socket
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
    camera_socket.bind((SERVER_IP, SERVER_PORT_main))
    camera_socket.listen(1)
    # todo: 尝试声音发送，先实现直接统一按帧发送
    voice_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    voice_socket.bind((SERVER_IP, SERVER_PORT_main))
    voice_socket.listen(1)


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


def display_screen(conn):
    while True:
        # 接收数据长度
        # data_length = int.from_bytes(conn.recv(4), byteorder='big')
        # 接收数据
        # todo: cannot ensure that recv() can receive data_length bytes each time
        data = recv_bytes_tcp(conn)
        frame = decompress_image(data)
        # 显示图像
        if frame.shape[0] > 0 and frame.shape[1] > 0:
            cv2.imshow('Screen Share', frame)
        else:
            raise ValueError("解压缩后的图像尺寸无效")

        # 按'q'键退出
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break


if __name__ == "__main__":
    conn, addr = server_socket_video.accept()
    print(f"Connected by {addr}")
    display_screen(conn)
    conn.close()
    cv2.destroyAllWindows()
