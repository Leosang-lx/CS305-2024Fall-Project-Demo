import socket
import time
import threading

import numpy as np
from util_test import *

import asyncio


class VideoStreamServer:
    def __init__(self):
        self.clients = set()

    async def handle_client(self, reader, writer):
        # 将新连接添加到客户端集合中
        self.clients.add(writer)
        client_address = writer.get_extra_info('peername')
        print(f"New connection from {client_address}")

        try:
            while True:
                # 读取客户端发送的数据
                data = await reader.read(1024)  # 你可以根据实际情况调整缓冲区大小
                if not data:
                    break

                # 转发数据给其他所有客户端
                for client in self.clients:
                    # if client != writer:  # 是否转发给自己
                    client.write(data)
                    await client.drain()
        except asyncio.CancelledError:
            pass
        finally:
            # 关闭连接并从客户端集合中移除
            print(f"Connection closed with {client_address}")
            self.clients.remove(writer)
            writer.close()
            await writer.wait_closed()

    async def start_server(self, host, port):
        server = await asyncio.start_server(
            self.handle_client, host, port
        )
        addr = server.sockets[0].getsockname()
        print(f'Serving on {addr}')

        async with server:
            await server.serve_forever()


# 创建服务器实例并启动
server = VideoStreamServer()
asyncio.run(server.start_server(SERVER_IP, SERVER_PORT_main))

audio = pyaudio.PyAudio()
streamin = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
streamout = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, output=True, frames_per_buffer=CHUNK)

if seperate_transmission:
    # 创建一个TCP socket
    server_socket_video = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket_video.bind((SERVER_IP, SERVER_PORT_main))
    server_socket_video.listen(1)
    # 不同数据源隔离发送
    # 一个连接发送屏幕，一个连接发送摄像头
    camera_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    camera_socket.bind((SERVER_IP, server_port_camera))
    camera_socket.listen(1)
    # 声音发送，先实现直接统一按帧发送
    audio_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # use UDP to transmit audio
    audio_socket.bind((SERVER_IP, server_port_voice))
    # voice_socket.listen(1)

else:
    recv_screen_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    recv_camera_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    recv_audio_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    recv_screen_socket.bind((SERVER_IP, SERVER_PORT_main))
    recv_camera_socket.bind((SERVER_IP, server_port_camera))
    recv_audio_socket.bind((SERVER_IP, server_port_voice))

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


def keep_recv_audio(recv_socket, running):
    while running:
        audio_chunk, addr = recv_socket.recvfrom(65535)
        assert len(audio_chunk) == CHUNK * 2
        streamout.write(audio_chunk)


def display_recv_frames(screen_socket, camera_socket, running):
    global recv_screen, recv_camera
    last_screen_tag = None
    last_camera_tag = None
    while running:
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
                # camera_tag, camera_frames = recv_camera
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
    # accept connections from clients
    screen_conn, addr = server_socket_video.accept()
    print(f"Screen service: Connected by {addr}")
    camera_conn, addr = camera_socket.accept()
    print(f"Camera service: Connected by {addr}")

    running = True
    if seperate_transmission:
        recv_screen_thread = threading.Thread(target=keep_recv_screen, args=(screen_conn, lambda: running))
        recv_camera_thread = threading.Thread(target=keep_recv_camera, args=(camera_conn, lambda: running))
        recv_audio_thread = threading.Thread(target=keep_recv_audio, args=(audio_socket, lambda: running))
        recv_screen_thread.start()
        recv_camera_thread.start()
        recv_audio_thread.start()

        display_recv_frames(screen_conn, camera_conn, lambda: running)

        time.sleep(10)
        running = False

        recv_screen_thread.join()
        recv_camera_thread.join()
        recv_audio_thread.join()

        screen_conn.close()
        camera_conn.close()
        server_socket_video.close()
        camera_socket.close()
        audio_socket.close()

    else:
        recv_thread = threading.Thread()

    cv2.destroyAllWindows()
